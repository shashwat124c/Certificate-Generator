import shutil
import uuid
from pathlib import Path

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture()
def app():
    test_root = Path.cwd() / ".test_artifacts" / str(uuid.uuid4())
    test_root.mkdir(parents=True, exist_ok=True)
    database_path = test_root / "test.db"
    storage_path = test_root / "certificates"

    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path.as_posix()}",
            "CERTIFICATE_STORAGE_PATH": str(storage_path),
        }
    )
    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
    shutil.rmtree(test_root, ignore_errors=True)


@pytest.fixture()
def client(app, monkeypatch):
    # Keep requests deterministic; tests run the worker explicitly when needed.
    monkeypatch.setattr("app.routes.submit_job", lambda _app, _job_id: None)
    return app.test_client()
