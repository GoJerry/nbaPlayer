# coding: utf-8

from flask import Flask

from config import Config

config = Config()


def create_app():
    app = Flask(__name__, static_folder="templates")
    app.config.from_object(config)
    with app.app_context():
        register_blueprints(app)

    return app


def register_blueprints(app):
    from .api import application
    app.register_blueprint(application, url_prefix="")
