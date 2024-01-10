import datetime

from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import Session
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    type_annotation_map = {
        datetime.datetime: TIMESTAMP(timezone=True),
    }


metadata = Base.metadata
engine = None
session: Session = None


class Experiment(Base):
    """Database model for experiments model."""

    __tablename__ = 'experiment'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    description: Mapped[str]

    sample_ration: Mapped[int]


class Team(Base):
    """Database model for team model."""

    __tablename__ = 'team'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str]
