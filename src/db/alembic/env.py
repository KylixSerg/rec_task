from logging import getLogger
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import text

from config import DATABASE_URL
from db import db_models

logger = getLogger('alembic.env')

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option('sqlalchemy.url', DATABASE_URL.replace('%', '%%'))

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = db_models.metadata


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    """

    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    engine = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    connection = engine.connect()
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        process_revision_directives=process_revision_directives,
    )

    try:
        with context.begin_transaction():
            # Ensure serialized migrations when multiple instance try to apply them
            context.get_context()._ensure_version_table()
            logger.info("Acquiring lock on `alembic_version` table")
            connection.execute(text("LOCK TABLE alembic_version IN ACCESS EXCLUSIVE MODE"))
            logger.info("Lock acquired, running migrations")
            context.run_migrations()
            logger.info("Migrations finished (if any)")
    finally:
        connection.close()


# Let's run alembic in online mode only, since we have DB privileges
# and we probably would like to have this automated as part of the API
# startup lifecycle where online mode should suffice, we can always
# add offline functionality later on if needed.
run_migrations_online()
