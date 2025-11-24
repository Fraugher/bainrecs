from apify_client import ApifyClient
from flask import Blueprint, jsonify, json, request, current_app
from functools import wraps
from datetime import datetime
from extensions import db
import json
from models import Review, Restaurant
from apify_client.errors import ApifyApiError

apify_endpoints = Blueprint('apify_endpoints', __name__)

def require_apify_api_key(f): 
    """decorator to ensure api key"""
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

def get_run_status(run_id):
    """Helper function to get Apify run status"""
    client = ApifyClient(current_app.config['APIFY_API_KEY'])
    try:
        run_client = client.run(run_id)
        run_info = run_client.get()
        return run_info['status'], None
    except ApifyApiError as e:
        if "does not exist" in str(e).lower() or "not found" in str(e).lower():
            return None, f"Error retrieving run with ID '{run_id}': {e}. The provided run ID likely does not exist or is incorrect."
        elif "badly formed" in str(e).lower() or "invalid format" in str(e).lower():
            return None, f"Error retrieving run with ID '{run_id}': {e}. The provided run ID is badly formed or in an invalid format."
        else:
            return None, f"Error retrieving run with ID '{run_id}': {e}. An unexpected Apify API error occurred."
    except Exception as e:
        return None, f"An unexpected error occurred: {e}"

# start-run, wait-run, and pop-db are used in concert to seed a new database with "all" restaurants
# they rely on apify_run_inputs.json
@apify_endpoints.route('/start-run')
@require_apify_api_key
def start_run():
    client = ApifyClient(current_app.config['APIFY_API_KEY'])
    file_path = current_app.config['FILE_BASE'] + 'json/apify_run_inputs.json'
    with open(file_path, 'r') as f:
        run_input = json.load(f)
    run_input['maxCrawledPlaces'] = 200 # we want more places for the 'All restaurants' run

    actor_run = client.actor(current_app.config['APIFY_RESTAURANT_REVIEW_URI']).start(run_input=run_input)
    run_id = actor_run["id"]
    return f"""<div>Reviews scraping run started with ID: {run_id} at {datetime.now().strftime("%H:%M:%S")}</div>
        <div>visit <a target='_blank' href='{request.host_url}apify/wait-run?run={run_id}'>
        {request.host_url}apify/wait-run?run={run_id}</a> for status update</div>""", 200

@apify_endpoints.route('/wait-run')
@require_apify_api_key
def wait_run():
    run_id = request.args.get('run')
    if run_id is None:
        return "Bad Request: run parameter required"

    status, error = get_run_status(run_id)
    if error:
        return error

    return f"Run status: {status} for run: {run_id} at {datetime.now().strftime("%H:%M:%S")}<div><a href='.'>refresh</a> this page for status updates</div>"

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
            new_review = Review.from_apify_data(review)
            db.session.add(new_review)
            review_count += 1
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

@apify_endpoints.route('/start-restaurant-type-run')
@require_apify_api_key
def start_restaurant_type_run ():
    restaurant_type = request.args.get('restaurant_type')
    if not restaurant_type:
        return "Error: 'restaurant_type' query parameter is required", 400

    client = ApifyClient(current_app.config['APIFY_API_KEY'])
    file_path = current_app.config['FILE_BASE'] + 'json/apify_run_inputs.json'
    with open(file_path, 'r') as f:
        run_input = json.load(f)

    # Override with the type from query string
    run_input['restaurant_type'] = restaurant_type
    run_input['keywords'] = [restaurant_type]

    actor_run = client.actor(current_app.config['APIFY_RESTAURANT_REVIEW_URI']).start(run_input=run_input)
    run_id = actor_run["id"]
    return f"""<div>Reviews scraping run started for {restaurant_type} restaurants with ID: {run_id} at {datetime.now().strftime("%H:%M:%S")}</div>
        <div>visit <a target='_blank' href='{request.host_url}apify/wait-reviews?run={run_id}&restaurant_type={restaurant_type}'>
        {request.host_url}apify/wait-restaurant-type-run?run={run_id}&restaurant_type={restaurant_type}</a> for status update</div>""", 200

@apify_endpoints.route('/wait-restaurant-type-run')
@require_apify_api_key
def wait_restaurant_type_run():
    run_id = request.args.get('run')
    restaurant_type = request.args.get('restaurant_type')

    if run_id is None:
        return "Bad Request: run parameter required"
    if restaurant_type is None:
        return "Bad Request: restaurant_type parameter required"

    status, error = get_run_status(run_id)
    if error:
        return error

    status_html = f"""<div>Run status: {status} for {restaurant_type} restaurants (run: {run_id}) at {datetime.now().strftime("%H:%M:%S")}</div>"""

    if status == "SUCCEEDED":
        status_html += f"""<div style='margin-top: 10px; padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px;'>
            ✓ Reviews ready! Next step: 
            <a target='_blank' href='{request.host_url}apify/pop-restaurant-type?runId={run_id}&restaurant_type={restaurant_type}'>
            Add {restaurant_type} restaurants to database</a>
        </div>"""
    else:
        status_html += f"<div><a href='.'>refresh</a> this page for status updates</div>"

    return status_html

@apify_endpoints.route('/pop-restaurant-type', methods=['GET', 'POST'])
@require_apify_api_key
def pop_restaurant_type():
    review_count = 0
    restaurant_added_count = 0
    restaurant_skipped_count = 0

    if request.method == 'POST':
        run_id = request.json.get('runId') if request.is_json else None
        restaurant_type = request.json.get('restaurant_type') if request.is_json else None
    else:
        run_id = request.args.get('runId')
        restaurant_type = request.args.get('restaurant_type')

    if run_id is None:
        return "Bad Request: runId parameter required"
    if restaurant_type is None:
        return "Bad Request: restaurant_type parameter required"

    client = ApifyClient(current_app.config['APIFY_API_KEY'])
    run_client = client.run(run_id)
    run_info = run_client.get()
    if run_info['status'] != "SUCCEEDED":
        return f"Data is not ready for run with ID {run_id}, run status is '{run_info['status']}'"

    if run_info and 'defaultDatasetId' in run_info and run_info['defaultDatasetId']:
        for review in client.dataset(run_info["defaultDatasetId"]).iterate_items():
            new_review=Review.from_apify_data(review)
            db.session.add(new_review)
            review_count += 1

            # Add restaurant type entry
            google_maps_id = review.get("googleMapsPlaceId")
            place_name = review.get("placeName", "")
            place_address = review.get("placeAddress", "")

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
                restaurant_added_count += 1
            else:
                restaurant_skipped_count += 1

        try:
            db.session.commit()
            db.session.expire_all()
            db.session.execute(db.text(current_app.config['DB_PROCEDURE_MAKE_RATINGS']))
            db.session.commit()

            msg = f"Successfully added {review_count} reviews and {restaurant_added_count} {restaurant_type} restaurants (skipped {restaurant_skipped_count} duplicates)"
        except Exception as e:
            db.session.rollback()
            msg = f"Error adding data: {e}"
    else:
        msg = f"Error retrieving run with ID '{run_id}'."

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
        new_review = Review.from_apify_data(review)
        db.session.add(new_review)
        review_count += 1
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
        new_review = Review.from_apify_data(review)
        db.session.add(new_review)
        review_count += 1
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