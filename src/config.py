from urllib.parse import quote

from prettyconf import config
from prettyconf.loaders import EnvFile
from prettyconf.loaders import Environment

config.loaders = [
    Environment(var_format=str.upper),
    EnvFile(filename='.env', var_format=str.upper),
]

DATABASE_NAME = config('DATABASE_NAME', default='rec_task')
DATABASE_HOST = config('DATABASE_HOST', default='127.0.0.1')
DATABASE_PORT = config('DATABASE_PORT', default='15436')
DATABASE_USER = config('DATABASE_USER', default='rec_task')
DATABASE_PASSWORD = config('DATABASE_PASSWORD', default='rec_task')
DATABASE_DRIVER = 'postgresql+psycopg2'
DATABASE_URL = f'{DATABASE_DRIVER}://{DATABASE_USER}:{quote(DATABASE_PASSWORD)}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'  # noQA
