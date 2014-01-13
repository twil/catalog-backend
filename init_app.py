# -*- coding: utf-8 -*-
"""
Init app object

"""
from flask import Flask
from json_encoder import JSONEncoder

# base config object (module) for Flask app creation
import base_config


def init_app():
    """Init flask app"""

    app = Flask(__name__)
    app.config.from_object(base_config)
    # Production or local config
    app.config.from_envvar('QFOOD_CONFIG', silent = True)
    # set json encoder capable serializing MongoDB ObjectId
    app.json_encoder = JSONEncoder

    return app
