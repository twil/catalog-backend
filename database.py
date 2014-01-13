# -*- coding: utf-8 -*-
from mongokit import Connection
from models import Product, Category


def get_config(app):
    """Get mongo config
    
    Decides whether to use config for testing or not
    
    """

    mongo_conf = app.config['MONGODB']
    if app.config['TESTING']:
        mongo_conf = app.config['MONGODB_TESTING']

    return mongo_conf

def init_connection(app):
    """
    Init DB connection and register models (documents)
    
    """
    
    config = get_config(app)
    conn = Connection(**config['connection'])
    conn.register([Product, Category])
    
    return conn

def select_db(app, connection):
    """
    Select DB and authenticate
    
    """
    
    config = get_config(app)
    db_name = config['database']['name']
    db_user = config['database']['user']
    db_password = config['database']['password']
    
    db = connection[db_name]
    if db_user and db_password:
        db.authenticate(db_user, db_password)
    
    return db
