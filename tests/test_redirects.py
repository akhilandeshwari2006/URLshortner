def test_redirect_returns_location_for_created_link(client):
    long_url = "https://example.com/somewhere"
    headers = {"X-API-Key": "dev-key-a"}

    create_response = client.post(
        "/links",
        json={"long_url": long_url},
        headers=headers,
    )

    assert create_response.status_code == 201

    code = create_response.json()["code"]

    redirect_response = client.get(
        f"/r/{code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 302
    assert redirect_response.headers["location"] == long_url