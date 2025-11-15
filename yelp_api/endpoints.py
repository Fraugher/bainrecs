import os
import requests
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from functools import wraps

load_dotenv()
yelp_endpoints = Blueprint('yelp_endpoints', __name__)

# from .utils import require_api_key, after_request, handle_yelp_error

YELP_API_KEY = os.getenv('YELP_API_KEY')
PYTHONANYWHERE_API_KEY = os.getenv('PYTHONANYWHERE_API_KEY')

def is_valid_pythonanywhere_api_key(api_key):
    return api_key == PYTHONANYWHERE_API_KEY

def require_yelp_api_key(f):
    """Decorator to check if Yelp API key is configured"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # YELP_API_KEY = os.environ.get('YELP_API_KEY')
        if not YELP_API_KEY:
            return jsonify({
                'error': 'Configuration Error',
                'message': 'YELP_API_KEY not configured in environment variables.'
            }), 500
        return f(*args, **kwargs)

    return decorated_function

@yelp_endpoints.route('/health')
def health():
    """Health check endpoint"""
    api_key_configured = YELP_API_KEY is not None
    return jsonify({
        'status': 'healthy' if api_key_configured else 'degraded',
        'api_key_configured': api_key_configured
    }), 200 if api_key_configured else 503

@yelp_endpoints.route('/hello')
def hello_world():
    return 'Hello from Flask endpoints!'

@yelp_endpoints.route('/reviews', methods=['GET'])
@require_yelp_api_key
def get_restaurants_reviews         ():
    biz_id=request.args.get('biz_id')
    return get_reviews(biz_id)

def get_reviews(biz_id):
    url: str = f"https://api.yelp.com/v3/businesses/{biz_id}/reviews"
    return get_yelp_api(url)

@yelp_endpoints.route('/search', methods=['GET'])
@require_yelp_api_key
def search_restaurants():
    """
    Search for restaurants using Yelp API
    Query parameters:
    - location (required): Location to search in
    - term: Search term (default: 'restaurants')
    - radius: Search radius in meters (default: 10000)
    - categories: Comma-separated list of category filters
    - price: Comma-separated pricing levels (1=cheap, 2, 3, 4=expensive)
    - attributes: Business attributes like 'ambiance'
    - sort_by: Sort results by (default: 'rating')
    """

    # Get query parameters
    location = request.args.get('location')

    # Validate required parameters
    if not location:
        return jsonify({
            'error': 'Missing Required Parameter',
            'message': 'The "location" parameter is required.'
        }), 400

    # Build Yelp API query parameters
    yelp_params = {
        'location': location,
        'locale': 'en_CA',
        'term': 'restaurants',
        'limit': 3, # this is temporary during development to keep things fast
        'radius': int(request.args.get('radius', 10000)),
        'sort_by': request.args.get('sort_by', 'rating')
    }

    # Add optional parameters if provided
    if request.args.get('categories'):
        yelp_params['categories'] = request.args.get('categories')

    if request.args.get('price'):
        yelp_params['price'] = request.args.get('price')

    if request.args.get('attributes'):
        yelp_params['attributes'] = request.args.get('attributes')

    url = "https://api.yelp.com/v3/businesses/search"
    response, search_status_code  = get_yelp_api(url, params=yelp_params)
    # current_app.logger.info("HEY AM I LOGGING?")
    # return response

    if search_status_code != 200  :
        return response, search_status_code
        # error_response = handle_yelp_error(search_status_code, response)
        # return jsonify(error_response), search_status_code
    else: #handle successful response
        response_biz = []
        response_date = response
        if "businesses" in response_date:
            for business in response_date["businesses"]:
                # Extract only desired fields
                response_reviews = []
                response_highlights = []
                biz_id = business.get("id")
                biz_reviews, reviews_status_code = get_reviews(biz_id)
                if reviews_status_code == 200:
                    if "reviews" in biz_reviews:
                        for review in biz_reviews["reviews"]:
                            simplified_review= {
                                "rating": review.get("rating"),
                                "text": review.get("text"),
                                "review_date": review.get("time_created")
                               }
                            response_reviews.append(simplified_review)
                else:
                    response_reviews.append(biz_reviews)

                biz_highlights, highlights_status_code = get_highlights(biz_id)
                if highlights_status_code == 200:
                    if "review_highlights" in biz_highlights:
                        for highlight in biz_highlights["review_highlights"]:
                            response_highlights.append(highlight)
                else:
                    response_highlights= biz_highlights

                simplified_business = {
                    "name": business.get("name"),
                    "id": biz_id,
                    "rating": business.get("rating"),
                    "display_address": business.get("location", {}).get("display_address"),
                    "reviews": response_reviews,
                    "highlights": response_highlights
                }
                response_biz.append(simplified_business)
        return response_biz, 200

@yelp_endpoints.route('/highlights', methods=['GET'])
@require_yelp_api_key
def get_restaurants_highlights         ():
    biz_id=request.args.get('biz_id')
    return get_highlights(biz_id)

def get_highlights        (biz_id):
    url=f"https://api.yelp.com/v3/businesses/{biz_id}/review_highlights"
    return get_yelp_api(url)

def get_yelp_api (url, params=None):
    if params is None:
        params = {}
    headers = {
        'Authorization': f'Bearer {YELP_API_KEY}'
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        # Parse response
        try:
            response_data = response.json()
        except ValueError:
            response_data = {'raw_response': response.text}

        # Handle successful response
        if response.status_code == 200:
            return response_data, 200

        # Handle error responses
        error_response = handle_yelp_error(response.status_code, response_data)
        return jsonify(error_response), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({
            'error': 'Request Timeout',
            'message': 'The request to Yelp API timed out. Please try again.',
        }), 504

    except requests.exceptions.ConnectionError:
        return jsonify({
            'error': 'Connection Error',
            'message': 'Unable to reach Yelp API. Please check your connection.',
        }), 503

    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': 'Request Error',
            'message': 'An error occurred while making the request to Yelp API.',
            'details': str(e)
        }), 500

    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred.',
            'details': str(e)
        }), 500


# CORS support not needed we are using Flask-Cors
# @yelp_endpoints.after_request
# def after_request(response):
#     """Add CORS headers to all responses"""
#     response.headers.add('Access-Control-Allow-Origin', '*')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
#     return response

def handle_yelp_error(status_code, response_data):
    """Handle specific Yelp API error codes with appropriate messages"""

    error_messages = {
        400: {
            'error': 'Bad Request',
            'message': 'Invalid request parameters. Please check your query parameters.',
            'details': response_data
        },
        401: {
            'error': 'Unauthorized',
            'message': 'The API key has either expired or does not have the required scope to query this endpoint.',
            'details': response_data,
            'possible_causes': [
                'UNAUTHORIZED_API_KEY: The API key provided is not currently able to query this endpoint.',
                'TOKEN_INVALID: Invalid API key or authorization header.'
            ]
        },
        403: {
            'error': 'Forbidden',
            'message': 'The API key provided is not currently able to query this endpoint.',
            'details': response_data
        },
        404: {
            'error': 'Resource Not Found',
            'message': 'The requested resource was not found. Please check the endpoint URL.',
            'details': response_data
        },
        413: {
            'error': 'Request Entity Too Large',
            'message': 'The length of the request exceeded the maximum allowed.',
            'details': response_data
        },
        429: {
            'error': 'Too Many Requests',
            'message': 'You have either exceeded your daily quota, or have exceeded the queries-per-second limit for this endpoint. Try reducing the rate at which you make queries.',
            'details': response_data
        },
        500: {
            'error': 'Internal Server Error',
            'message': 'Yelp API is experiencing internal server errors. Please try again later.',
            'details': response_data
        },
        503: {
            'error': 'Service Unavailable',
            'message': 'Yelp API service is temporarily unavailable. Please try again later.',
            'details': response_data
        }
    }

    return error_messages.get(status_code, {
        'error': f'Yelp API Error ({status_code})',
        'message': 'An unexpected error occurred with the Yelp API.',
        'details': response_data
    })