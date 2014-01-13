# coding: utf-8
"""
Backend for mobile clients

"""
from init_app import init_app
from flask import json, render_template, request, abort
from flask.ext.mail import Mail, Message
from flask.ext.restful import fields, marshal, marshal_with
from database import init_connection, select_db
from decorators import check_api_key, crossdomain_dec
from mongokit import ObjectId


#
# Init
#

# Create mobile backend app object
app = init_app()

# init DB connection and register models
connection = init_connection(app)

# select DB and authenticate
db = select_db(app, connection)

# mail
mail = Mail(app)


#
# Helpers
#

# TODO: refactor. partially overlaps with admin api.

class DateTimeField(fields.Raw):
    """Return formated datetime value"""
    
    def format(self, value):
        return value.strftime('%s %s'.format(DATE_FORMAT, TIME_FORMAT))

# cart item fields
cartitem_fields = {
    "id": fields.String,
    "name": fields.String,
    "count": fields.Integer,
    "total": fields.Float,
    "custom_properties": fields.Raw, # no marshaling here!
}

# address fields
address_fields = {
    "street": fields.String,
    "house": fields.String,
    "building": fields.String,
    "porch": fields.String,
    "floor": fields.String,
    "room": fields.String,
    "comments": fields.String,
}

# person fields
person_fields = {
    "firstname": fields.String,
    "lastname": fields.String,
    "fathersname": fields.String,
}

# order fields
order_fields = {
    "id": fields.String(attribute = '_id'),
    "datetime": DateTimeField,
    "status": fields.String,
    "address": fields.Nested(address_fields),
    "person": fields.Nested(person_fields),
    "phones": fields.List(fields.String),
    "comments": fields.String,
    "operator_comments": fields.String,
    "count": fields.Integer,
    "total": fields.Float,
    "cart": fields.List(fields.Nested(cartitem_fields)),
}


#
# Mobile client API
#

@app.route('/db_version', methods = ['GET', 'OPTIONS'])
@check_api_key
@crossdomain_dec
def get_db_version():
    """
    Return current db version
    
    Hash of prepared DB in cache (Redis). If differes from previously saved
    value on client request for full DB is made

    TODO:
    
    """
    
    return json.jsonify(version = 1)

@app.route('/db', methods = ['GET', 'OPTIONS'])
@check_api_key
@crossdomain_dec
def get_db():
    """
    Return DB in format suitable for client app

    It is designed to return full DB. Client app should work offline.
    Total size is roughly 300 Kb for every 500 products (not gziped).
    
    Format as follows (JSON):
    {
        "collections": [
            "categories",
            "dishes"
        ],
        
        "categories": {
            "<id>": {
                "id": "<id>",
                "parent": "<cat_id>",
                "label": "Category",
                ...
            },
            ...
        },
        
        "dishes": {
            "<id>": {
                "id": "<id>",
                "categories": ["<cat1_id>", ...],
                "label": "Dish",
                ...
            },
            ...
        }
    }
        
    """
    
    def _adapt_category(obj):
       
        return (
            unicode(obj['_id']),
            {
                "id": obj['_id'],
                "parent": obj['parent'],
                "label": obj['name'],
                "description": obj['description'],
                "icon_small": obj['icon_small'],
                "icon_big": obj['icon_big'],
                "order": obj['order'],
                "items_order": obj['items_order'] if 'items_order' in obj else [],
            },
        )
        
    def _adapt_product(obj):

        props = {
            "id": obj['_id'],
            "categories": obj["categories"],
            "label": obj['name'],
            "description": obj['description'],
            "price": obj['price'],
            "units": obj['units'],
            "icon_small": obj['icon_small'],
            "icon_big": obj['icon_big'],
            "parent": obj['parent'],
        }
        
        # TODO: may overwrite product property
        for custom_prop in obj['properties']:
            props[custom_prop['name']] = custom_prop['value']
        
        return (
            unicode(obj['_id']),
            props,
        )

    categories = list(db.categories.Category.find({
        "is_hidden": False
    }))
    products = list(db.products.Product.find({
        "is_template": False,
        "is_hidden": False,
        "categories": {
            "$ne": []
        },
    }))
        
    db_data = {
        "collections": [
            "categories",
            "dishes",
        ],
        "categories": dict(map(_adapt_category, categories)),
        "dishes": dict(map(_adapt_product, products)),
    }
    
    return json.jsonify(**db_data)

@app.route('/order', methods = ['POST', 'OPTIONS'])
@check_api_key
@crossdomain_dec
def post_order():
    """
    Post order
    
    Create DB entry and notify restaurant staff via email letter.

    Order freezes values (prices especially) for products in itself.
    
    """
       
    cart = json.loads(request.form.get('cart', '[]'))
    address = json.loads(request.form.get('address', '{}'))
    phones = json.loads(request.form.get('phones', '[]'))
    total = 0.0
    for p in cart:
        prod = db.products.Product.find_one({u"_id": ObjectId(p['id'])})
        if prod is None:
            continue
        prod['total'] = prod['price'] * p['count']
        total += float(prod['total'])

        for custom_opt in prod['properties']:
            prod[custom_opt['name']] = custom_opt['value']
        p.update(prod)
        # add custom properties
        p['custom_properties'] = prod.get_properties()
    
    # form fields
    person = {
        "firstname": request.form.get('firstname', u''),
        "lastname": request.form.get('lastname', u''),
        "fathersname": request.form.get('fathersname', u''),
    }
    order_comments = request.form.get('comments', u'')
    
    # address
    address = {
        "street": address.get('street', u''),
        "house": address.get('house', u''),
        "building": address.get('building', u''),
        "porch": address.get('porch', u''),
        "floor": address.get('floor', u''),
        "room": address.get('room', u''),
        "comments": address.get('comments', u''),
    }

    # Secret hash to change order status via Public API
    # Needed for restaurant operators. They are changing status right
    # from email.
    secret_key = uuid.uuid4().get_hex()

    # REMOVED IN DEMO: get settings
    #settings = get_settings_from_db(db)

    # get emails
    email_from = 'order@example.com'
    #if 'order_email_from' in settings and settings['order_email_from']:
    #    email_from = settings['order_email_from']
    emails_to = ['twildor@gmail.com']
    #if 'order_email_to' in settings and settings['order_email_to']:
    #    # may be comma separated list
    #    emails_to = [e.strip() for e in settings['order_email_to'].split(',') if e.strip()]

    # send message
    # log errors
    if emails_to:
        try:
            msg = Message(
                u'[FOOD] new order',
                sender = email_from,
                recipients = emails_to
            )

            order_text = render_template('new_order_email.txt',
                person = person,
                phones = phones,
                cart = cart,
                total = total,
                order_comments = order_comments,
                address = address,
                secret = secret_key,
                #settings = settings
            )

            msg.body = order_text
            mail.send(msg)
        except Exception as e:
            app.logger.error(pprint.pformat(e))
   
    # create order in DB
    # REMOVED IN DEMO:
    #order = db.orders.Order()
    order = {}
    order['person'] = person
    order['address'] = address
    order['phones'] = phones
    #order.phone_hidden = phone_hidden
    order['comments'] = order_comments
    order['datetime'] = datetime.now()
    order['status'] = u'new'
    order['count'] = len(cart)
    order['total'] = total
    order['secret'] = unicode(secret_key)
    
    # need to filter cart fields
    order_cart = []
    for i in cart:
        order_cart.append({
            "id": ObjectId(i["id"]),
            "name": i["name"],
            "count": i["count"],
            "total": i["total"],
            "custom_properties": i["custom_properties"],
        })
    order['cart'] = order_cart
   
    # REMOVED IN DEMO:
    #order.save()

    data = marshal(dict(order), order_fields)
    return json.jsonify(data)

