from factories import ExperimentFactory, TeamFactory


def test_experiment_team_relationship():
    """Test experiment <-> team, many to many works as expected."""

    t1, t2, t3 = TeamFactory.create_batch(3)
    e1, e2 = ExperimentFactory.create_batch(2)

    e1.teams.extend([t1, t2])
    e2.teams.extend([t2, t3])

    assert len(t1.experiments) == 1
    assert len(t2.experiments) == 2
    assert len(t3.experiments) == 1


