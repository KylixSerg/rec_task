import datetime

from sqlalchemy import TIMESTAMP
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Table
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import Session
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    type_annotation_map = {
        datetime.datetime: TIMESTAMP(timezone=True),
    }


metadata = Base.metadata
engine = None
session: Session = None


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

    experiments: Mapped[list["Team"]] = relationship(
        secondary=experiments_teams, uselist=True, lazy='selectin'
    )


class Team(Base):
    """Database model for team model."""

    __tablename__ = 'team'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str]

    experiments: Mapped[list["Experiment"]] = relationship(
        secondary=experiments_teams, uselist=True, lazy='selectin'
    )
