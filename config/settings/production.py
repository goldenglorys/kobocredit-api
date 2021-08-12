from .base import *
from decouple import config
import django_heroku
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


DEBUG = False

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# CORS_ORIGIN_WHITELIST = (
#     'productbase-*.now.sh'
# )

# CORS_ORIGIN_REGEX_WHITELIST = (r'^(https?://)?(\w+\-\w+\.)?now\.sh$', )

CORS_ORIGIN_ALLOW_ALL = True

django_heroku.settings(locals())

sentry_sdk.init(
    dsn="https://04f18b6642a745b49a82d2e0f182661d@sentry.io/1464931",
    integrations=[DjangoIntegration()]
)
