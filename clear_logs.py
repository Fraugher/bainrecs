import requests
import os
from dotenv import load_dotenv
from pathlib import Path

project_root = Path(__file__).parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path)

PYTHONANYWHERE_API_KEY = os.getenv('PYTHONANYWHERE_API_KEY')
USERNAME = os.getenv('PYTHONANYWHERE_USERNAME')
DOMAIN = os.getenv('PYTHONANYWHERE_DOMAIN')

response = requests.delete(
    f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/error_log/',
    headers={'Authorization': f'Token {PYTHONANYWHERE_API_KEY}'}
)

if response.status_code == 204:
    print("Error log cleared successfully!")
else:
    print(f"Failed to clear log: {response.status_code}")
    print(response.text)