# -*- encoding: utf-8 -*-
from itertools import chain
from mongokit import Document, ObjectId, OR


class Product(Document):
    """
    Product or product type
    
    Makes tree with attribute inheritance
    
    Create object:
    >>> from database import init_db
    >>> from app import app
    >>> conn = init_db(app)
    >>> coll = conn['test'].products
    >>> p = coll.Product()
    >>> p.name = u"Prod1"
    >>> p.description = u"Desc1"
    >>> p.price = 1.1
    >>> p.save()
    
    Set custom property:
    >>> p['custom_property'] = u"SomeSome"
    >>> p.save()
    
    Query:
    >>> list(coll.Product.find())
    [{u'category': None, u'name': u'Prod1', u'price': 1.1, 
    u'custom_property': u'SomeSome', u'units': None, u'icon_small': None, 
    u'_id': ObjectId('51d614d2eac8ad4dcb2bc7dd'), u'icon_big': None, 
    u'description': u'Desc1'}]
    
    All products and templates are added to root template or its children.
    
    root (template)
      |
      |-- pizzas (template)
      |     |
      |     |-- New-York
      |
      |-- Heineken
    
    """
    
    structure = {
        'name': unicode,
        'description': unicode,
        'price': float,
        'units': unicode,
        'icon_small': unicode,
        'icon_big': unicode,
        
        'is_template': bool,
        'is_hidden': bool,
        
        # list of custom properties
        # TODO: it ought to be moved to some meta-data
        #       and properties should be just plane obj['prop']
        'properties': [
            {
                "name": unicode,
                "label": unicode,
                #"type": OR(int, float, unicode, list),
                "default_value": OR(bool, int, float, unicode),
                "value": OR(bool, int, float, unicode),
                "options": list, # if not empty then we have "select" field
                "order": int,
                "is_deleted": bool,
            }
        ],
        
        # references to Categories
        'categories': [ObjectId],
        
        # reference to Product
        'parent': ObjectId,
    }
    
    default_values = {
        'price': 0.0,
        'is_template': False,
        'units': u'шт.',
        'description': u'',
        'icon_small': u'',
        'icon_big': u'',
    }
    
    use_dot_notation = True
    use_schemaless = True
    
    #
    # Custom properties API
    #
    # this methods save object
    #
    
    def add_property(self, name, default_value, value, options=None, order=0, 
                     label=None, is_deleted=False):
        """
        Add custom property to product and all it's descendants
        
        If property already exists it will be recreated.
        
        """
        
        if options is None:
            options = []
        
        if label is None:
            label = unicode(name).capitalize()
    
        # TODO: not so good. we a wrapping and unwrapping values in every call.
        #       we may simply use **kwargs and pass that dict
        prop = {
            "name": unicode(name),
            "label": label,
            "default_value": default_value,
            "value": value,
            "options": options,
            "order": order,
            "is_deleted": is_deleted,
        }
    
        self.del_property(prop['name'], True)
        
        self.properties.append(prop)
        self.save()
        
        # find descendants and add
        descendants = self.collection.Product.find({"parent": self._id})
        for p in descendants:
            p.add_property(**prop)
            
    def edit_property(self, name, **kwargs):
        """
        Change attributes of property
        
        Recursive. Can override current values for all products!!!
        
        """
        
        prop_fields = [
            "name",
            "label",
            "default_value",
            "value",
            "options",
            "order",
            "is_deleted",
        ]
        
        prop_found = False
        for i, v in enumerate(self.properties):
            if v['name'] == name:
                prop_found = True
                for pk, pv in kwargs.items():
                    if pk in prop_fields:
                        self.properties[i][pk] = pv
                self.save()
        
        if not prop_found:
            raise Exception(u"Custom property '{}' not found for ObjectId('{}')".format(name, self._id))
        
        descendants = self.collection.Product.find({"parent": self._id})
        for p in descendants:
            p.edit_property(name, **kwargs)
    
    def del_property(self, name, recursively=False):
        """
        Delete custom property
        
        By default deletes (marks deleted) property of current node (product).
        If recursively is True than completely deletes property from current
        node and all it descendants.  
        
        """
        
        # only set flag on current product
        if not recursively:
            for i, v in enumerate(self.properties):
                if v['name'] == name:
                    self.properties[i]['is_deleted'] = True
                    self.save()
                    break
            return
        
        # completely delete property
        for i, v in enumerate(self.properties):
            if v['name'] == name:
                del self.properties[i]
                self.save()
                break
        
        # only saved products can have descendants
        if '_id' in self:
            descendants = self.collection.Product.find({"parent": self._id})
            for p in descendants:
                p.del_property(name, True)

    def get_property(self, name):
        """Get custom property by name"""
        
        for p in self.properties:
            if p['name'] == name:
                return p['value']
        
        return None

    def get_properties(self):
        """Get custom properties as dict"""
        props = {}
        if self['properties']:
            for p in self['properties']:
                props[p['name']] = p['value']
        return props
    
    def set_property(self, name, value):
        """
        Set custom property
        
        Property must be added before or exception will be thrown
        
        """
    
        for i, v in enumerate(self.properties):
            if v['name'] == name:
                self.properties[i]['value'] = value
                self.save()
                return True
            
        return False
    
    #
    # API for using custom properties as properties;)
    #
    
    def __setattr__(self, key, value):
        if key.startswith('custom_property'):
            self.set_property(key.replace('custom_property_', ''), value)
        else:
            super(Product, self).__setattr__(key, value)
    
    def __getattr__(self, key):
        if key.startswith('custom_property'):
            return self.get_property(key.replace('custom_property_', ''))
        else:
            return super(Product, self).__getattr__(key)
    
    
