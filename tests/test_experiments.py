from unittest.mock import ANY

from tests.factories import TeamFactory


def test_create_experiment(client, faker):
    """Test creating an experiment."""

    # Missing json data
    payload = {}

    ret = client.post('/experiments', json=payload)
    assert ret.status_code == 400
    assert ret.json == {
        'description': ['Missing data for required field.'],
        'sample_ratio': ['Missing data for required field.'],
        'team_ids': ['Missing data for required field.'],
    }

    # team ids longer than allowed
    payload = {
        "description": faker.pystr(),
        "sample_ratio": faker.pyint(min_value=0, max_value=100),
        "team_ids": [2, 3, 4],
    }

    ret = client.post('/experiments', json=payload)
    assert ret.status_code == 400
    assert ret.json == {'team_ids': ['Length must be between 1 and 2.']}

    # Team(s) not in DB
    payload = {
        "description": faker.pystr(),
        "sample_ratio": faker.pyint(min_value=0, max_value=100),
        "team_ids": [2],
    }

    ret = client.post('/experiments', json=payload)
    assert ret.status_code == 400
    assert ret.json == 'Some/All of the teams specified were not found'

    # valid
    team = TeamFactory()

    payload = {
        "description": faker.pystr(),
        "sample_ratio": faker.pyint(min_value=0, max_value=100),
        "team_ids": [team.id],
    }

    ret = client.post('/experiments', json=payload)
    assert ret.status_code == 201
    assert ret.json == {
        'description': payload['description'],
        'id': ANY,
        'sample_ratio': payload['sample_ratio'],
        'teams': [{'id': team.id, 'name': team.name}],
    }
