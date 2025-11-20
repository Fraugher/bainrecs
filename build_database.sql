-- ============================================
-- Toronto Restaurants Database Build Script
-- ============================================
-- This script will create the database from scratch
--
-- Usage on PythonAnywhere:
--   mysql -h fraugher.mysql.pythonanywhere-services.com -u fraugher -p < build_database.sql
--
-- Or from MySQL console:
--   source /home/fraugher/build_database.sql
-- ============================================

-- Use the database
-- Note: On PythonAnywhere, database is named: fraugher$toronto_restaurants
-- USE fraugher$toronto_restaurants;

-- ============================================
-- DROP EXISTING OBJECTS (in correct order)
-- ============================================

-- Drop procedures first
DROP PROCEDURE IF EXISTS cleardb;
DROP PROCEDURE IF EXISTS makebainratings;
DROP PROCEDURE IF EXISTS makeratings;
DROP PROCEDURE IF EXISTS makerestaurants;

-- Drop tables created by procedures
DROP TABLE IF EXISTS bain_ratings;
DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS restaurants;
DROP TABLE IF EXISTS reviews_bup;
DROP TABLE IF EXISTS reviews_bain;

-- Drop main table last
DROP TABLE IF EXISTS reviews;

-- ============================================
-- CREATE MAIN TABLE
-- ============================================

CREATE TABLE `reviews` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `google_maps_id` VARCHAR(128) DEFAULT NULL,
  `date_updated` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `place_name` VARCHAR(255) NOT NULL,
  `place_url` VARCHAR(255) DEFAULT NULL,
  `place_address` VARCHAR(255) DEFAULT NULL,
  `provider` VARCHAR(100) DEFAULT NULL,
  `review_title` VARCHAR(255) DEFAULT NULL,
  `review_text` TEXT,
  `review_date` DATETIME DEFAULT NULL,
  `review_rating` TINYINT DEFAULT NULL,
  `author_name` VARCHAR(100) DEFAULT NULL,
  `ignore_for_quality` TINYINT(1) DEFAULT NULL,
  `ignore_for_rating` TINYINT(1) DEFAULT NULL,
  `ignore_for_insufficient` TINYINT(1) DEFAULT NULL,
  `selected_as_top_rating` TINYINT(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX idx_google_maps_id (`google_maps_id`),
  INDEX idx_provider (`provider`),
  INDEX idx_rating (`review_rating`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- ============================================
-- CREATE STORED PROCEDURES
-- ============================================

DELIMITER //

-- Procedure to create restaurants table from reviews
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

-- Procedure to create ratings table from all reviews
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

-- Procedure to create Bain-specific ratings table
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

-- Procedure to clear database (keeps only Bain reviews)
CREATE PROCEDURE cleardb()
BEGIN
    DROP TABLE IF EXISTS reviews_bup;
    CREATE TABLE reviews_bup AS SELECT * FROM reviews;
    DROP TABLE IF EXISTS ratings;
    DROP TABLE IF EXISTS restaurants;
    DELETE FROM reviews WHERE provider != 'Bain';
END //

DELIMITER ;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- Uncomment these to verify the build

-- SHOW TABLES;
-- SELECT COUNT(*) AS review_count FROM reviews;
-- CALL makerestaurants();
-- CALL makeratings();
-- CALL makebainratings();
-- SELECT COUNT(*) FROM restaurants;
-- SELECT COUNT(*) FROM ratings;
-- SELECT COUNT(*) FROM bain_ratings;

-- ============================================
-- END OF BUILD SCRIPT
-- ============================================