import pytest

contact_example = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+380501234567",
    "birthday": "1990-01-01",
    "description": "Test contact"
}


@pytest.mark.asyncio
async def test_create_contact(client, get_token):
    response = client.post(
        "/contacts/",
        json=contact_example,
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == contact_example["email"]
    contact_example["id"] = data["id"]  # для наступних тестів


@pytest.mark.asyncio
async def test_read_contacts(client, get_token):
    response = client.get(
        "/contacts/",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(contact["email"] == contact_example["email"] for contact in data)


@pytest.mark.asyncio
async def test_search_contacts(client, get_token):
    response = client.get(
        f"/contacts/search?email={contact_example['email']}",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["email"] == contact_example["email"]


@pytest.mark.asyncio
async def test_update_contact(client, get_token):
    # Спочатку створюємо контакт
    contact_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com",
        "phone": "+380501112233",
        "birthday": "1995-05-05",
        "description": "Initial"
    }
    response = client.post(
        "/contacts/",
        json=contact_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 201
    contact = response.json()
    contact_id = contact["id"]  # <- тут правильне отримання id

    # Оновлюємо контакт
    updated_data = {
        "first_name": "Updated",
        "last_name": "User",
        "email": "updated@example.com",
        "phone": "+380507777777",
        "birthday": "1995-05-05",
        "description": "Updated"
    }

    response = client.put(
        f"/contacts/{contact_id}",
        json=updated_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200
    updated_contact = response.json()
    assert updated_contact["first_name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_contact(client, get_token):
    # Створюємо контакт
    contact_data = {
        "first_name": "Delete",
        "last_name": "Me",
        "email": "deleteme@example.com",
        "phone": "+380509999999",
        "birthday": "1992-02-02",
        "description": "Delete me"
    }
    response = client.post(
        "/contacts/",
        json=contact_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )
    contact_id = response.json()["id"]  # ← знову беремо id

    # Видаляємо
    response = client.delete(
        f"/contacts/{contact_id}",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200
