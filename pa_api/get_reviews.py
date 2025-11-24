from flask import Blueprint, request, jsonify
from sqlalchemy import text
from extensions import db

# Create the blueprint
review_endpoints= Blueprint('get_reviews', __name__)

def load_query(filename):
    with open(f'queries/{filename}', 'r') as f:
        return f.read()

# 1. get all restaurants with their reviews
@review_endpoints.route('/reviews', methods=['GET'])
@review_endpoints.route('/reviews', methods=['GET'])
def get_all_reviews():
    try:
        restaurant_type = request.args.get('restaurant_type', 'all')
        provider = request.args.get('provider', None)

        query = """
                SELECT r.google_maps_id, 
                       r.place_name, 
                       r.place_address, 
                       rev.id, 
                       rev.review_title, 
                       rev.review_text, 
                       rev.review_date, 
                       rev.review_rating, 
                       rev.author_name, 
                       rev.provider
                FROM restaurants r
                         LEFT JOIN reviews rev ON r.google_maps_id = rev.google_maps_id
                """

        params = {}
        where_clauses = []

        # Add restaurant_type filter if not 'all'
        if restaurant_type != 'all':
            where_clauses.append("r.restaurant_type = :restaurant_type")
            params['restaurant_type'] = restaurant_type

        # Add provider filter if specified
        if provider:
            where_clauses.append("rev.provider = :provider")
            params['provider'] = provider

        # Build WHERE clause if we have any conditions
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY r.place_name, rev.review_date DESC"

        result = db.session.execute(text(query), params)
        rows = result.fetchall()

        restaurants = {}
        for row in rows:
            google_maps_id = row[0]
            if google_maps_id not in restaurants:
                restaurants[google_maps_id] = {
                    'google_maps_id': row[0],
                    'place_name': row[1],
                    'place_address': row[2],
                    'reviews': []
                }

            if row[3]:  # review id
                restaurants[google_maps_id]['reviews'].append({
                    'id': row[3],
                    'review_title': row[4],
                    'review_text': row[5],
                    'review_date': row[6].isoformat() if row[6] else None,
                    'review_rating': row[7],
                    'author_name': row[8],
                    'provider': row[9]
                })

        return jsonify({
            'success': True,
            'data': list(restaurants.values())
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 2. GET all restaurants with their ratings (including Bain ratings)
@review_endpoints.route('/ratings', methods=['GET'])
def get_all_ratings():
    try:
        restaurant_type = request.args.get('restaurant_type', 'all')

        query = """
                SELECT DISTINCT r.google_maps_id,
                                MAX(r.place_name)    as place_name,
                                MAX(r.place_address) as place_address,
                                rat.ratings_count,
                                rat.ratings_avg,
                                brat.ratings_count   as bain_ratings_count,
                                brat.ratings_avg     as bain_ratings_avg
                FROM restaurants r
                         LEFT JOIN ratings rat ON r.google_maps_id = rat.google_maps_id
                         LEFT JOIN bain_ratings brat ON r.google_maps_id = brat.google_maps_id \
                """

        params = {}

        # Only add WHERE clause if not 'all'
        if restaurant_type != 'all':
            query += " WHERE r.restaurant_type = :restaurant_type"
            params['restaurant_type'] = restaurant_type

        query += """
                    GROUP BY r.google_maps_id, rat.ratings_count, rat.ratings_avg, 
                             brat.ratings_count, brat.ratings_avg
                    ORDER BY place_name
                    """

        result = db.session.execute(text(query), params)
        rows = result.fetchall()

        restaurants = []
        for row in rows:
            restaurants.append({
                'google_maps_id': row[0],
                'place_name': row[1],
                'place_address': row[2],
                'all_ratings': {
                    'count': row[3] if row[3] else 0,
                    'average': float(row[4]) if row[4] else None
                },
                'bain_ratings': {
                    'count': row[5] if row[5] else 0,
                    'average': float(row[6]) if row[6] else None
                }
            })

        return jsonify({
            'success': True,
            'data': restaurants
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# 3. GET one restaurant with its reviews
@review_endpoints.route('/reviews/<google_maps_id>', methods=['GET'])
def get_restaurant_reviews(google_maps_id):
    try:
        provider = request.args.get('provider', None)

        # Build query
        query = """
                SELECT r.google_maps_id, \
                       r.place_name, \
                       r.place_address, \
                       rev.id, \
                       rev.review_title, \
                       rev.review_text, \
                       rev.review_date, \
                       rev.review_rating, \
                       rev.author_name, \
                       rev.provider
                FROM restaurants r
                         LEFT JOIN reviews rev ON r.google_maps_id = rev.google_maps_id
                WHERE r.google_maps_id = :google_maps_id \
                """

        params = {'google_maps_id': google_maps_id}

        # Add provider filter if specified
        if provider:
            query += " AND rev.provider = :provider"
            params['provider'] = provider

        query += " ORDER BY rev.review_date DESC"

        result = db.session.execute(text(query), params)
        rows = result.fetchall()

        if not rows:
            return jsonify({
                'success': False,
                'error': 'Restaurant not found'
            }), 404

        # Build response
        restaurant = {
            'google_maps_id': rows[0][0],
            'place_name': rows[0][1],
            'place_address': rows[0][2],
            'reviews': []
        }

        for row in rows:
            if row[3]:  # review id exists
                restaurant['reviews'].append({
                    'id': row[3],
                    'review_title': row[4],
                    'review_text': row[5],
                    'review_date': row[6].isoformat() if row[6] else None,
                    'review_rating': row[7],
                    'author_name': row[8],
                    'provider': row[9]
                })

        return jsonify({
            'success': True,
            'data': restaurant
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 4. GET one restaurant with its ratings (including Bain ratings)
@review_endpoints.route('/ratings/<google_maps_id>', methods=['GET'])
def get_restaurant_ratings(google_maps_id):
    try:
        query = """
                SELECT r.google_maps_id, \
                       r.place_name, \
                       r.place_address, \
                       rat.ratings_count, \
                       rat.ratings_avg, \
                       brat.ratings_count as bain_ratings_count, \
                       brat.ratings_avg   as bain_ratings_avg
                FROM restaurants r
                         LEFT JOIN ratings rat ON r.google_maps_id = rat.google_maps_id
                         LEFT JOIN bain_ratings brat ON r.google_maps_id = brat.google_maps_id
                WHERE r.google_maps_id = :google_maps_id \
                """

        result = db.session.execute(text(query), {'google_maps_id': google_maps_id})
        row = result.fetchone()

        if not row:
            return jsonify({
                'success': False,
                'error': 'Restaurant not found'
            }), 404

        restaurant = {
            'google_maps_id': row[0],
            'place_name': row[1],
            'place_address': row[2],
            'all_ratings': {
                'count': row[3] if row[3] else 0,
                'average': float(row[4]) if row[4] else None
            },
            'bain_ratings': {
                'count': row[5] if row[5] else 0,
                'average': float(row[6]) if row[6] else None
            }
        }

        return jsonify({
            'success': True,
            'data': restaurant
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 5. Search restaurants and reviews by place_name keyword
@review_endpoints.route('/search_reviews', methods=['GET'])
def search_reviews():
    try:
        keyword = request.args.get('keyword', '').strip()
        restaurant_type = request.args.get('restaurant_type', 'all')
        provider = request.args.get('provider', None)

        if not keyword:
            return jsonify({
                'success': False,
                'error': 'keyword parameter is required'
            }), 400

        # Build query with LIKE for partial matching
        query = """
                SELECT r.google_maps_id, \
                       r.place_name, \
                       r.place_address, \
                       rev.id, \
                       rev.review_title, \
                       rev.review_text, \
                       rev.review_date, \
                       rev.review_rating, \
                       rev.author_name, \
                       rev.provider
                FROM restaurants r
                         LEFT JOIN reviews rev ON r.google_maps_id = rev.google_maps_id
                WHERE r.restaurant_type = :restaurant_type
                  AND r.place_name LIKE :keyword
                """

        params = {
            'restaurant_type': restaurant_type,
            'keyword': f'%{keyword}%'  # Add wildcards for partial matching
        }

        if provider:
            query += " AND rev.provider = :provider"
            params['provider'] = provider

        query += " ORDER BY r.place_name, rev.review_date DESC"
        print("QUERY REVIEWS: " + query)
        result = db.session.execute(text(query), params)
        rows = result.fetchall()

        # Group reviews by restaurant
        restaurants = {}
        for row in rows:
            google_maps_id = row[0]
            if google_maps_id not in restaurants:
                restaurants[google_maps_id] = {
                    'google_maps_id': row[0],
                    'place_name': row[1],
                    'place_address': row[2],
                    'reviews': []
                }

            # Add review if it exists
            if row[3]:  # review id
                restaurants[google_maps_id]['reviews'].append({
                    'id': row[3],
                    'review_title': row[4],
                    'review_text': row[5],
                    'review_date': row[6].isoformat() if row[6] else None,
                    'review_rating': row[7],
                    'author_name': row[8],
                    'provider': row[9]
                })

        return jsonify({
            'success': True,
            'count': len(restaurants),
            'data': list(restaurants.values())
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 6. Search restaurants and ratings by place_name keyword
@review_endpoints.route('/search_ratings', methods=['GET'])
def search_ratings():
    try:
        keyword = request.args.get('keyword', '').strip()
        restaurant_type = request.args.get('restaurant_type', 'all')

        if not keyword:
            return jsonify({
                'success': False,
                'error': 'keyword parameter is required'
            }), 400

        query = """
                SELECT r.google_maps_id, \
                       r.place_name, \
                       r.place_address, \
                       rat.ratings_count, \
                       rat.ratings_avg, \
                       brat.ratings_count as bain_ratings_count, \
                       brat.ratings_avg   as bain_ratings_avg
                FROM restaurants r
                         LEFT JOIN ratings rat ON r.google_maps_id = rat.google_maps_id
                         LEFT JOIN bain_ratings brat ON r.google_maps_id = brat.google_maps_id
                WHERE r.restaurant_type = :restaurant_type
                  AND r.place_name LIKE :keyword
                ORDER BY r.place_name
                """

        params = {
            'restaurant_type': restaurant_type,
            'keyword': f'%{keyword}%'  # Add wildcards for partial matching
        }

        print("QUERY RATINGS: " + query)
        result = db.session.execute(text(query), params)
        rows = result.fetchall()

        restaurants = []
        for row in rows:
            restaurants.append({
                'google_maps_id': row[0],
                'place_name': row[1],
                'place_address': row[2],
                'all_ratings': {
                    'count': row[3] if row[3] else 0,
                    'average': float(row[4]) if row[4] else None
                },
                'bain_ratings': {
                    'count': row[5] if row[5] else 0,
                    'average': float(row[6]) if row[6] else None
                }
            })

        return jsonify({
            'success': True,
            'count': len(restaurants),
            'data': restaurants
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
