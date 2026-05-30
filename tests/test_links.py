def test_create_link_returns_code_and_short_url(client):
    headers = {"X-API-Key": "dev-key-a"}

    response = client.post(
        "/links",
        json={"long_url": "https://example.com/create-test"},
        headers=headers,
    )

    assert response.status_code == 201

    body = response.json()
    assert body["code"]
    assert body["short_url"].endswith(f"/r/{body['code']}")