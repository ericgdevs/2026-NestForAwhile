from app.auth import Role


def test_shared_fixtures_seed_data_and_create_role_session(logged_in_client, database):
    client = logged_in_client(Role.CLIENT)

    assert client.user.role == Role.CLIENT.value
    assert client.cookies["session"] == client.token
    assert database.query(type(client.user)).count() >= 5
