import os
from apify_client import ApifyClient
from dotenv import load_dotenv
from flask import Blueprint, jsonify, json, request
from functools import wraps
from datetime import datetime
from extensions import db
import json
from models import Review
from apify_client.errors import ApifyApiError

load_dotenv()
apify_endpoints = Blueprint('apify_endpoints', __name__)

APIFY_API_KEY = os.getenv('APIFY_API_KEY')
YELP_API_KEY = os.getenv('YELP_API_KEY')
PYTHONANYWHERE_API_KEY = os.getenv('PYTHONANYWHERE_API_KEY')
SQL_ALCHEMY_URI = os.getenv('SQL_ALCHEMY_URI')

@apify_endpoints.route('/startpop')
def startpop():
    client = ApifyClient(APIFY_API_KEY)
    run_input = {
      "keywords": ["upscale," "business," "quiet", "private dining"],
      "location": "2 Bloor Street E,  Toronto, ON M4W 1A8, Canada",
      "maxDistanceMeters": 10, #10000,
      "checkNames": False,
      "requireExactNameMatch": False,
      "deeperCityScrape": False,
      "maxReviewsPerPlaceAndProvider": 1, #10,
      "reviewsFromDate" : "2021-01-01",
      "scrapeReviewPictures": False,
      "scrapeReviewResponses": False
    }

    apify_uri ="tri_angle/restaurant-review-aggregator"
    actor_run = client.actor(apify_uri).start(run_input=run_input)
    run_id = actor_run["id"]
    return f"<div>Reviews scraping run started with ID: {run_id} at {datetime.now().strftime("%H:%M:%S")}</div><div>visit <a target='_blank' href='{request.host_url}apify/waitforreviews?run={run_id}'>{request.host_url}apify/waitforreviews?run={run_id}</a> for status update</div>"

@apify_endpoints.route('/waitforreviews')
def waitforreviews():
    run_id = request.args.get('run')
    if run_id is None:
        return "Bad Request"
    client = ApifyClient(APIFY_API_KEY)
    try:
        run_client = client.run(run_id)
        run_info = run_client.get()
        status = run_info['status']
        return f"Run status: {status} for run: {run_id} at {datetime.now().strftime("%H:%M:%S")}<div><a href='.'>refresh</a> this page for status updates</div>"
    except ApifyApiError as e:
        if "does not exist" in str(e).lower() or "not found" in str(e).lower():
            return f"Error retrieving run with ID '{run_id}': {e}. The provided run ID likely does not exist or is incorrect."
        elif "badly formed" in str(e).lower() or "invalid format" in str(e).lower():
            return f"Error retrieving run with ID '{run_id}': {e}. The provided run ID is badly formed or in an invalid format."
        else:
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                return f"Error retrieving run with ID '{run_id}': {e}.  The provided run ID likely does not exist or is incorrect."
            elif "badly formed" in str(e).lower() or "invalid format" in str(e).lower():
                return f"Error retrieving run with ID '{run_id}': {e}. The provided run ID is badly formed or in an invalid format."
            else:
                return f"Error retrieving run with ID '{run_id}': {e}. An unexpected Apify API error occurred."
    except Exception as e:
        # Catch any other unexpected errors
        return f"An unexpected error occurred: {e}. An unexpected Apify API error occurred."

@apify_endpoints.route('/one2db')
def one2db():
    if request.is_json:
        try:
            review=request.get_json()
        except (Exception,):
            return {"message": "Malformed request"}, 400
    else:
        return {"message": "Malformed request"}, 400

    # validate this data...
    google_maps_id = review.get("googleMapsPlaceId")
    place_name = review.get("placeName","")
    place_url = review.get("placeUrl","")
    place_address = review.get("placeAddress","")
    provider = review.get("provider","Bain")
    review_text = review.get("reviewText","")
    review_date = review.get("reviewDate", datetime.now().strftime("%Y-%m-%d"))
    review_rating = review.get("reviewRating", None)
    author_name = review.get("authorName","")

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
    db.session.add(new_review)
    try:
        db.session.commit()
        return {"message": "Successfully added your Bain review to database"},201
    except Exception as e:
        db.session.rollback()
        return {"message": f"Error adding your review to our database, detail: {e}"},200

@apify_endpoints.route('/popdb', methods=['POST'])
def popdb():
    review_count = 0
    run_id = request.args.get('run')
    if run_id is None:
        return "Bad Request"
    client = ApifyClient(APIFY_API_KEY)
    run_client = client.run(run_id)
    run_info = run_client.get()
    if run_info['status'] != "SUCCEEDED":
        return f"Data is not ready for run with ID {run_id}, run status is '{run_info['status']}'"
    if run_info and 'defaultDatasetId' in run_info and run_info['defaultDatasetId']:
        # return f"run status is '{run_info['status']}'"
        for review in client.dataset(run_info["defaultDatasetId"]).iterate_items():
            google_maps_id  =review.get("googleMapsPlaceId")
            place_name = review.get("placeName","")
            place_url = review.get("placeUrl","")
            place_address = review.get("placeAddress","")
            provider = review.get("provider","")
            review_title= review.get("reviewTitle", "")
            review_text = review.get("reviewText","")
            review_date = review.get("reviewDate", None)
            review_rating = review.get("reviewRating", None)
            author_name = review.get("authorName","")
            review_count += 1
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
            msg=f"Successfully added {review_count} reviews to database"
        except Exception as e:
            db.session.rollback()
            msg=f"Error adding reviews: {e}"
    else:
        msg= f"Error retrieving run with ID '{run_id}'."
    return msg

@apify_endpoints.route('/testpop')
def apify_testpop():
    review_count=0
    reviews = [
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
    for review in reviews:
        google_maps_id  =review.get("googleMapsPlaceId")
        place_name = review.get("placeName","")
        place_url = review.get("placeUrl","")
        place_address = review.get("placeAddress","")
        provider = review.get("provider","")
        review_title= review.get("reviewTitle","")
        review_text = review.get("reviewText", "")
        review_date = review.get("reviewDate", None)
        review_rating = review.get("reviewRating", None)
        author_name = review.get("authorName","")
        review_count += 1
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
        msg=f"Successfully added {review_count} reviews to database"
    except Exception as e:
        db.session.rollback()
        msg=f"Error adding reviews: {e}"

    return msg


@apify_endpoints.route('/debug')
def apify_debug():
    import os

    current_dir = os.getcwd()
    file_name = 'search.json'

    # Check multiple possible locations
    locations = [
        os.path.join(current_dir, file_name),
        os.path.join('/home/fraugher/bainrecs', file_name),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name),
    ]

    debug_info = f"<h3>Debug Info:</h3>"
    debug_info += f"<p>Current working directory: {current_dir}</p>"
    debug_info += f"<p>This file location: {os.path.abspath(__file__)}</p>"
    debug_info += f"<h4>Checking locations:</h4><ul>"

    for loc in locations:
        exists = os.path.exists(loc)
        debug_info += f"<li>{loc} - {'✓ EXISTS' if exists else '✗ NOT FOUND'}</li>"

    # List files in current directory
    debug_info += f"</ul><h4>Files in {current_dir}:</h4><ul>"
    try:
        for f in os.listdir(current_dir):
            debug_info += f"<li>{f}</li>"
    except Exception as e:
        debug_info += f"<li>Error listing: {e}</li>"

    debug_info += "</ul>"

    # List files in project root
    debug_info += f"<h4>Files in /home/fraugher/bainrecs:</h4><ul>"
    try:
        for f in os.listdir('/home/fraugher/bainrecs'):
            debug_info += f"<li>{f}</li>"
    except Exception as e:
        debug_info += f"<li>Error listing: {e}</li>"

    debug_info += "</ul>"

    return debug_info

@apify_endpoints.route('/popfromfile')
def apify_popfromfile():
    file_path = '/home/fraugher/bainrecs/search.json'
    review_count=0
    try:
        with open(file_path, 'r') as search_resuls_file:
            reviews = json.load(search_resuls_file)
    except FileNotFoundError:
        return "Error: The file 'search.json' was not found." #}, 404
    except json.JSONDecodeError:
        return "Error: Could not decode JSON from the file." #}, 500
    except Exception as e:
        return f"An unexpected error occurred: {e}" #}, 500


    for review in reviews:
        google_maps_id = review.get("googleMapsPlaceId")
        place_name = review.get("placeName","")
        place_url = review.get("placeUrl","")
        place_address = review.get("placeAddress","")
        provider = review.get("provider","")
        review_text = review.get("reviewText","")
        review_date = review.get("reviewDate", None)
        review_rating = review.get("reviewRating", None)
        author_name = review.get("authorName","")
        review_count += 1
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
        msg=f"Successfully added {review_count} reviews to database"
    except Exception as e:
        db.session.rollback()
        msg=f"Error adding reviews: {e}"

    return msg

@apify_endpoints.route('/test')
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
    for review in client.dataset(run["defaultDatasetId"]).iterate_items():
        restaurant_list.append(review)
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

@apify_endpoints.route('/health')
def apify_health():
    """Health check endpoint"""
    api_key_configured = APIFY_API_KEY is not None
    return jsonify({
        'status': 'healthy' if api_key_configured else 'degraded',
        'api_key_configured': api_key_configured
    }), 200 if api_key_configured else 503


def handle_apify_error(status_code, response_data):
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