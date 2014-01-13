# -*- coding: utf-8 -*-
"""
Base configuration

"""
import os


DEBUG = True
SECRET_KEY = 'KryPharphUbJeraxFurUpjuAkticGewdAlUnayftosyairgadchocveefipVuFlo'
JSON_AS_ASCII = False

# key: api_version
API_KEYS = {
    "yoarmoitOxEvhacsIamorhactOoheeckvoorgyixnoFraggOnidBafphufIfnoyt": "0.1",
}

# Main DB
MONGODB = {
    "connection": {
        "host": "localhost",
        "port": 27017,
        "safe": True,
        "journal": True,
    },
    "database": {
        "name": "food",
        "user": "",
        "password": "",
    }
}

# DB for testing
MONGODB_TESTING = {
    "connection": {
        "host": "localhost",
        "port": 27017,
        "safe": True,
        "journal": True,
    },
    "database": {
        "name": "food_test",
        "user": "",
        "password": "",
    }
}

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(PROJECT_PATH, 'static')

# Ought be on different domain and served separately
STATIC_URL = '/static'

# Mail config
MAIL_SERVER = 'localhost'
MAIL_DEBUG = True
#MAIL_PORT = 25
#MAIL_USE_TLS = False
#MAIL_USE_SSL = False
#MAIL_USERNAME = 'username'
#MAIL_PASSWORD = 'password'

# Bug reports
BUG_FROM = 'food.bug@example.com'
BUG_TO = [
    "twildor@gmail.com",
]

# Default date and time formats
DATE_FORMAT = '%d/%m/%y'
TIME_FORMAT = '%H:%M'
