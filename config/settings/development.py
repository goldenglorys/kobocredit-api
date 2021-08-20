from .base import *

DEBUG == config('DEBUG', default=True, cast=bool)

from decouple import config
import django_heroku
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from environs import Env
env = Env()
env.read_env() 

import django_heroku

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

SECRET_KEY = 'testing21wq'

# CORS_ORIGIN_WHITELIST = (
#     'localhost:3000'
# )

CORS_ORIGIN_ALLOW_ALL = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'), 
        'PORT': 5432  # default postgres port
    }
    # "default": env.dj_db_url("DATABASE_URL")

    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    # }

}

# django_heroku.settings(locals())