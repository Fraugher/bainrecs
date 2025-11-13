# from app import app
from flask import Flask

def start(app: Flask):
    app.route('/hello')
    def hello_world():
        return 'Hello from Flasksimple!'