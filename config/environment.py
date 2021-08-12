import os

ENVIRONMENT=  os.environ.get("ENVIRONMENT", "development")

SETTINGS_DICT = {
    "local": "config.settings.local",
    "development": "config.settings.development",
    "production": "config.settings.production"
}

SETTINGS_MODULE = SETTINGS_DICT.get(ENVIRONMENT, 'local')