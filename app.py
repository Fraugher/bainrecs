
from flask import Flask
import yelp_api.endpoints
app = Flask(__name__)

yelp_api.endpoints.register_endpoints(app);

# @app.route('/hello')
# def hello_world():
#     return 'Hello from Flask 2!'

if __name__ == '__main__':
    # For local development only
    # PythonAnywhere will use WSGI
    app.run(debug=True, host='127.0.0.1', port=5000)