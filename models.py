from extensions import db
from datetime import datetime, timezone

class Review(db.Model):
    __tablename__ = 'reviews'
    __table_args__ = {'extend_existing': True}  # Add this

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    google_maps_id = db.Column(db.String(128))
    date_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                             onupdate=lambda: datetime.now(timezone.utc))
    place_name = db.Column(db.String(255), nullable=False)
    place_url = db.Column(db.String(255))
    place_address = db.Column(db.String(255))
    provider = db.Column(db.String(100))
    review_title = db.Column(db.String(255))
    review_text = db.Column(db.Text)
    review_date = db.Column(db.DateTime)
    review_rating = db.Column(db.SmallInteger)  # TINYINT maps to SmallInteger
    author_name = db.Column(db.String(100))
    ignore_for_quality = db.Column(db.Boolean)
    ignore_for_rating = db.Column(db.Boolean)
    ignore_for_insufficient = db.Column(db.Boolean)
    selected_as_top_rating = db.Column(db.Boolean)

    def __repr__(self):
        return f'<Review {self.id}: {self.place_name} - {self.review_rating}/5>'

class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    __table_args__ = {'extend_existing': True}

    google_maps_id = db.Column(db.String(128), primary_key=True)
    place_name = db.Column(db.String(255), nullable=False)
    place_address = db.Column(db.String(255))
    restaurant_type = db.Column(db.String(50), primary_key=True)

    def __repr__(self):
        return f'<Restaurant {self.google_maps_id} {self.restaurant_type}:: {self.place_name} ({self.place_address})>'