import pytest
from app import create_app
from extensions import db
import os


@pytest.fixture(scope='function')
def app():
    """Create and configure a test app instance."""
    # Create a temporary test database
    test_db_uri = 'sqlite:///:memory:'  # In-memory SQLite for fast tests

    # Override environment variables for testing
    os.environ['SQL_ALCHEMY_URI'] = test_db_uri

    # Create the app with test config
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = test_db_uri

    # Create tables
    with app.app_context():
        db.create_all()

        # Insert test data
        _insert_test_data()

    yield app

    # Cleanup
    with app.app_context():
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create a test client."""
    return app.test_client()


def _insert_test_data():
    """Insert test data into the database."""
    from sqlalchemy import text

    # Insert test restaurants
    db.session.execute(text("""
                            CREATE TABLE IF NOT EXISTS restaurants
                            (
                                google_maps_id
                                VARCHAR
                            (
                                128
                            ),
                                place_name VARCHAR
                            (
                                255
                            ),
                                place_address VARCHAR
                            (
                                255
                            ),
                                restaurant_type VARCHAR
                            (
                                3
                            )
                                )
                            """))

    db.session.execute(text("""
                            INSERT INTO restaurants (google_maps_id, place_name, place_address, restaurant_type)
                            VALUES ('place_1', 'Test Restaurant 1', '123 Main St', 'all'),
                                   ('place_2', 'Test Restaurant 2', '456 Oak Ave', 'all'),
                                   ('place_3', 'Test Restaurant 3', '789 Pine Rd', 'all')
                            """))

    # Insert test reviews
    db.session.execute(text("""
                            CREATE TABLE IF NOT EXISTS reviews
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                google_maps_id
                                VARCHAR
                            (
                                128
                            ),
                                review_title VARCHAR
                            (
                                255
                            ),
                                review_text TEXT,
                                review_date DATETIME,
                                review_rating INTEGER,
                                author_name VARCHAR
                            (
                                100
                            ),
                                provider VARCHAR
                            (
                                100
                            )
                                )
                            """))

    db.session.execute(text("""
                            INSERT INTO reviews (google_maps_id, review_title, review_text, review_date, review_rating,
                                                 author_name, provider)
                            VALUES ('place_1', 'Great food!', 'Amazing experience', '2024-01-01', 5, 'John Doe',
                                    'Google'),
                                   ('place_1', 'Good service', 'Nice staff', '2024-01-02', 4, 'Jane Smith', 'Bain'),
                                   ('place_2', 'Decent', 'It was okay', '2024-01-03', 3, 'Bob Johnson', 'Google'),
                                   ('place_2', 'Excellent', 'Best meal ever', '2024-01-04', 5, 'Alice Brown', 'Bain'),
                                   ('place_3', 'Poor', 'Not recommended', '2024-01-05', 2, 'Charlie Davis', 'Google')
                            """))

    # Insert test ratings
    db.session.execute(text("""
                            CREATE TABLE IF NOT EXISTS ratings
                            (
                                google_maps_id
                                VARCHAR
                            (
                                128
                            ),
                                place_name VARCHAR
                            (
                                255
                            ),
                                ratings_count BIGINT,
                                ratings_avg DECIMAL
                            (
                                7,
                                4
                            )
                                )
                            """))

    db.session.execute(text("""
                            INSERT INTO ratings (google_maps_id, place_name, ratings_count, ratings_avg)
                            VALUES ('place_1', 'Test Restaurant 1', 2, 4.5000),
                                   ('place_2', 'Test Restaurant 2', 2, 4.0000),
                                   ('place_3', 'Test Restaurant 3', 1, 2.0000)
                            """))

    # Insert test bain_ratings
    db.session.execute(text("""
                            CREATE TABLE IF NOT EXISTS bain_ratings
                            (
                                google_maps_id
                                VARCHAR
                            (
                                128
                            ),
                                place_name VARCHAR
                            (
                                255
                            ),
                                ratings_count BIGINT,
                                ratings_avg DECIMAL
                            (
                                7,
                                4
                            )
                                )
                            """))

    db.session.execute(text("""
                            INSERT INTO bain_ratings (google_maps_id, place_name, ratings_count, ratings_avg)
                            VALUES ('place_1', 'Test Restaurant 1', 1, 4.0000),
                                   ('place_2', 'Test Restaurant 2', 1, 5.0000)
                            """))

    db.session.commit()