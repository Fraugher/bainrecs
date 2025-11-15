import requests
import os
from dotenv import load_dotenv

load_dotenv()

PYTHONANYWHERE_API_KEY = os.getenv('PYTHONANYWHERE_API_KEY')
USERNAME = 'fraugher'
DOMAIN = 'fraugher.pythonanywhere.com'

response = requests.delete(
    f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/error_log/',
    headers={'Authorization': f'Token {PYTHONANYWHERE_API_KEY}'}
)

if response.status_code == 204:
    print("Error log cleared successfully!")
else:
    print(f"Failed to clear log: {response.status_code}")
    print(response.text)