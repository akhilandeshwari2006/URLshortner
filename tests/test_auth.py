def test_protected_route_requires_api_key(client):
    response = client.post(
        "/links",
        json={"long_url": "https://example.com"},
    )

    assert response.status_code == 401