# coding: utf-8
"""
Package for testing application

"""
from flask.ext.testing import TestCase
from init_app import init_app
from database import init_connection, select_db

class AppTestCase(TestCase):
    """
    Base class for test cases. Initializes mongo connection
    """

    def create_app(self):
        """Helper to create flask app for testing"""

        app = init_app()
        app.config['TESTING'] = True
        app.debug = True
        return app

    def _pre_setup(self):
        """Init db here"""
        
        super(AppTestCase, self)._pre_setup()
        
        self.mongo_connection = init_connection(self.app)
        self.mongo_db = select_db(self.app, self.mongo_connection)
