import os


class Config(object):
    """This is the main settings object. Define settings variables as UPPER CASE."""
    APP_ROOT = os.path.dirname(os.path.dirname(__file__))
    DB_NAME = 'main.db'
    DATABASE = os.path.join(APP_ROOT, DB_NAME)

    DEBUG = True
    SECRET_KEY = 'development key'
    USERNAME = 'admin'
    PASSWORD = '123'