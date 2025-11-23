import json

def test_get_all_reviews(client):
    """Test GET /reviews/reviews endpoint."""
    response = client.get('/reviews/reviews?restaurant_type=all')

    assert response.status_code == 200
    data = json.loads(response.data)

    assert data['success'] is True
    assert len(data['data']) == 3  # 3 restaurants
    assert data['data'][0]['place_name'] in ['Test Restaurant 1', 'Test Restaurant 2', 'Test Restaurant 3']


def test_get_all_reviews_with_provider_filter(client):
    """Test GET /reviews/reviews with provider filter."""
    response = client.get('/reviews/reviews?restaurant_type=all&provider=Bain')

    assert response.status_code == 200
    data = json.loads(response.data)

    assert data['success'] is True
    # Should only return restaurants with Bain reviews
    for restaurant in data['data']:
        for review in restaurant['reviews']:
            assert review['provider'] == 'Bain'


def test_get_all_ratings(client):
    """Test GET /reviews/ratings endpoint."""
    response = client.get('/reviews/ratings?restaurant_type=all')

    assert response.status_code == 200
    data = json.loads(response.data)

    assert data['success'] is True
    assert len(data['data']) == 3

    # Check structure
    restaurant = data['data'][0]
    assert 'google_maps_id' in restaurant
    assert 'place_name' in restaurant
    assert 'all_ratings' in restaurant
    assert 'bain_ratings' in restaurant
    assert 'count' in restaurant['all_ratings']
    assert 'average' in restaurant['all_ratings']


def test_get_restaurant_reviews(client):
    """Test GET /reviews/reviews/<google_maps_id> endpoint."""
    response = client.get('/reviews/reviews/place_1')

    assert response.status_code == 200
    data = json.loads(response.data)

    assert data['success'] is True
    assert data['data']['google_maps_id'] == 'place_1'
    assert data['data']['place_name'] == 'Test Restaurant 1'
    assert len(data['data']['reviews']) == 2  # place_1 has 2 reviews


def test_get_restaurant_reviews_with_provider(client):
    """Test GET /reviews/reviews/<google_maps_id> with provider filter."""
    response = client.get('/reviews/reviews/place_1?provider=Bain')

    assert response.status_code == 200
    data = json.loads(response.data)

    assert data['success'] is True
    assert len(data['data']['reviews']) == 1  # Only 1 Bain review
    assert data['data']['reviews'][0]['provider'] == 'Bain'


def test_get_restaurant_reviews_not_found(client):
    """Test GET /reviews/reviews/<google_maps_id> with non-existent ID."""
    response = client.get('/reviews/reviews/nonexistent_id')

    assert response.status_code == 404
    data = json.loads(response.data)

    assert data['success'] is False
    assert 'not found' in data['error'].lower()


def test_get_restaurant_ratings(client):
    """Test GET /reviews/ratings/<google_maps_id> endpoint."""
    response = client.get('/reviews/ratings/place_1')

    assert response.status_code == 200
    data = json.loads(response.data)

    assert data['success'] is True
    assert data['data']['google_maps_id'] == 'place_1'
    assert data['data']['all_ratings']['count'] == 2
    assert data['data']['all_ratings']['average'] == 4.5
    assert data['data']['bain_ratings']['count'] == 1
    assert data['data']['bain_ratings']['average'] == 4.0


def test_get_restaurant_ratings_not_found(client):
    """Test GET /reviews/ratings/<google_maps_id> with non-existent ID."""
    response = client.get('/reviews/ratings/nonexistent_id')

    assert response.status_code == 404
    data = json.loads(response.data)

    assert data['success'] is False
    assert 'not found' in data['error'].lower()


def test_restaurant_with_no_bain_ratings(client):
    """Test restaurant that has overall ratings but no Bain ratings."""
    response = client.get('/reviews/ratings/place_3')

    assert response.status_code == 200
    data = json.loads(response.data)

    assert data['success'] is True
    assert data['data']['all_ratings']['count'] == 1
    assert data['data']['bain_ratings']['count'] == 0
    assert data['data']['bain_ratings']['average'] is None