import os

DEBUG = os.getenv('DEBUG', False)
SECRET_KEY = os.getenv(
    'SECRET_KEY', 'change_me')
