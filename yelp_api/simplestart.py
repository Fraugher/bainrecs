# from app import app
from flask import Flask,Blueprint, render_template

start_blueprint = Blueprint('start_blueprint', __name__,template_folder='templates',static_folder='static'    )
@start_blueprint.route('/hello')
def hello():
    return 'Hello from Flasksimple!'

@start_blueprint.route('/hello3')
def hello3():
    return 'Hello from Flasksimple3!'