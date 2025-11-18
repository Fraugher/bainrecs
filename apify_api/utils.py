# from flask import Flask, request, jsonify
# import os
#
# from functools import wraps
#
# def api_utils(app: Flask):
#     def require_api_key(f):
#         """Decorator to check if Yelp API key is configured"""
#
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             YELP_API_KEY = os.environ.get('YELP_API_KEY')
#             if not YELP_API_KEY:
#                 return jsonify({
#                     'error': 'Configuration Error',
#                     'message': 'YELP_API_KEY not configured in environment variables.'
#                 }), 500
#             return f(*args, **kwargs)
#
#         return decorated_function
#
#     # CORS support
#     app.after_request
#     def after_request(response):
#         """Add CORS headers to all responses"""
#         response.headers.add('Access-Control-Allow-Origin', '*')
#         response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#         response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
#         return response
#
#     def handle_yelp_error(status_code, response_data):
#         """Handle specific Yelp API error codes with appropriate messages"""
#
#         error_messages = {
#             400: {
#                 'error': 'Bad Request',
#                 'message': 'Invalid request parameters. Please check your query parameters.',
#                 'details': response_data
#             },
#             401: {
#                 'error': 'Unauthorized',
#                 'message': 'The API key has either expired or doesn\'t have the required scope to query this endpoint.',
#                 'details': response_data,
#                 'possible_causes': [
#                     'UNAUTHORIZED_API_KEY: The API key provided is not currently able to query this endpoint.',
#                     'TOKEN_INVALID: Invalid API key or authorization header.'
#                 ]
#             },
#             403: {
#                 'error': 'Forbidden',
#                 'message': 'The API key provided is not currently able to query this endpoint.',
#                 'details': response_data
#             },
#             404: {
#                 'error': 'Resource Not Found',
#                 'message': 'The requested resource was not found. Please check the endpoint URL.',
#                 'details': response_data
#             },
#             413: {
#                 'error': 'Request Entity Too Large',
#                 'message': 'The length of the request exceeded the maximum allowed.',
#                 'details': response_data
#             },
#             429: {
#                 'error': 'Too Many Requests',
#                 'message': 'You have either exceeded your daily quota, or have exceeded the queries-per-second limit for this endpoint. Try reducing the rate at which you make queries.',
#                 'details': response_data
#             },
#             500: {
#                 'error': 'Internal Server Error',
#                 'message': 'Yelp API is experiencing internal server errors. Please try again later.',
#                 'details': response_data
#             },
#             503: {
#                 'error': 'Service Unavailable',
#                 'message': 'Yelp API service is temporarily unavailable. Please try again later.',
#                 'details': response_data
#             }
#         }
#
#         return error_messages.get(status_code, {
#             'error': f'Yelp API Error ({status_code})',
#             'message': 'An unexpected error occurred with the Yelp API.',
#             'details': response_data
#         })