
from flask import Flask
# import yelp_api.endpoints
import yelp_api.simplestart as simplestart

app = Flask(__name__)

# yelp_api.endpoints.register_endpoints(app)
simplestart.start(app)

# @app.route('/hello')
# def hello_world():
#     return 'Hello from Flask 2!'

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=6000)