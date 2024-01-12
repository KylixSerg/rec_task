import datetime

from sqlalchemy import TIMESTAMP
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Table
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import text
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

    @staticmethod
    def get_all_sub_teams(team_ids: tuple[int]):
        """
        Return all teams down the hierarchy of teams.
        """
        session = get_session()

        query = text(
            """
        WITH RECURSIVE levels AS (
            SELECT parent_team_id, '{}'::INT[] || id AS children
            FROM team
            UNION ALL
            SELECT t.parent_team_id, l.children || t.id
            FROM team t
            JOIN levels l ON t.id = l.parent_team_id
        ),
        parent_subteams AS (
            SELECT
                parent_team_id AS team_id, ARRAY_AGG(DISTINCT child) AS children
            FROM
                levels,
                LATERAL UNNEST(children) AS child
            WHERE
                parent_team_id IN :team_ids
            GROUP BY
            parent_team_id
        )
        -- TODO: So we use this for queries - Ideally this is a Mat view 
        SELECT ARRAY_AGG(DISTINCT child) FROM parent_subteams, UNNEST(children) child
            
        """
        )
        params = {
            'team_ids': team_ids,
        }

        return session.scalar(query, params=params) or []


# TODO: extract to a MAT VIEW
experiment_teams_cte = (
    select(
        experiments_teams.c.experiment_id,
        func.array_agg(experiments_teams.c.team_id).label("team_ids"),
    )
    .group_by(experiments_teams.c.experiment_id)
    .cte()
)
