from flask_cors import CORS
from dotenv import load_dotenv
import os
from flask import Flask
from extensions import db

load_dotenv()
SQL_ALCHEMY_URI = os.getenv('SQL_ALCHEMY_URI')
PYTHONANYWHERE_API_KEY = os.getenv('PYTHONANYWHERE_API_KEY')

def create_app():
    app = Flask(__name__)
    CORS(app)


    app.config["SQLALCHEMY_DATABASE_URI"] = SQL_ALCHEMY_URI
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 280}


    db.init_app(app)  # Initialize db with your Flask app

    # Import and register your blueprints here
    from apify_api.apify_endpoints import apify_endpoints
    # from apify_api.endpoints import yelp_endpoints
    from pa_api.get_reviews import review_endpoints

    app.register_blueprint(apify_endpoints)
    app.register_blueprint(review_endpoints)
    # app.register_blueprint(yelp_endpoints)
    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Operations requiring app context
    app.run(debug=True)