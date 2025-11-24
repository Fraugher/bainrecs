# Bainrecs - Bain Restaurant Recommendations Backend API

Restaurant review aggregation for Bain & Company Toronto.

## Overview

Bainrecs provides two main API collections:

### 1. Review Collection & Aggregation (`/apify`)
- Integrates with Apify's Restaurant Review Aggregator
- Two workflows:
  - **Seed workflow**: Populate fresh database with upscale/business restaurants
  - **Restaurant Type workflow**: Add specific cuisine types (Italian, Chinese, etc.) to existing database
- Collects reviews from multiple sources (Google, TripAdvisor, etc.)
- Aggregates data in MySQL database via stored procedures
- Guided workflow with status monitoring and next-step links

### 2. Review Access & Submission (`/reviews`)
- Search and filter restaurant reviews
- Retrieve ratings and aggregated data
- Submit Bain user reviews
- Query by restaurant type or keyword

## Tech Stack

- **Framework:** Flask 3.1.2
- **Database:** MySQL (via PyMySQL)
- **ORM:** SQLAlchemy 2.0.44
- **API Integration:** Apify Client 2.3.0
- **Server:** Gunicorn (production)

## Local Development Setup

### Prerequisites
- Python 3.12
- MySQL database
- Virtual environment tool

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Fraugher/bainrecs.git
cd bainrecs
```

2. Create and activate virtual environment:
```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables (create `.env` file):
```
FLASK_ENV=development
SQL_ALCHEMY_URI=mysql+pymysql://user:pass@localhost:3306/database
APIFY_API_KEY=your_apify_key
FILE_BASE_PRODUCTION=
GITHUB_WEBHOOK_SECRET=your_webhook_secret
```

5. Database Setup

   The application uses a MySQL database with a primary `reviews` table and several derived tables created by stored procedures.

   ### Building the Database

   To create the complete database structure from scratch, use the provided build script:

   **From terminal:**
   ```bash
   mysql -h fraugher.mysql.pythonanywhere-services.com -u fraugher -p fraugher$toronto_restaurants < build_database.sql
   ```

   **From MySQL console:**
   ```sql
   source /path/to/build_database.sql
   ```

   The build script (`build_database.sql`) contains:
    - Complete table definitions
    - All stored procedures (`makerestaurants`, `makeratings`, `makebainratings`, `cleardb`)
    - Proper drop/create order for rebuilding from scratch

   See comments in `build_database.sql` for detailed information about the database structure and procedures.

6. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## Docker Deployment

### Build the Image
```bash
docker build -t bainrecs-backend:latest .
```

### Run the Container
```bash
docker run -d -p 5000:5000 \
  -v "$(pwd)/.env:/app/.env" \
  --name bainrecs-backend \
  bainrecs-backend:latest
```

See [DOCKER.md](DOCKER.md) for detailed Docker instructions.

## API Endpoints

### Apify Collection Endpoints

#### Workflow 1: Seeding a Fresh Database ("All Restaurants")
Use this workflow to create a new database with general upscale/business restaurants:

**Step 1: Start the run**
- `GET /apify/start-run` 
- Starts Apify scraper for upscale restaurants using base configuration
- Uses `apify_run_inputs.json` with keywords: `["upscale", "business", "quiet", "private dining"]`
- Crawls ~200 restaurants
- Returns run ID and link to status page
- a full Apify run like this can take more than 30 minutes to complete

**Step 2: Check status**
- `GET /apify/wait-run?run={run_id}` 
- Monitor scraping progress
- Refresh page to check status updates
- Proceed when status shows "SUCCEEDED"

**Step 3: Populate database**
- `POST /apify/pop-db?runId={run_id}` or `GET /apify/pop-db?runId={run_id}`
- **WARNING:** Cleans entire database first, then imports all reviews
- Adds reviews to `reviews` table
- Executes `MAKE_RATINGS` procedure (creates aggregated ratings)
- Executes `MAKE_RESTAURANTS` procedure (creates restaurant records)

**Apify Webhook**
There is a disabled webhook set up in Apify to automatically trigger the pop-db endpoint. Remember that a full Apify run like this can take more than 30 minutes to complete.


#### Workflow 2: Adding Restaurant Types (Incremental)
Use this workflow to add specific cuisine types to an existing database:

**Step 1: Start type-specific run**
- `GET /apify/start-restaurant-type-run?restaurant_type={type}` 
- Starts scraper for a specific cuisine type
- Examples: 
  - `?restaurant_type=Italian`
  - `?restaurant_type=Chinese`
  - `?restaurant_type=Japanese`
- Overrides base configuration keywords with the specified type
- Crawls ~50 restaurants per type
- Returns run ID and link to status page

**Step 2: Check status**
- `GET /apify/wait-restaurant-type-run?run={run_id}&restaurant_type={type}` 
- Monitor scraping progress for this specific type
- Displays "Next step" link automatically when complete
- Status page includes direct link to populate step

**Step 3: Add to database**
- `POST /apify/pop-restaurant-type?runId={run_id}&restaurant_type={type}` or `GET /apify/pop-restaurant-type?runId={run_id}&restaurant_type={type}`
- Adds new reviews to `reviews` table
- Creates restaurant-type associations in `restaurants` table
- Does NOT clean database (incremental add)
- Executes `MAKE_RATINGS` procedure to update aggregated ratings
- Returns count of reviews added and restaurants tagged

**Apify Webhook**
For a second prototype, would be good to automate this process flow with an Apify Webhook that triggers pop-restaurant-type, some hacking required to track restaurant_type by run_id on the python side

#### Utility Endpoints
- `POST /apify/clean-db` - Clear all data from database
- `GET /apify/test-pop` - Populate with hardcoded test data (6 sample reviews)
- `GET /apify/pop-file` - Populate from `json/search.json` file (for testing)
- `GET /apify/health` - API health check (returns API key configuration status)

#### Configuration Files
**`apify_run_inputs.json`** - Single configuration file for both workflows
```json
{
  "keywords": ["upscale", "business", "quiet", "private dining"],
  "_keywordGetsOverridenWhenSearchingByRestaurantType": ["Italian"],
  "location": "2 Bloor Street E, Toronto, ON M4W 1A8, Canada",
  "maxDistanceMeters": 10000,
  "maxCrawledPlaces": 50,
  "_maxCrawledPlaces_fullRun": 200,
  "maxReviewsPerPlaceAndProvider": 10,
  "_maxReviewsPerPlaceAndProvider_dev": 1,
  "reviewsFromDate": "2022-11-01",
  "scrapeReviewPictures": false,
  "scrapeReviewResponses": false
}
```

Notes:
- Base keywords used for "All Restaurants" workflow
- Type-specific runs override `restaurant_type` and `keywords` fields
- `_comment_` prefixed fields are documentation only (not used by API)
- Adjust `maxReviewsPerPlaceAndProvider` and `maxCrawledPlaces` to conserve Apify credits during development

### Review Access Endpoints

#### Get All Data
- `GET /reviews/ratings` - Get all ratings for all restaurants, returns restaurant info and rating
- `GET /reviews/reviews` - Get all reviews for all restaurants, returns detailed reviews

#### Get Specific Restaurant
- `GET /reviews/ratings/<google_maps_id>` - Get ratings, , returns info and rating for a specific restaurant
- `GET /reviews/reviews/<google_maps_id>` - Get reviews for specific restaurant, returns detailed reviews

#### Search & Filter
- `GET /reviews/search_reviews` - Search reviews with filters
  - Query parameters: keyword, restaurant_type, min_rating, etc.
- `GET /reviews/search_ratings` - Search ratings with filters
  - Query parameters: restaurant_type, min_rating, max_rating, etc.

#### Submit Reviews
- `POST /reviews/submit-review` - Submit a Bain user review
  - Requires: google_maps_id, place_name, review_text, review_rating, author_name

## Testing

Run tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=.
```

## Project Structure

```
bainrecs/
├── app.py                 # Main application
├── config.py              # Configuration classes
├── extensions.py          # SQLAlchemy setup
├── models.py              # Database models
├── apify_api/
│   └── apify_endpoints.py # Apify integration endpoints
├── pa_api/                # Our custom Python Anywhere APIs
│   └── capture_review.py  # POST route save a Bain review
│   └── get_reviews.py     # Our API, searches and gets restaurants and reviews
│   └── deploy_app.py      # util to autodeploy on Python Anywhere from github webhook
├── json/
│   └── apify_run_inputs.json  # Apify configuration
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker configuration
└── .dockerignore          # Docker ignore patterns
```

## Workflow Examples

### Example 1: Fresh Database Setup
```bash
# 1. Start scraping upscale restaurants
curl http://localhost:5000/apify/start-run

# 2. Check status (replace {run_id} with actual ID)
curl http://localhost:5000/apify/wait-run?run={run_id}

# 3. When SUCCEEDED, populate database
curl -X POST http://localhost:5000/apify/pop-db?runId={run_id}
```

### Example 2: Add Italian Restaurants
```bash
# 1. Start Italian restaurant scraping
curl http://localhost:5000/apify/start-restaurant-type-run?restaurant_type=Italian

# 2. Check status
curl http://localhost:5000/apify/wait-restaurant-type-run?run={run_id}&restaurant_type=Italian

# 3. Add to existing database
curl -X POST http://localhost:5000/apify/pop-restaurant-type?runId={run_id}&restaurant_type=Italian
```

### Example 3: Query Restaurants
```bash
# Get all Italian restaurants
curl http://localhost:5000/reviews/search_ratings?restaurant_type=Italian

# Search reviews by keyword
curl http://localhost:5000/reviews/search_reviews?keyword=Bistro&restaurant_type=All
```

## Database Schema

### Main Tables
- **reviews**: All scraped reviews (source of truth)
- **ratings**: Aggregated ratings per restaurant (created by `MAKE_RATINGS`)
- **restaurants**: Restaurant meta data and -type associations (created by `MAKE_RESTAURANTS` and aggregated in type-runs)
- **bain_ratings**: Ratings from Bain staff reviews (created by `MAKEBAINRATINGS`)

### Stored Procedures
- `MAKE_RATINGS`: Aggregates review data into ratings table
- `MAKE_RESTAURANTS`: Creates unique restaurant records from reviews
- `MAKEBAINRATINGS`: Combines scraped reviews with Bain submissions
- `CLEARDB`: Truncates all tables for fresh start, but saves Bain Reviews
<br /><br />
#### Project Link

[https://github.com/Fraugher/bainrecs](https://github.com/Fraugher/bainrecs)
<br /><br />