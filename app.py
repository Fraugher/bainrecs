from flask_cors import CORS
from dotenv import load_dotenv
import os
from flask import Flask
import config
from extensions import db
from config import DevelopmentConfig, ProductionConfig
from pathlib import Path

project_root = Path(__file__).parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path)

def create_app(config_object=None):
    app = Flask(__name__)
    CORS(app)

    env = config.Environment(os.getenv('FLASK_ENV', 'development'))

    if config_object:
        app.config.from_object(config_object)
    else:
        if env == config.Environment.DEVELOPMENT:
            app.config.from_object(DevelopmentConfig)
        else:
            app.config.from_object(ProductionConfig)

    def create_app(config_object=None):
        app = Flask(__name__)
        CORS(app)

        env = config.Environment(os.getenv('FLASK_ENV', 'development'))

        if config_object:
            app.config.from_object(config_object)
        else:
            if env == config.Environment.DEVELOPMENT:
                app.config.from_object(DevelopmentConfig)
            else:
                app.config.from_object(ProductionConfig)

        # ... rest of setup
        return app
    db.init_app(app)  # Initialize db with your Flask app

    # Blueprints
    from apify_api.apify_endpoints import apify_endpoints
    from pa_api.get_reviews import review_endpoints
    from pa_api.capture_review import capture_review
    from pa_api.deploy_app import deploy_app

    app.register_blueprint(apify_endpoints, url_prefix='/apify')
    app.register_blueprint(review_endpoints, url_prefix='/reviews')
    app.register_blueprint(capture_review, url_prefix='/reviews')
    app.register_blueprint(deploy_app, url_prefix='/')

    print("\n=== Registered Routes ===")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule} {rule.methods}")
    print("========================\n")

    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Operations requiring app context
    app.run(debug=True)