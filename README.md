# Bainrecs - Bain Restaurant Recommendations Backend API

Restaurant review aggregation for Bain & Company Toronto.

## Overview

Bainrecs provides two main API collections:

### 1. Review Collection & Aggregation (`/apify`)
- Integrates with Apify's Restaurant Review Aggregator
- Collects reviews from multiple sources (Google, TripAdvisor, etc.)
- Populates and aggregates data in MySQL database

### 2. Review Access & Submission (`/reviews`)
- Search and filter restaurant reviews
- Retrieve ratings and aggregated data
- Submit Bain user reviews
- Query by type of restaurant or keyword

## Tech Stack

- **Framework:** Flask 3.1.2
- **Database:** MySQL (via PyMySQL)
- **ORM:** SQLAlchemy 2.0.44
- **API Integration:** Apify Client 2.3.0
- **Server:** Gunicorn (production)

## Current Deployment

Currently deployed on **PythonAnywhere** at:
- Production: `https://fraugher.pythonanywhere.com`

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
python -m venv venv
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
- `GET /apify/start-run` - Start Apify RUN -> review collection, uses apify_run_inputs.json
- `POST /apify/pop-db` - requires runId Populate database with reviews from Apify RUN
- `GET /apify/start_run_for_types` - Start Apify RUN for a particular type of restaurant, uses apify_run_for_types_inputs.json
- `POST /apify/pop-types` - requires runId Populates database with reviews from run_for_types
- `POST /apify/pop-reviews-only` - requires runId, use in concert with pop=types
- `GET /apify/health` - Health check

### Review Access Endpoints
- `GET /reviews/reviews` - Get all reviews for all restaurants
- `GET /reviews/ratings` - Get all ratings for all restaurants
- `GET /reviews/reviews/<google_maps_id>` - Get specific restaurant reviews
- `GET /reviews/ratings/<google_maps_id>` - Get specific restaurant ratings
- `GET /reviews/search_reviews` - Search reviews with filters
- `GET /reviews/search_ratings` - Search ratings with filters
- `POST /reviews/submit-review` - Submit a Bain user review

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
├── apify_api/            # Apify integration endpoints
├── pa_api/               # Review access endpoints
├── tests/                # Test suite
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
└── .dockerignore        # Docker ignore patterns
```
