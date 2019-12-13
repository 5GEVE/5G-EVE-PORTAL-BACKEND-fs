import os
from flask import Flask
from .config import configure

from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_oidc import OpenIDConnect
from flask_cors import CORS

from app.keycloak.keycloak_client import Keycloak

db = SQLAlchemy()
ma = Marshmallow()
bcrypt = Bcrypt()
oidc = OpenIDConnect()

# Keycloak adapter
kc_client = Keycloak()

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)
    configure("DEV", app)

    # serialize/deserialize
    ma = Marshmallow(app)

    with app.app_context():
        # Imports
        from .blueprints.files.files_bp import bp as files_bp

        # DB connection configuration
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Hw8J6q2hCGr7xga8@127.0.0.1:5060/ftpdb'
        db.init_app(app)
        db.create_all()

        # flask-bcrypt
        bcrypt.init_app(app)

        # OpenIDConnect initialization
        oidc.init_app(app)

        app.register_blueprint(files_bp)

        return app
