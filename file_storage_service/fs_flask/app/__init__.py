import os
from flask import Flask
from .config import configure

from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

from flask_cors import CORS


db = SQLAlchemy()
ma = Marshmallow()

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    CORS(app)

    configure("DEV", app)

    # serialize/deserialize
    ma = Marshmallow(app)

    with app.app_context():
        # Imports
        from .blueprints.files_storage.fs_bp import bp as fs_bp

        # DB connection configuration
        #app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@authenticationdb:5432/authdb'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@10.5.7.11:5861/fsdb'
        db.init_app(app)
        db.create_all()

        # flask-bcrypt
        #bcrypt.init_app(app)

        app.register_blueprint(fs_bp)

        return app
