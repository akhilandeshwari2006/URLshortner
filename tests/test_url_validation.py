def test_rejects_encoded_url_bypass(client):
    headers = {"X-API-Key": "dev-key-a"}

    response = client.post(
        "/links",
        json={"long_url": "http%3A%2F%2Fevil.example.com"},
        headers=headers,
    )

    assert response.status_code == 400