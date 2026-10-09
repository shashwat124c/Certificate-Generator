from flask import Flask

from .config import Config
from .health import health


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    app.add_url_rule("/health", view_func=health, methods=["GET"])

    return app

