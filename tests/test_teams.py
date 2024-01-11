from unittest.mock import ANY


def test_create_team(client, faker):
    """Test creating a team."""

    # Missing json data
    payload = {}

    ret = client.post('/teams', json=payload)
    assert ret.status_code == 400
    assert ret.json == {
        'name': ['Missing data for required field.'],
    }

    # valid
    payload = {
        "name": faker.pystr(),
    }

    ret = client.post('/teams', json=payload)
    assert ret.status_code == 201
    assert ret.json == {'experiments': [], 'id': ANY, 'name': payload['name']}

    # Cannot create team with the same name
    ret = client.post('/teams', json=payload)
    assert ret.status_code == 400
    assert ret.json == 'Team already exists'
