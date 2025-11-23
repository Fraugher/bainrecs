import os
from dotenv import load_dotenv
from enum import Enum
from pathlib import Path

project_root = Path(__file__).parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path)

class Environment(Enum):
    DEVELOPMENT = 'development'
    PRODUCTION = 'production'
    TEST = 'test'

class Config:
    """Base configuration"""
    SQLALCHEMY_DATABASE_URI = os.getenv('SQL_ALCHEMY_URI')
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_recycle': 280}
    APIFY_API_KEY = os.getenv('APIFY_API_KEY')
    APIFY_RESTAURANT_REVIEW_URI = os.getenv('APIFY_RESTAURANT_REVIEW_URI')
    DB_PROCEDURE_BAIN_RATING = os.getenv('DB_PROCEDURE_BAIN_RATING')
    DB_PROCEDURE_CLEAR_DB = os.getenv('DB_PROCEDURE_CLEAR_DB')
    DB_PROCEDURE_MAKE_RATINGS= os.getenv('DB_PROCEDURE_MAKE_RATINGS')
    DB_PROCEDURE_MAKE_RESTAURANTS= os.getenv('DB_PROCEDURE_MAKE_RESTAURANTS')

class DevelopmentConfig(Config):
    DEBUG = True
    FILE_BASE = ''

class ProductionConfig(Config):
    DEBUG = False
    FILE_BASE = os.getenv('FILE_BASE_PRODUCTION')

class TestingConfig(Config):
    TESTING = True
    FILE_BASE = '/tmp/test_files/'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # ✅ In-memory DB
    SQLALCHEMY_TRACK_MODIFICATIONS = False