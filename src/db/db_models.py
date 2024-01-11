import datetime

from sqlalchemy import TIMESTAMP
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Table
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import Session
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL


class Base(DeclarativeBase):
    type_annotation_map = {
        datetime.datetime: TIMESTAMP(timezone=True),
    }


metadata = Base.metadata
engine = None
session: Session = None


def get_session() -> Session:
    return session


def _create_engine():
    global engine
    engine = create_engine(DATABASE_URL)
    return engine


def setup_db(engine=None):
    global session
    if not engine:
        engine = _create_engine()
    session_factory = sessionmaker(engine, autocommit=False)
    session = scoped_session(session_factory)


experiments_teams = Table(
    'experiments_teams',
    Base.metadata,
    Column(
        'experiment_id',
        Integer,
        ForeignKey('experiment.id'),
        primary_key=True,
    ),
    Column(
        'team_id',
        Integer,
        ForeignKey('team.id'),
        primary_key=True,
    ),
)


class Experiment(Base):
    """Database model for experiments model."""

    __tablename__ = 'experiment'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    description: Mapped[str]

    sample_ratio: Mapped[int]

    teams: Mapped[list["Team"]] = relationship(
        secondary=experiments_teams, uselist=True, lazy='selectin', back_populates="experiments"
    )


class Team(Base):
    """Database model for team model."""

    __tablename__ = 'team'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    parent_team_id: Mapped[int] = mapped_column(ForeignKey("team.id"), nullable=True)

    name: Mapped[str]

    experiments: Mapped[list["Experiment"]] = relationship(
        secondary=experiments_teams, uselist=True, lazy='selectin', back_populates="teams"
    )


# TODO: extract to a MAT VIEW
experiment_teams_cte = (
    select(
        experiments_teams.c.experiment_id,
        func.array_agg(experiments_teams.c.team_id).label("team_ids"),
    )
    .group_by(experiments_teams.c.experiment_id)
    .cte()
)
