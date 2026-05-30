def test_user_b_cannot_read_user_a_link(client):
    long_url = "https://example.com/private"
    user_a_headers = {"X-API-Key": "dev-key-a"}
    user_b_headers = {"X-API-Key": "dev-key-b"}

    create_response = client.post(
        "/links",
        json={"long_url": long_url},
        headers=user_a_headers,
    )
    assert create_response.status_code == 201

    link_id = create_response.json()["id"]

    read_response = client.get(
        f"/links/{link_id}",
        headers=user_b_headers,
    )

    assert read_response.status_code in (403, 404)
    assert long_url not in read_response.text