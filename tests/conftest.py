import pytest
from factories import ExperimentFactory
from factories import TeamFactory
from sqlalchemy import event

from db import db_models

test_factories = [ExperimentFactory, TeamFactory]


def bind_test_session_to_factories(session):
    """Set factory session to the test's scoped session."""

    global test_factories

    for factory in test_factories:
        factory._meta.sqlalchemy_session = session


@pytest.fixture(scope='function', autouse=True)
def session():
    """
    Isolated test session.

    For each test create a savepoint within the connection level
    transaction for the test db SQL, rollback once done to the state
    of the connection-level transaction.
    """

    with db_models._create_engine().begin() as connection:
        connection.begin_nested()

        db_models.setup_db(engine=db_models.engine)
        db_models.metadata.create_all(bind=db_models.engine)

        session = db_models.session

        bind_test_session_to_factories(session=session)

        @event.listens_for(session, "after_transaction_end")
        def end_savepoint(session, transaction):
            # Make sure the tests are always running within a savepoint.
            if connection.closed:
                # give up if the connection-level transaction is closed
                return
            if not connection.in_nested_transaction():
                connection.begin_nested()

        yield session

        session.flush()
        session.rollback()
        db_models.metadata.drop_all(bind=db_models.engine)
