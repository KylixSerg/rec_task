from unittest.mock import ANY

from tests.factories import ExperimentFactory
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


def test_get_experiments(client):
    """Test experiment listing."""

    e1, e2, e3, e4 = ExperimentFactory.create_batch(4)
    t1, t2, t3 = TeamFactory.create_batch(3)

    e1.teams = [t1, t2]
    e2.teams = [t2, t3]

    # no qs are required
    ret = client.get('/experiments', query_string={})
    assert ret.status_code == 200
    # defaulted to order by id
    assert [exp["id"] for exp in ret.json["data"]] == [e1.id, e2.id, e3.id, e4.id]
    assert ret.json['meta'] == {
        'items': 4,
        'limit': 25,
        'order_by': 'asc',
        'page': 1,
        'sort_by': 'id',
    }

    # custom pagination/sorting
    qs = {"page": 2, "limit": 2, "order_by": "desc"}

    ret = client.get('/experiments', query_string=qs)
    assert ret.status_code == 200
    # descending order / 2nd page for a 2 items per page partition
    assert [exp["id"] for exp in ret.json["data"]] == [e2.id, e1.id]
    assert ret.json['meta'] == {
        'items': 2,
        'limit': 2,
        'order_by': 'desc',
        'page': 2,
        'sort_by': 'id',
    }

    # filter by team_ids
    qs = {"team_ids[]": [t1.id, t2.id]}

    ret = client.get('/experiments', query_string=qs)
    assert ret.status_code == 200
    assert ret.json["data"] == [
        {
            'description': e1.description,
            'id': e1.id,
            'sample_ratio': e1.sample_ratio,
            'teams': [
                {'id': t1.id, 'name': t1.name},
                {'id': t2.id, 'name': t2.name},
            ],
        },
        {
            'description': e2.description,
            'id': e2.id,
            'sample_ratio': e2.sample_ratio,
            'teams': [
                {'id': t2.id, 'name': t2.name},
                {'id': t3.id, 'name': t3.name},
            ],
        },
    ]

    # filter by teams (that have sub-teams)
    parent_team = TeamFactory()
    # make it parent for t1, t2, t3
    t1.parent_team_id = parent_team.id
    t2.parent_team_id = parent_team.id
    t3.parent_team_id = parent_team.id
    # create an experiment linked to the parent
    pe = ExperimentFactory(teams=[parent_team])

    # Fetching experiment for parent team should give us back experiment of t1, t2, t3
    qs = {"team_ids[]": [parent_team.id]}

    ret = client.get('/experiments', query_string=qs)
    assert ret.status_code == 200
    assert ret.json["data"] == [
        # Linked to descendents of that team
        {
            'description': e1.description,
            'id': e1.id,
            'sample_ratio': e1.sample_ratio,
            'teams': [
                {'id': t1.id, 'name': t1.name},
                {'id': t2.id, 'name': t2.name},
            ],
        },
        {
            'description': e2.description,
            'id': e2.id,
            'sample_ratio': e2.sample_ratio,
            'teams': [
                {'id': t2.id, 'name': t2.name},
                {'id': t3.id, 'name': t3.name},
            ],
        },
        # Directly linked to the team
        {
            'description': pe.description,
            'id': pe.id,
            'sample_ratio': pe.sample_ratio,
            'teams': [
                {'id': parent_team.id, 'name': parent_team.name},
            ],
        },
    ]

    # t1, has no descendents - only e1
    qs = {"team_ids[]": [t1.id]}

    ret = client.get('/experiments', query_string=qs)
    assert ret.status_code == 200
    assert ret.json["data"] == [
        # Linked to descendents of that team
        {
            'description': e1.description,
            'id': e1.id,
            'sample_ratio': e1.sample_ratio,
            'teams': [
                {'id': t1.id, 'name': t1.name},
                {'id': t2.id, 'name': t2.name},
            ],
        }
    ]


def test_update_experiment(client):
    """Test update experiment teams."""

    t1, t2 = TeamFactory.create_batch(2)
    e = ExperimentFactory(teams=[t1])

    # At least 1 and max 2 teams can be specified
    payload = {"team_ids": [1, 2, 3]}
    ret = client.put(f'/experiments/{e.id}', json=payload)
    assert ret.status_code == 400
    assert ret.json == {'team_ids': ['Length must be between 1 and 2.']}

    # experiment not found
    payload = {"team_ids": [1, 2]}
    ret = client.put(f'/experiments/{e.id + 1}', json=payload)
    assert ret.status_code == 404
    assert ret.json == 'Experiment not found!'

    # trying to add a new team for a 1 team experiment
    payload = {"team_ids": [1, 2]}
    ret = client.put(f'/experiments/{e.id}', json=payload)
    assert ret.status_code == 400
    assert ret.json == 'Cannot change number of linked teams now'

    # nothing to update(above condition is ignore when duplicate id)
    # trying to add a new team for a 1 team experiment
    payload = {"team_ids": [t1.id, t1.id]}
    ret = client.put(f'/experiments/{e.id}', json=payload)
    assert ret.status_code == 200
    assert ret.json == 'Nothing to update'

    # update with non-existing team
    payload = {"team_ids": [t1.id + 2]}
    ret = client.put(f'/experiments/{e.id}', json=payload)
    assert ret.status_code == 400
    assert ret.json == 'Some/All of the teams specified were not found'

    # update
    payload = {"team_ids": [t2.id]}
    ret = client.put(f'/experiments/{e.id}', json=payload)
    assert ret.status_code == 200
    assert ret.json == {
        'description': e.description,
        'id': e.id,
        'sample_ratio': e.sample_ratio,
        'teams': [{'id': t2.id, 'name': t2.name}],
    }

    # create another experiment with 2 teams
    t2_child, t_ = TeamFactory.create_batch(2)
    t2_child.parent_team_id = t2.id
    e = ExperimentFactory(teams=[t2_child, t_])

    # Cant have both t2 and t2_child assigned to one experiment
    payload = {"team_ids": [t2.id, t2_child.id]}
    ret = client.put(f'/experiments/{e.id}', json=payload)
    assert ret.status_code == 400
    assert ret.json == 'Experiment teams cannot be descendents of one another'



