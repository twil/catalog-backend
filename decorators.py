# coding: utf-8
from datetime import timedelta
from functools import wraps, update_wrapper
from flask import make_response, request, abort, current_app

#
# View decorators
#

def check_api_key(func):
    """Check validity of API KEY in request"""
    
    @wraps(func)
    def decorator(*args, **kwargs):
        api_key = request.args.get('api_key', '')
        if not api_key:
            api_key = request.form.get('api_key', '')
        if not api_key:
            abort(401, "Invalid request")
            
        if api_key not in current_app.config['API_KEYS']:
            abort(401, "Invalid request")
            
        return func(*args, **kwargs)
    return decorator

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    """Allow cross-domain requests"""

    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

# TODO: add authentication. Development version uses only HTTP AUTH
crossdomain_dec = crossdomain(
    origin = '*',
    headers = [
        'X-Requested-With',
        'Content-Type',
    ])
