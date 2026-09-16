def register_user(
    client,
    username,
    password="password123",
):
    return client.post(
        "/register",
        json={
            "username": username,
            "password": password,
        },
    )


def login_user(
    client,
    username,
    password="password123",
):
    response = client.post(
        "/login",
        json={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.get_json()["access_token"]


def auth(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok"
    }


def test_register_and_login(client):
    response = register_user(
        client,
        "alice",
    )

    assert response.status_code == 201

    response = client.post(
        "/login",
        json={
            "username": "alice",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert "access_token" in payload
    assert "refresh_token" in payload


def test_user_delete_requires_authentication(client):
    register_user(
        client,
        "alice",
    )

    response = client.delete("/user/1")

    assert response.status_code == 401


def test_user_cannot_delete_another_user(client):
    register_user(
        client,
        "alice",
    )

    register_user(
        client,
        "bob",
    )

    token = login_user(
        client,
        "alice",
    )

    response = client.delete(
        "/user/2",
        headers=auth(token),
    )

    assert response.status_code == 403


def test_item_put_requires_authentication(client):
    response = client.put(
        "/item/1",
        json={
            "price": 20,
        },
    )

    assert response.status_code == 401


def test_partial_item_update(client):
    register_user(
        client,
        "alice",
    )

    token = login_user(
        client,
        "alice",
    )

    store_response = client.post(
        "/store",
        headers=auth(token),
        json={
            "name": "Store One",
        },
    )

    assert store_response.status_code == 201

    store_id = store_response.get_json()["id"]

    item_response = client.post(
        "/item",
        headers=auth(token),
        json={
            "name": "Coffee",
            "description": "Fresh coffee",
            "price": 5.0,
            "store_id": store_id,
        },
    )

    assert item_response.status_code == 201

    item_id = item_response.get_json()["id"]

    response = client.put(
        f"/item/{item_id}",
        headers=auth(token),
        json={
            "price": 6.5,
        },
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["name"] == "Coffee"
    assert payload["price"] == 6.5
    assert payload["description"] == "Fresh coffee"


def test_tag_cannot_cross_store_boundary(client):
    register_user(
        client,
        "alice",
    )

    token = login_user(
        client,
        "alice",
    )

    store_one = client.post(
        "/store",
        headers=auth(token),
        json={
            "name": "Store One",
        },
    ).get_json()

    store_two = client.post(
        "/store",
        headers=auth(token),
        json={
            "name": "Store Two",
        },
    ).get_json()

    item = client.post(
        "/item",
        headers=auth(token),
        json={
            "name": "Coffee",
            "price": 5,
            "store_id": store_one["id"],
        },
    ).get_json()

    tag = client.post(
        f"/store/{store_two['id']}/tag",
        headers=auth(token),
        json={
            "name": "Sale",
        },
    ).get_json()

    response = client.post(
        f"/item/{item['id']}/tag/{tag['id']}",
        headers=auth(token),
    )

    assert response.status_code == 400


def test_duplicate_tag_link_returns_conflict(client):
    register_user(
        client,
        "alice",
    )

    token = login_user(
        client,
        "alice",
    )

    store = client.post(
        "/store",
        headers=auth(token),
        json={
            "name": "Store One",
        },
    ).get_json()

    item = client.post(
        "/item",
        headers=auth(token),
        json={
            "name": "Coffee",
            "price": 5,
            "store_id": store["id"],
        },
    ).get_json()

    tag = client.post(
        f"/store/{store['id']}/tag",
        headers=auth(token),
        json={
            "name": "Popular",
        },
    ).get_json()

    first_response = client.post(
        f"/item/{item['id']}/tag/{tag['id']}",
        headers=auth(token),
    )

    assert first_response.status_code == 200

    second_response = client.post(
        f"/item/{item['id']}/tag/{tag['id']}",
        headers=auth(token),
    )

    assert second_response.status_code == 409