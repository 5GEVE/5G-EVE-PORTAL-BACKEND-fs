from flask import ( jsonify, request )
from functools import wraps

from .keycloak_client import KeycloakClient

kc_client = KeycloakClient()

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if not 'Authorization' in request.headers:
            return jsonify({"message": "Authorization header not provided"}), 401

        token = str(request.headers["Authorization"]).split(" ")[1]
        status, token_data = kc_client.token_to_user(token)

        if status != 200:
            return jsonify({"message": "Token not valid"}), 401

        token_data['access_token'] = token

        return f(token_data, *args, **kwargs)
    return decorator