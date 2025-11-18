DELIMITER //

CREATE PROCEDURE makeratings()
BEGIN
    DROP TABLE IF EXISTS ratings;
    CREATE TABLE ratings AS
        SELECT
            reviews.google_maps_id,
            MAX(reviews.place_name) AS place_name,
            COUNT(reviews.review_rating) AS ratings_count,
            AVG(reviews.review_rating) AS ratings_avg
        FROM reviews
        WHERE reviews.review_rating IS NOT NULL
        GROUP BY reviews.google_maps_id;
END //

DELIMITER;


DELIMITER //

CREATE PROCEDURE makerestaurants()
BEGIN
    DROP TABLE IF EXISTS restaurants;

    CREATE TABLE restaurants AS
    SELECT
        reviews.google_maps_id AS google_maps_id,
        MAX(reviews.place_name) AS place_name,
        MAX(reviews.place_address) AS place_address,
        'all' AS restaurant_type
    FROM reviews
    GROUP BY reviews.google_maps_id
    ORDER BY MAX(reviews.place_name);
END //

DELIMITER ;


CREATE VIEW reviews_details AS
SELECT
    reviews.google_maps_id,
    reviews.provider,
    reviews.review_title,
    reviews.review_text,
    reviews.review_date,
    reviews.review_rating
FROM reviews;

CREATE VIEW reviews_bain AS
SELECT
    reviews.google_maps_id,
    reviews.provider,
    reviews.review_title,
    reviews.review_text,
    reviews.review_date,
    reviews.review_rating
FROM reviews
WHERE provider="Bain";
DELIMITER;

CREATE PROCEDURE makebainratings()
BEGIN
    DROP TABLE IF EXISTS bain_ratings;
    CREATE TABLE bain_ratings AS
        SELECT
            reviews.google_maps_id,
            MAX(reviews.place_name) AS place_name,
            COUNT(reviews.review_rating) AS ratings_count,
            AVG(reviews.review_rating) AS ratings_avg
        FROM reviews
        WHERE reviews.review_rating IS NOT NULL
          AND reviews.provider = 'Bain'
        GROUP BY reviews.google_maps_id;
END //