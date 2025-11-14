from flask import Flask
from yelp_api.endpoints import yelp_endpoints
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.register_blueprint(yelp_endpoints)

@app.route('/hello')
def hello_world():
    return 'Hello from App!'

def application(environ, start_response):
  if environ['REQUEST_METHOD'] == 'OPTIONS':
    start_response(
      '200 OK',
      [
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
      ]
    )
    return ''

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)