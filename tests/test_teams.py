from unittest.mock import ANY

from tests.factories import TeamFactory


def test_create_team(client, faker):
    """Test creating a team."""

    parent_team = TeamFactory()

    # Missing json data
    payload = {}

    ret = client.post('/teams', json=payload)
    assert ret.status_code == 400
    assert ret.json == {
        'name': ['Missing data for required field.'],
    }

    # valid
    payload = {"name": faker.pystr(), "parent_team_id": parent_team.id}

    ret = client.post('/teams', json=payload)
    assert ret.status_code == 201
    assert ret.json == {'experiments': [], 'id': ANY, 'name': payload['name']}

    # Cannot create team with the same name
    ret = client.post('/teams', json=payload)
    assert ret.status_code == 400
    assert ret.json == 'Team already exists'
