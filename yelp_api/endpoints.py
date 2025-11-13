# from app import app
import os
import requests
from flask import Flask, request, jsonify
# import yelp_api.utils
from functools import wraps

# from .utils import require_api_key, after_request, handle_yelp_error

YELP_API_KEY = os.environ.get('YELP_API_KEY')


def require_api_key(f):
    """Decorator to check if Yelp API key is configured"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        YELP_API_KEY = os.environ.get('YELP_API_KEY')
        if not YELP_API_KEY:
            return jsonify({
                'error': 'Configuration Error',
                'message': 'YELP_API_KEY not configured in environment variables.'
            }), 500
        return f(*args, **kwargs)

    return decorated_function

def register_endpoints(app: Flask):
    # utils.api_utils(app);

    app.route('/health')
    def health():
        """Health check endpoint"""
        api_key_configured = YELP_API_KEY is not None
        return jsonify({
            'status': 'healthy' if api_key_configured else 'degraded',
            'api_key_configured': api_key_configured
        }), 200 if api_key_configured else 503

    app.route('/hello')
    def hello_world():
        return 'Hello from Flask endpoints!'

    app.route('/search', methods=['GET'])
    @require_api_key
    def search_restaurants(f):
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
            'term': request.args.get('term', 'restaurants'),
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

        # Make request to Yelp API
        headers = {
            'Authorization': f'Bearer {YELP_API_KEY}'
        }

        try:
            response = requests.get(
                'https://api.yelp.com/v3/businesses/search',
                params=yelp_params,
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
                return jsonify(response_data), 200

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



    # CORS support
    app.after_request
    def after_request(response):
        """Add CORS headers to all responses"""
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response

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
                'message': 'The API key has either expired or doesn\'t have the required scope to query this endpoint.',
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