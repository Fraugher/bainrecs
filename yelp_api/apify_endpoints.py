import os
import requests
from apify_client import ApifyClient
from dotenv import load_dotenv
from flask import Blueprint, jsonify, json
from functools import wraps
from datetime import datetime, timezone
from app import db

load_dotenv()
apify_endpoints = Blueprint('apify_endpoints', __name__)

APIFY_API_KEY = os.getenv('APIFY_API_KEY')
YELP_API_KEY = os.getenv('YELP_API_KEY')
PYTHONANYWHERE_API_KEY = os.getenv('PYTHONANYWHERE_API_KEY')
SQL_ALCHEMY_URI = os.getenv('SQL_ALCHEMY_URI')

# db = SQLAlchemy()
# app.config["SQLALCHEMY_DATABASE_URI"] = SQL_ALCHEMY_URI
# app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 280}
# db.init_app(app)

class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    google_maps_id =db.Column(db.String(128))
    date_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    place_name = db.Column(db.String(255), nullable=False)
    place_url = db.Column(db.String(255))
    place_address = db.Column(db.String(255))
    provider = db.Column(db.String(100))
    review_text = db.Column(db.Text)
    review_date = db.Column(db.DateTime)
    review_rating = db.Column(db.SmallInteger)  # TINYINT maps to SmallInteger
    author_name = db.Column(db.String(100))
    ignore_for_quality = db.Column(db.Boolean)
    ignore_for_rating = db.Column(db.Boolean)
    ignore_for_insufficient = db.Column(db.Boolean)
    selected_as_top_rating = db.Column(db.Boolean)

    def __repr__(self):
        return f'<Review {self.id}: {self.place_name} - {self.review_rating}/5>'

@apify_endpoints.route('/apify/popdb')
def apify_popdb():
    item_count=0
    client = ApifyClient(APIFY_API_KEY)
    run_input = {
      "keywords": ["Maison Selby"],
      "location": "2 Bloor Street E,  Toronto, ON M4W 1A8, Canada",
      "checkNames": False,
      "requireExactNameMatch": False,
      "deeperCityScrape": False,
      "maxReviewsPerPlaceAndProvider": 10,
      "reviewsFromDate" : "2021-01-01",
      "scrapeReviewPictures": False,
      "scrapeReviewResponses": False
    }

    apify_uri ="tri_angle/restaurant-review-aggregator"
    run = client.actor(apify_uri).call(run_input=run_input)

    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        google_maps_id  =item.get("googleMapsPlaceId")
        place_name = item.get("placeName","")
        place_url = item.get("placeUrl","")
        place_address = item.get("placeAddress","")
        provider = item.get("provider","")
        review_text = item.get("reviewText","")
        review_date = item.get("reviewDate", None)
        review_rating = item.get("reviewRating", None)
        author_name = item.get("authorName","")
        item_count += 1
        new_review = Review(
            google_maps_id=google_maps_id,
            place_name=place_name,
            place_url=place_url,
            place_address=place_address,
            provider = provider,
            review_text=review_text,
            review_date=review_date if isinstance(review_date, datetime) else None,
            review_rating=review_rating,
            author_name=author_name,
            ignore_for_quality=False,
            ignore_for_rating=False,
            ignore_for_insufficient=False,
            selected_as_top_rating=False
        )

        # Add to session
        db.session.add(new_review)

    try:
        db.session.commit()
        msg=f"Successfully added {item_count} reviews to database"
    except Exception as e:
        db.session.rollback()
        msg=f"Error adding reviews: {e}"

    return msg

@apify_endpoints.route('/apify/testpop')
def apify_testpop():
    item_count=0
    items = [
  {
    "placeName": "Maison Selby",
    "placeAddress": "592 Sherbourne St, Toronto, ON M4X 1L4, Canada",
    "provider": "google-maps",
    "reviewText": "Booked online and requested \"standard\" reservation (not bar). In spite of this, the restaurant had me at the bar.  While they were able to find a table I had to be done with dinner by 7:30 (6 pm booking). The kitchen send all the food to the table at once and there was no room at all at the table for it.  I must say that the servers, especially Victoria, were lovely and the food was good but because of the issue that led to the 1 star review, I won't be back.",
    "reviewDate": "2025-11-09T00:48:43.566Z",
    "reviewRating": 1,
    "authorName": "Alita Wolff"
  },
  {
    "placeName": "Maison Selby",
    "placeAddress": "592 Sherbourne St, Toronto, ON M4X 1L4, Canada",
    "provider": "google-maps",
    "reviewText": None,
    "reviewDate": "2025-11-08T21:15:28.187Z",
    "reviewRating": 5,
    "authorName": "Rachel McMullan"
  },
  {
    "placeName": "Maison Selby",
    "placeAddress": "592 Sherbourne St, Toronto, ON M4X 1L4, Canada",
    "provider": "google-maps",
    "reviewText": "Recently, my wife and I had dinner at this restaurant, and I was genuinely impressed by both the service and the quality of the cuisine. We initially stopped by for a light bite, but the evening turned into a full-fledged culinary experience.\n\nI would especially like to highlight the exceptional friendliness of the staff. Our server was impeccable: attentive, discreet, and highly knowledgeable about the menu. The manager was equally pleasant, creating a sense that every guest is truly valued.\n\nThe atmosphere is remarkably cozy, offering a calm and comfortable setting perfect for an unhurried evening and effortless conversation. A particular delight was the restaurant’s signature oyster dressing. It features a delicate touch of heat that beautifully enhances the dish. For me, it was one of the culinary highlights of the night.\n\nI will be happy to return here again with my wife. And certainly more than once.",
    "reviewDate": "2025-11-08T18:07:41.155Z",
    "reviewRating": 5,
    "authorName": "Georgii Tibilov"
  },
  {
    "placeName": "Maison Selby",
    "placeAddress": "592 Sherbourne Street, Toronto, Ontario M4X 1L4 Canada",
    "provider": "tripadvisor",
    "reviewText": "Esse restaurante é muito agradável, com linda decoração e um ótimo atendimento. Comida saborosa e bem servida, com ótimas cartas de vinhos.",
    "reviewDate": "2025-10-20T00:00:00.000Z",
    "reviewRating": 5,
    "authorName": "Gustavo M"
  },
  {
    "placeName": "Maison Selby",
    "placeAddress": "592 Sherbourne Street, Toronto, Ontario M4X 1L4 Canada",
    "provider": "tripadvisor",
    "reviewText": "We had a wonderful time celebrating a family birthday at the end of August. The place had a great atmosphere, the service impeccable, and the food of a high standard. I was a little nervous booking online from the UK but my expectations were far exceeded! Thank you for a great meal :)",
    "reviewDate": "2025-09-16T00:00:00.000Z",
    "reviewRating": 5,
    "authorName": "Kathy B"
  },
  {
    "placeName": "Maison Selby",
    "placeAddress": "592 Sherbourne Street, Toronto, Ontario M4X 1L4 Canada",
    "provider": "tripadvisor",
    "reviewText": "In a wonderful old house\nComfortable well spaced seating\nOur waiter Mark aka Molly was excellent\nVery well priced wine list\nFood was superb",
    "reviewDate": "2025-08-19T00:00:00.000Z",
    "reviewRating": 5,
    "authorName": "Arthur Z"
  }
]
    for item in items:
        google_maps_id  =item.get("googleMapsPlaceId")
        place_name = item.get("placeName","")
        place_url = item.get("placeUrl","")
        place_address = item.get("placeAddress","")
        provider = item.get("provider","")
        review_text = item.get("reviewText","")
        review_date = item.get("reviewDate", None)
        review_rating = item.get("reviewRating", None)
        author_name = item.get("authorName","")
        item_count += 1
        new_review = Review(
            google_maps_id=google_maps_id,
            place_name=place_name,
            place_url=place_url,
            place_address=place_address,
            provider = provider,
            review_text=review_text,
            review_date=review_date if isinstance(review_date, datetime) else None,
            review_rating=review_rating,
            author_name=author_name,
            ignore_for_quality=False,
            ignore_for_rating=False,
            ignore_for_insufficient=False,
            selected_as_top_rating=False
        )

        # Add to session
        db.session.add(new_review)

    try:
        db.session.commit()
        msg=f"Successfully added {item_count} reviews to database"
    except Exception as e:
        db.session.rollback()
        msg=f"Error adding reviews: {e}"

    return msg

@apify_endpoints.route('/apify/test')
def apify_test():
    client = ApifyClient(APIFY_API_KEY)
    run_input = {
      "keywords": "sunset grill",
      "location": "2 Bloor Street E,  Toronto, ON M4W 1A8, Canada",
      "checkNames": 'false',
      "requireExactNameMatch": 'false',
      "deeperCityScrape": 'false',
      "maxReviewsPerPlaceAndProvider": 3,
      "scrapeReviewPictures": 'false',
      "scrapeReviewResponses": 'false'
    }

    apify_uri ="tri_angle/restaurant-review-aggregator"
    # Run the Actor and wait for it to finish
    run = client.actor(apify_uri).call(run_input=run_input)

    # Fetch and print Actor results from the run's dataset (if there are any)
    print("💾 Check your data here: https://console.apify.com/storage/datasets/" + run["defaultDatasetId"])
    restaurant_list = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        restaurant_list.append(item)
    json_string = json.dumps(restaurant_list, indent=4)
    return json_string

def is_valid_apify_api_key(api_key):
    return api_key == APIFY_API_KEY

def require_yelp_api_key(f):
    """Decorator to check if Yelp API key is configured"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not APIFY_API_KEY:
            return jsonify({
                'error': 'Configuration Error',
                'message': 'APIFY_API_KEY not configured in environment variables.'
            }), 500
        return f(*args, **kwargs)
    return decorated_function

@apify_endpoints.route('/apify/health')
def apify_health():
    """Health check endpoint"""
    api_key_configured = APIFY_API_KEY is not None
    return jsonify({
        'status': 'healthy' if api_key_configured else 'degraded',
        'api_key_configured': api_key_configured
    }), 200 if api_key_configured else 503



def get_apify_api (url, params=None):
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