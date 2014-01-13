# coding: utf-8
from flask import json
from bson import json_util
from mongokit import ObjectId

def to_json(data):
    return json.dumps(data, default=json_util.default)

class JSONEncoder(json.JSONEncoder):
    """JSON encoder capable of serializing ObjectIds"""
    
    def default(self, o):
        if isinstance(o, ObjectId):
            return unicode(o)
        return super(JSONEncoder, self).default(o)
