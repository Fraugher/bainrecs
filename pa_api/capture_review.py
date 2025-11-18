from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from extensions import db

capture_review = Blueprint('capture_review', __name__)

class ReviewDetails(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    google_maps_id = db.Column(db.String(128), nullable=False)
    provider = db.Column(db.String(100), nullable=True)
    review_title = db.Column(db.String(255), nullable=True)
    review_text = db.Column(db.Text, nullable=True)
    review_rating = db.Column(db.SmallInteger, nullable=True)
    author_name = db.Column(db.String(128), nullable=True)


@capture_review.route('/submit-review', methods=['POST'])
def submit_review():
    try:
        # Extract data from form
        google_maps_id = request.form.get('google_maps_id', '').strip()
        review_title = request.form.get('review_title', '').strip()
        review_text = request.form.get('review_text', '').strip()
        review_rating = request.form.get('review_rating', '').strip()
        author_name = request.form.get('author_name', '').strip()

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

        # Validate review_title length
        if review_title and len(review_title) > 255:
            errors.append("review_title must be 255 characters or less")

        # Validate author_name length
        if author_name and len(author_name) > 128:
            errors.append("author_name must be 128 characters or less")

        # If there are validation errors, return them
        if errors:
            return jsonify({
                'success': False,
                'errors': errors
            }), 400

        # Create new review record
        new_review = ReviewDetails(
            google_maps_id=google_maps_id,
            provider='Bain',
            review_title=review_title if review_title else None,
            review_text=review_text if review_text else None,
            review_rating=rating_value,
            author_name=author_name if author_name else None
        )

        # Insert into database
        db.session.add(new_review)
        db.session.commit()

        # Call stored procedure to update bain_ratings
        try:
            db.session.execute(db.text("CALL makebainratings()"))
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
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500