from flask_cors import CORS
from dotenv import load_dotenv
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

load_dotenv()
db = SQLAlchemy()
SQL_ALCHEMY_URI = os.getenv('SQL_ALCHEMY_URI')
PYTHONANYWHERE_API_KEY = os.getenv('PYTHONANYWHERE_API_KEY')

def create_app():
  app = Flask(__name__)
  CORS(app)

  app.config["SQLALCHEMY_DATABASE_URI"] = SQL_ALCHEMY_URI
  app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 280}


  db.init_app(app)  # Initialize db with your Flask app

  # Import and register your blueprints here
  from yelp_api.apify_endpoints import apify_endpoints
  from yelp_api.endpoints import yelp_endpoints
  app.register_blueprint(apify_endpoints)
  app.register_blueprint(yelp_endpoints)
  return app

# def application(environ, start_response):
#   if environ['REQUEST_METHOD'] == 'OPTIONS':
#     start_response(
#       '200 OK',
#       [
#         ('Content-Type', 'application/json'),
#         ('Access-Control-Allow-Origin', '*'),
#         ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
#         ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
#       ]
#     )
#     return ''

# @app.before_request
# def require_api_key():
#     api_key = request.headers.get('X-API-KEY')
#     if not api_key or not is_valid_api_key(api_key):
#         abort(401, description="Unauthorized: Invalid or missing API key")
#
# def is_valid_api_key(key):
#     return key == PYTHONANYWHERE_API_KEY # For demonstration, use a real check

# if __name__ == '__main__':
#     app.run(debug=True, host='127.0.0.1', port=5000)
app = create_app()
# # For WSGI (PythonAnywhere uses this)
# application = app

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Operations requiring app context
    app.run(debug=True)