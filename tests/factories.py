import factory

from db.db_models import Experiment
from db.db_models import Team


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session_persistence = 'flush'


class ExperimentFactory(BaseFactory):
    class Meta:
        model = Experiment

    description = factory.Faker('paragraph')
    sample_ratio = factory.Faker('pyint', min_value=0, max_value=100)


class TeamFactory(BaseFactory):
    class Meta:
        model = Team

    name = factory.Faker('pystr')
