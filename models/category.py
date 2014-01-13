# -*- encoding: utf-8 -*-
from mongokit import Document, ObjectId


class Category(Document):
    """
    Category
    
    Forms tree
    
    """
    
    structure = {
        'name': unicode,
        'description': unicode,
        'icon_small': unicode,
        'icon_big': unicode,
        "is_hidden": bool,
        "order": int,
        "items_order": [ObjectId],
        
        # reference to Category 
        'parent': ObjectId,
    }
    
    default_values = {
        "order": 0,
        "is_hidden": True,
        "name": u"",
        "description": u"",
        "items_order": [],
    }
    
    use_dot_notation = True
    # for storing different metadata
    use_schemaless = True
