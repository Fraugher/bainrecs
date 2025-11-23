from apify_client import ApifyClient
from flask import Blueprint, jsonify, json, request, current_app
from functools import wraps
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from extensions import db
import json
from models import Review, Restaurant
from apify_client.errors import ApifyApiError

apify_endpoints = Blueprint('apify_endpoints', __name__)

def require_apify_api_key(f): #decorator to ensure api key
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_app.config['APIFY_API_KEY']:
            return jsonify({
                'error': 'Configuration Error',
                'message': 'APIFY_API_KEY not configured in environment variables.'
            }), 500
        return f(*args, **kwargs)
    return decorated_function

def clean_database():
    """Helper function to clean the database"""
    try:
        db.session.execute(db.text(current_app.config['DB_PROCEDURE_CLEAR_DB']))
        db.session.commit()
        return True, "Successfully cleaned the database"
    except Exception as e:
        db.session.rollback()
        return False, f"Error cleaning the database: {e}"

@apify_endpoints.route('/start-run')
@require_apify_api_key
def start_run():
    client = ApifyClient(current_app.config['APIFY_API_KEY'])
    file_path = current_app.config['FILE_BASE'] + 'json/apify_run_inputs.json'
    with open(file_path, 'r') as f:
        run_input = json.load(f)

    actor_run = client.actor(current_app.config['APIFY_RESTAURANT_REVIEW_URI']).start(run_input=run_input)
    run_id = actor_run["id"]
    return f"""<div>Reviews scraping run started with ID: {run_id} at {datetime.now().strftime("%H:%M:%S")}</div>
        <div>visit <a target='_blank' href='{request.host_url}apify/wait-run?run={run_id}'>
        {request.host_url}apify/wait-reviews?run={run_id}</a> for status update</div>""", 200

@apify_endpoints.route('/start-run-for-types')
@require_apify_api_key
def start_run_for_types():
    client = ApifyClient(current_app.config['APIFY_API_KEY'])
    file_path = current_app.config['FILE_BASE'] + 'json/apify_run_for_types_inputs.json'
    with open(file_path, 'r') as f:
        run_input = json.load(f)

    actor_run = client.actor(current_app.config['APIFY_RESTAURANT_REVIEW_URI']).start(run_input=run_input)
    run_id = actor_run["id"]
    return f"""<div>Reviews scraping run started with ID: {run_id} at {datetime.now().strftime("%H:%M:%S")}</div>
        <div>visit <a target='_blank' href='{request.host_url}apify/wait-run?run={run_id}'>
        {request.host_url}apify/wait-reviews?run={run_id}</a> for status update</div>""", 200

@apify_endpoints.route('/wait-run')
@require_apify_api_key
def wait_run():
    run_id = request.args.get('run')
    if run_id is None:
        return "Bad Request"
    client = ApifyClient(current_app.config['APIFY_API_KEY'])
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
        return f"An unexpected error occurred: {e}. An unexpected Apify API error occurred."

@apify_endpoints.route('/pop-db', methods=['GET', 'POST'])
@require_apify_api_key
def pop_db():

    review_count = 0
    if request.method == 'POST':
        run_id = request.json.get('runId') if request.is_json else None
    else:
        run_id = request.args.get('runId')

    if run_id is None:
        return "Bad Request: runId parameter required"
    client = ApifyClient(current_app.config['APIFY_API_KEY'])
    run_client = client.run(run_id)
    run_info = run_client.get()
    if run_info['status'] != "SUCCEEDED":
        return f"Data is not ready for run with ID {run_id}, run status is '{run_info['status']}'"

    # Clean out database first
    success, clean_msg = clean_database()
    if not success:
        return clean_msg

    if run_info and 'defaultDatasetId' in run_info and run_info['defaultDatasetId']:  # this is all apify protocol
        for review in client.dataset(run_info["defaultDatasetId"]).iterate_items():
            google_maps_id = review.get("googleMapsPlaceId")
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
                review_title=review_title,
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
            db.session.expire_all()
            db.session.execute(db.text(current_app.config['DB_PROCEDURE_MAKE_RATINGS']))
            db.session.execute(db.text(current_app.config['DB_PROCEDURE_MAKE_RESTAURANTS']))
            db.session.commit()
            msg=f"Successfully added {review_count} reviews to database"
        except Exception as e:
            db.session.rollback()
            msg=f"Error adding reviews: {e}"
    else:
        msg= f"Error retrieving run with ID '{run_id}'."
    return msg

@apify_endpoints.route('/pop-reviews-only', methods=['GET', 'POST'])
@require_apify_api_key
def pop_reviews_only    ():
    review_count = 0
    if request.method == 'POST':
        run_id = request.json.get('runId') if request.is_json else None
    else:
        run_id = request.args.get('runId')

    if run_id is None:
        return "Bad Request: runId parameter required"
    client = ApifyClient(current_app.config['APIFY_API_KEY'])
    run_client = client.run(run_id)
    run_info = run_client.get()
    if run_info['status'] != "SUCCEEDED":
        return f"Data is not ready for run with ID {run_id}, run status is '{run_info['status']}'"

    if run_info and 'defaultDatasetId' in run_info and run_info['defaultDatasetId']:  # this is all apify protocol
        for review in client.dataset(run_info["defaultDatasetId"]).iterate_items():
            google_maps_id = review.get("googleMapsPlaceId")
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
                review_title=review_title,
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
            db.session.expire_all()
            db.session.execute(db.text(current_app.config['DB_PROCEDURE_MAKE_RATINGS']))
            #db.session.execute(db.text(current_app.config['DB_PROCEDURE_MAKE_RESTAURANTS']))
            db.session.commit()
            msg=f"Successfully added {review_count} reviews to database"
        except Exception as e:
            db.session.rollback()
            msg=f"Error adding reviews: {e}"
    else:
        msg= f"Error retrieving run with ID '{run_id}'."
    return msg


@apify_endpoints.route('/pop-type', methods=['GET', 'POST'])
@require_apify_api_key
def pop_type():
    added_count = 0
    skipped_count = 0
    if request.method == 'POST':
        run_id = request.json.get('runId') if request.is_json else None
    else:
        run_id = request.args.get('runId')

    if run_id is None:
        return "Bad Request: runId parameter required"
    client = ApifyClient(current_app.config['APIFY_API_KEY'])
    run_client = client.run(run_id)
    run_info = run_client.get()
    if run_info['status'] != "SUCCEEDED":
        return f"Data is not ready for run with ID {run_id}, run status is '{run_info['status']}'"
    # a run type is a run for a particular type of restaurant like Italian, Japanese, American, etc.
    type_file_path = current_app.config['FILE_BASE'] + 'json/apify_run_for_types_inputs.json'
    with open(type_file_path, 'r') as f:  # this is a hack for now to get different types like Chinese, Italian
        run_type = json.load(f)
        restaurant_type = run_type.get('restaurant_type', 'all')

    if run_info and 'defaultDatasetId' in run_info and run_info['defaultDatasetId']:  # this is all apify protocol
        for review in client.dataset(run_info["defaultDatasetId"]).iterate_items():
            google_maps_id = review.get("googleMapsPlaceId")
            place_name = review.get("placeName","")
            place_address = review.get("placeAddress","")

            # Check if this combination already exists
            existing = Restaurant.query.filter_by(
                google_maps_id=google_maps_id,
                restaurant_type=restaurant_type
            ).first()

            if not existing:
                new_restaurant_with_type = Restaurant(
                    google_maps_id=google_maps_id,
                    place_name=place_name,
                    place_address=place_address,
                    restaurant_type=restaurant_type,
                )
                db.session.add(new_restaurant_with_type)
                added_count += 1
            else:
                skipped_count += 1

            # new_restaurant_with_type = Restaurant(
            #     google_maps_id=google_maps_id,
            #     place_name=place_name,
            #     place_address=place_address,
            #     restaurant_type=restaurant_type,
            # )
            # db.session.add(new_restaurant_with_type)
            # # print(f"ADDING RESTAIRANT WITH TYPE: {restaurant_type}")
            # # print(f" with place name: {place_name}")
            # # print(f" with google_maps_id: {google_maps_id}")
        try:
            db.session.commit()
            msg = f"Added {added_count} restaurants, skipped {skipped_count} duplicates"
            #msg=f"Successfully added restaurant types to database"
        # except IntegrityError as e:
        #     db.session.rollback()
        #     msg = f"Some restaurants and types already existed (skipped duplicates)"
        except Exception as e:
            db.session.rollback()
            msg=f"Error adding restaurant types : {e}"
    else:
        msg= f"Error retrieving run with ID '{run_id}'."
    return msg

@apify_endpoints.route('/clean-db', methods=['POST'])
@require_apify_api_key
def clean_db():
    success, msg = clean_database()
    return msg

@apify_endpoints.route('/test-pop')
def test_pop():
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
            review_title=review_title,
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

@apify_endpoints.route('/pop-file')
def pop_file():
    file_path = current_app.config['FILE_BASE'] + 'json/search.json'
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

@apify_endpoints.route('/health')
def health():
    api_key_configured = current_app.config['APIFY_API_KEY'] is not None
    return jsonify({
        'status': 'healthy' if api_key_configured else 'degraded',
        'api_key_configured': api_key_configured
    }), 200 if api_key_configured else 503

# @apify_endpoints.route('/debug')
# def apify_debug():
#     import os
#
#     current_dir = os.getcwd()
#     file_name = 'json/search.json'
#
#     # Check multiple possible locations
#     locations = [
#         os.path.join(current_dir, file_name),
#         os.path.join('/home/fraugher/bainrecs', file_name),
#         os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name),
#     ]
#
#     debug_info = f"<h3>Debug Info:</h3>"
#     debug_info += f"<p>Current working directory: {current_dir}</p>"
#     debug_info += f"<p>This file location: {os.path.abspath(__file__)}</p>"
#     debug_info += f"<h4>Checking locations:</h4><ul>"
#
#     for loc in locations:
#         exists = os.path.exists(loc)
#         debug_info += f"<li>{loc} - {'✓ EXISTS' if exists else '✗ NOT FOUND'}</li>"
#
#     # List files in current directory
#     debug_info += f"</ul><h4>Files in {current_dir}:</h4><ul>"
#     try:
#         for f in os.listdir(current_dir):
#             debug_info += f"<li>{f}</li>"
#     except Exception as e:
#         debug_info += f"<li>Error listing: {e}</li>"
#
#     debug_info += "</ul>"
#
#     # List files in project root
#     debug_info += f"<h4>Files in /home/fraugher/bainrecs:</h4><ul>"
#     try:
#         for f in os.listdir('/home/fraugher/bainrecs'):
#             debug_info += f"<li>{f}</li>"
#     except Exception as e:
#         debug_info += f"<li>Error listing: {e}</li>"
#
#     debug_info += "</ul>"
#
#     return debug_info

# @apify_endpoints.route('/debug')
# def apify_debug():
#     import os
#
#     current_dir = os.getcwd()
#     file_name = 'json/search.json'
#
#     # Check multiple possible locations
#     locations = [
#         os.path.join(current_dir, file_name),
#         os.path.join('/home/fraugher/bainrecs', file_name),
#         os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name),
#     ]
#
#     debug_info = f"<h3>Debug Info:</h3>"
#     debug_info += f"<p>Current working directory: {current_dir}</p>"
#     debug_info += f"<p>This file location: {os.path.abspath(__file__)}</p>"
#     debug_info += f"<h4>Checking locations:</h4><ul>"
#
#     for loc in locations:
#         exists = os.path.exists(loc)
#         debug_info += f"<li>{loc} - {'✓ EXISTS' if exists else '✗ NOT FOUND'}</li>"
#
#     # List files in current directory
#     debug_info += f"</ul><h4>Files in {current_dir}:</h4><ul>"
#     try:
#         for f in os.listdir(current_dir):
#             debug_info += f"<li>{f}</li>"
#     except Exception as e:
#         debug_info += f"<li>Error listing: {e}</li>"
#
#     debug_info += "</ul>"
#
#     # List files in project root
#     debug_info += f"<h4>Files in /home/fraugher/bainrecs:</h4><ul>"
#     try:
#         for f in os.listdir('/home/fraugher/bainrecs'):
#             debug_info += f"<li>{f}</li>"
#     except Exception as e:
#         debug_info += f"<li>Error listing: {e}</li>"
#
#     debug_info += "</ul>"
#
#     return debug_info


# @apify_endpoints.route('/one2db')
# def one2db():
#     if request.is_json:
#         try:
#             review=request.get_json()
#         except (Exception,):
#             return {"message": "Malformed request"}, 400
#     else:
#         return {"message": "Malformed request"}, 400
#
#     # validate this data...
#     google_maps_id = review.get("googleMapsPlaceId")
#     place_name = review.get("placeName","")
#     place_url = review.get("placeUrl","")
#     place_address = review.get("placeAddress","")
#     provider = review.get("provider","Bain")
#     review_text = review.get("reviewText","")
#     review_date = review.get("reviewDate", datetime.now().strftime("%Y-%m-%d"))
#     review_rating = review.get("reviewRating", None)
#     author_name = review.get("authorName","")
#
#     new_review = Review(
#         google_maps_id=google_maps_id,
#         place_name=place_name,
#         place_url=place_url,
#         place_address=place_address,
#         provider = provider,
#         review_text=review_text,
#         review_date=review_date if isinstance(review_date, datetime) else None,
#         review_rating=review_rating,
#         author_name=author_name,
#         ignore_for_quality=False,
#         ignore_for_rating=False,
#         ignore_for_insufficient=False,
#         selected_as_top_rating=False
#     )
#     db.session.add(new_review)
#     try:
#         db.session.commit()
#         return {"message": "Successfully added your Bain review to database"},201
#     except Exception as e:
#         db.session.rollback()
#         return {"message": f"Error adding your review to our database, detail: {e}"},200
