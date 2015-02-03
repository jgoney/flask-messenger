"""Common settings are defined here. Only upper case variables are exported."""

import os


APP_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_NAME = 'main.db'
DATABASE = os.path.join(APP_ROOT, DB_NAME)
