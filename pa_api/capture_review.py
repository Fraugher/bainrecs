from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError
from extensions import db
from models import Review

capture_review = Blueprint('capture_review', __name__)

@capture_review.route('/submit-review', methods=['POST'])
def submit_review():
    try:
        print("=== SUBMIT REVIEW CALLED ===")
        print(f"Form data: {request.form}")
        google_maps_id = request.form.get('google_maps_id', '').strip()
        print(f"google_maps_id: {google_maps_id}")
        place_name = request.form.get('place_name', '').strip()
        print(f"place_name: {place_name}")
        review_title = request.form.get('review_title', '').strip()
        print(f"review_title: {review_title}")
        review_text = request.form.get('review_text', '').strip()
        print(f"review_text: {review_text}")
        review_rating = request.form.get('review_rating', '').strip()
        print(f"review_rating: {review_rating}")
        author_name = request.form.get('author_name', '').strip()
        print(f"author_name: {author_name}")

        # Validation
        errors = []

        # Validate google_maps_id (required)
        if not google_maps_id:
            errors.append("google_maps_id is required")
        elif len(google_maps_id) > 128:
            errors.append("google_maps_id must be 128 characters or less")

        # Validate review_rating (required for Bain reviews)
        rating_value = None
        if not review_rating:
            errors.append("review_rating is required")
        else:
            try:
                rating_value = int(review_rating)
                if rating_value < 1 or rating_value > 5:
                    errors.append("review_rating must be between 1 and 5")
            except ValueError:
                errors.append("review_rating must be a valid integer")

        if review_title and len(review_title) > 255:
            errors.append("review_title must be 255 characters or less")

        if author_name and len(author_name) > 128:
            errors.append("author_name must be 128 characters or less")

        if errors:
            return jsonify({
                'success': False,
                'errors': errors
            }), 400

        new_review = Review(
            google_maps_id=google_maps_id,
            provider='Bain',
            place_name=place_name,
            review_title=review_title if review_title else None,
            review_text=review_text if review_text else None,
            review_rating=rating_value,
            author_name=author_name if author_name else None
        )
        db.session.add(new_review)
        db.session.commit()

        try:
            # run stored procedure to aggregate this new rating with others
            db.session.execute(db.text(current_app.config['DB_PROCEDURE_BAIN_RATING']))
            db.session.commit()
        except Exception as proc_error:
            # Log the error but don't fail the request since review was saved
            print(f"Warning: Failed to update bain_ratings: {proc_error}")

        return jsonify({
            'success': True,
            'message': 'Review submitted successfully',
            'review_id': new_review.id
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'details': str(e)
        }), 500

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500