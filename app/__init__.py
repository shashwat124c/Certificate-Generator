from pathlib import Path

from flask import Flask

from .config import Config
from .extensions import db
from .health import health
from .routes import api


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    app.register_blueprint(api, url_prefix="/api/v1")
    app.add_url_rule("/health", view_func=health, methods=["GET"])

    with app.app_context():
        db.create_all()

    return app

