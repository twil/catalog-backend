# coding: utf-8
"""
Backend for mobile clients

"""
from init_app import init_app
from json_encoder import JSONEncoder
from flask import json, render_template, request, abort
from flask.ext.restful import Resource, Api, reqparse, fields, marshal, marshal_with
from flask.ext.restful.representations.json import settings as restful_json_output_settings
from database import init_connection, select_db
from decorators import check_api_key, crossdomain_dec
from mongokit import ObjectId
from images import save_img


#
# Init
#

# Create mobile backend app object
app = init_app()

# init DB connection and register models
connection = init_connection(app)

# select DB and authenticate
db = select_db(app, connection)

# HACK: configuring flask-restful json_output helper function
restful_json_output_settings['cls'] = JSONEncoder
api = Api(app, decorators = [crossdomain_dec])

#
# Helpers
#

def to_object_id(data):
    """Get ObjectId from request right"""
    
    if not data:
        return None
    
    return ObjectId(data)

def to_object_id_list(data):
    """Get ObjectId list from request"""
    
    if not data:
        return []
    return [ObjectId(i) for i in data if i]

def to_image_data(data):
    """Get image data from request
    
    Image may come in "data:" URL (base64)
    
    Returns mime, data
    
    """
   
    # removing image
    if not data:
        return u''

    # image path (not changed)
    if data[0:5] != u'data:':
        return None
    
    # TODO: better MIME handling
    mime = data[5:data.index(u';')].lower()
    img = data[data.index(u',') + 1:].decode('base64')
    
    return mime, img

def add_custom_properties(product):
    """Add custom properties to product"""
    
    # TODO: may override property of object
    if product['properties']:
        for p in product['properties']:
            product[p['name']] = p['value']
    
    return product

class ImageField(fields.Raw):
    """Prepends STATIC_URL to image fields"""
    
    def format(self, value):
        if not value:
            return ''
        return os.path.join(STATIC_URL, value)

class ObjectIdField(fields.Raw):
    """Converts ObjectId to str"""
    
    def format(self, value):
        return unicode(value)

class NoneCapableList(fields.List):
    """If item is None return empty list"""

    def output(self, key, data):
        if key not in data or not data[key]:
            return []

        return super(NoneCapableList, self).output(key, data)

class CustomPropertyField(fields.Raw):
    """Get custom property from object"""
    
    def output(self, key, obj):
        return super(CustomPropertyField, self).output(key, obj)

class DateTimeField(fields.Raw):
    """Return formated datetime value"""
    
    def format(self, value):
        return value.strftime('%s %s'.format(DATE_FORMAT, TIME_FORMAT))


#
# Admin interface API
#

# category data parser
category_parser = reqparse.RequestParser()
category_parser.add_argument('name', type=unicode, location = 'json')
category_parser.add_argument('description', type=unicode, location = 'json')
category_parser.add_argument('icon_small', type=to_image_data, location = 'json')
category_parser.add_argument('icon_big', type=to_image_data, location = 'json')
category_parser.add_argument('is_hidden', type=bool, location = 'json')
category_parser.add_argument('order', type=int, location = 'json')
category_parser.add_argument('items_order', type=to_object_id_list, location = 'json')
category_parser.add_argument('parent', type=to_object_id, location = 'json')

# category fields
category_fields = {
    "id": fields.String(attribute='_id'),
    "name": fields.String,
    "description": fields.String,
    "icon_small": ImageField,
    "icon_big": ImageField,
    "is_hidden": fields.Boolean,
    "order": fields.Integer,
    "items_order": fields.List(ObjectIdField),
    "parent": fields.String,
}

# Category Resource
class CategoryList(Resource):
    """List of categories and new category creation"""
    
    def options(self):
        return '', 200, {'Allow': 'GET,POST,OPTIONS'}
    
    @marshal_with(category_fields)
    def get(self):
        """Just return list of categories - all of them"""
        
        categories = db.categories.Category.find()
        return list(categories)
    
    @marshal_with(category_fields)
    def post(self):
        """Create new category
        
        It is rather empty by default. We only really need 'parent'
        
        """

        args = category_parser.parse_args()
        
        category = db.categories.Category()
        category.name = args['name']
        category.description = args['description']
        category.is_hidden = args['is_hidden']
        category.order = args['order']
        # TODO: check IDs
        # TODO: flask-restful doesn't create arg if it's not in request
        if args['items_order'] is None:
            args['items_order'] = []
        category.items_order = args['items_order']
        
        parent = None
        # chech ID for parent
        if 'parent' in args and args['parent'] is not None:
            parent = db.categories.Category.find_one({"_id": ObjectId(args['parent'])})
        if parent is not None:
            category.parent = parent['_id']
        
        category.save()
        
        return category, 201

class Category(Resource):
    """Single category get, update, delete"""
    
    def options(self):
        return '', 200, {'Allow': 'GET,DELETE,POST,OPTIONS'}
    
    @marshal_with(category_fields)
    def get(self, id_):
        """Get single category"""
        
        try:
            category = db.categories.Category.find_one({"_id": ObjectId(id_)})
        except:
            # TODO: better exception handling - not catch all
            return 'Not found', 404
        
        return category
    
    def delete(self, id_):
        """Remove and that's all"""
        
        db.categories.remove({'_id': ObjectId(id_)})
        return '', 204
    
    @marshal_with(category_fields)
    def post(self, id_):
        """Update category data
        
        Images (icon_small, icon_big) may come in 'data:' URL (base64)
        
        """
        
        try:
            category = db.categories.Category.find_one({"_id": ObjectId(id_)})
        except:
            # TODO: better exception handling - not catch all
            return 'Not found', 404
        
        args = category_parser.parse_args()
        
        category.name = args['name']
        category.description = args['description']
        category.is_hidden = args['is_hidden']
        category.order = args['order']
        # TODO: check IDs
        category.items_order = args['items_order']
        
        # handle parent change (or not change :))
        if 'parent' in args:
            parent = None
            if args['parent'] is not None:
                parent = db.categories.Category.find_one({"_id": ObjectId(args['parent'])})
            if parent is not None:
                category.parent = parent['_id']

            # move to top
            if not args['parent']:
                category.parent = None
        
        # TODO: refactor image handling
        # big image
        if args['icon_big'] is not None and args['icon_big']:
            filepath = save_img(
                os.path.join(
                    STATIC_ROOT,
                    'categories',
                    '{}_icon_big'.format(str(category['_id']))
                ), 
                args['icon_big']
            )
            category.icon_big = os.path.join('categories', os.path.basename(filepath))
        elif args['icon_big'] is not None and not args['icon_big']:
            category.icon_big = u''

        # small image
        if args['icon_small'] is not None and args['icon_small']:
            filepath = save_img(
                os.path.join(
                    STATIC_ROOT,
                    'categories',
                    '{}_icon_small'.format(str(category['_id']))
                ), 
                args['icon_small']
            )
            category.icon_small = os.path.join('categories', os.path.basename(filepath))
        elif args['icon_small'] is not None and not args['icon_small']:
            category.icon_small = u''
        
        category.save()
        
        return category, 201

# register Category Resource
api.add_resource(CategoryList, '/db/categories')
api.add_resource(Category, '/db/categories/<string:id_>')


# product data parser
product_parser = reqparse.RequestParser()
product_parser.add_argument('name', type=unicode, location = 'json')
product_parser.add_argument('description', type=unicode, location = 'json')
product_parser.add_argument('price', type=float, location = 'json')
product_parser.add_argument('icon_small', type=to_image_data, location = 'json')
product_parser.add_argument('icon_big', type=to_image_data, location = 'json')
product_parser.add_argument('categories', type=list, location = 'json')
product_parser.add_argument('parent', type=to_object_id, location = 'json')
product_parser.add_argument('is_hidden', type=bool, location = 'json')

# custom property fields
customproperty_fields = {
    "name": fields.String,
    "label": fields.String,
    "default_value": fields.String,
    "value": fields.String,
    "options": fields.List(fields.String),
    "order": fields.Integer,
    "is_deleted": fields.Boolean,
}

# product fields
product_fields = {
    "id": fields.String(attribute = '_id'),
    "name": fields.String,
    "description": fields.String,
    "price": fields.Float,
    "icon_small": ImageField,
    "icon_big": ImageField,
    "categories": fields.List(ObjectIdField),
    "is_hidden": fields.Boolean,
    "parent": fields.Raw,
    "properties": fields.List(fields.Nested(customproperty_fields)),
}

# Product Resource
class ProductList(Resource):
    """List of products and new product creation"""
    
    def options(self):
        return '', 200, {'Allow': 'GET,POST,OPTIONS'}
    
    #@marshal_with(product_fields)
    def get(self):
        """Return products list
        
        Plane list without templates.
        
        TODO: Custom fields are inherited from parent
        
        """
        
        products = db.products.Product.find({"is_template": False})
        
        # marshal and transform custom properties
        products_marshaled = marshal(list(products), product_fields)
        products_marshaled = [add_custom_properties(p) for p in products_marshaled]
        
        return products_marshaled
    
    #@marshal_with(product_fields)
    def post(self):
        """Create new product

        Basically it is created empty
                
        """

        args = product_parser.parse_args()
        
        product = db.products.Product()
        product.name = args['name']
        product.description = args['description']
        product.price = args['price']
        product.is_hidden = args['is_hidden']
        
        product.save()
        
        # marshal and transform custom properties
        product_marshaled = marshal(product, product_fields)
        product_marshaled = add_custom_properties(product_marshaled)
        
        return product_marshaled, 201

class Product(Resource):
    """Single product get, update, delete
    
    TODO: custom properties with nested resource
    like /products/<id>/property/<name>
    
    """
    
    def options(self):
        return '', 200, {'Allow': 'GET,DELETE,POST,OPTIONS'}
    
    #@marshal_with(product_fields)
    def get(self, id_):
        """Get single product"""
        
        try:
            product = db.products.Product.find_one({"_id": ObjectId(id_)})
        except:
            # TODO: better exception handling - not catch all
            return 'Not found', 404
        
        # marshal and transform custom properties
        product_marshaled = marshal(product, product_fields)
        product_marshaled = add_custom_properties(product_marshaled)
        
        return product_marshaled
    
    def delete(self, id_):
        """Remove and that's all"""
        
        db.products.remove({'_id': ObjectId(id_)})
        return '', 204
    
    #@marshal_with(product_fields)
    def post(self, id_):
        """Update product data
        
        Images (icon_small, icon_big) may come in data: URL (base64)
        
        """
        
        try:
            product = db.products.Product.find_one({"_id": ObjectId(id_)})
        except:
            # TODO: better exception handling - not catch all
            return 'Not found', 404
        
        args = product_parser.parse_args()
        
        product.name = args['name']
        product.description = args['description']
        product.price = args['price']
        product.is_hidden = args['is_hidden']
        
        # check categories
        categories = []
        for c in args['categories']:
            cat = db.categories.Category.find_one({"_id": ObjectId(c)})
            if cat is None:
                continue
            categories.append(cat['_id'])
            # update items ordering in category
            if product['_id'] not in cat['items_order']:
                cat['items_order'].append(product['_id'])
                cat.save()
        product.categories = categories

        # TODO: refactor
        # big image
        if args['icon_big'] is not None and args['icon_big']:
            filepath = save_img(
                os.path.join(
                    STATIC_ROOT,
                    'products',
                    '{}_icon_big'.format(str(product['_id']))
                ), 
                args['icon_big']
            )
            product.icon_big = os.path.join('products', os.path.basename(filepath))
        elif args['icon_big'] is not None and not args['icon_big']:
            product.icon_big = u''

        # small image
        if args['icon_small'] is not None and args['icon_small']:
            filepath = save_img(
                os.path.join(
                    STATIC_ROOT,
                    'products',
                    '{}_icon_small'.format(str(product['_id']))
                ), 
                args['icon_small']
            )
            product.icon_small = os.path.join('products', os.path.basename(filepath))
        if args['icon_small'] is not None and not args['icon_small']:
            product.icon_small  = u''
        
        product.save()
        
        # marshal and transform custom properties
        product_marshaled = marshal(product, product_fields)
        product_marshaled = add_custom_properties(product_marshaled)
        
        return product_marshaled, 201

# register Product Resource
api.add_resource(ProductList, '/db/products')
api.add_resource(Product, '/db/products/<string:id_>')
