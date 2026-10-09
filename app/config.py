import os
from pathlib import Path


class Config:
    ENV = os.getenv("FLASK_ENV", "development")
    BASE_DIR = Path(__file__).resolve().parent.parent
    INSTANCE_DIR = BASE_DIR / "instance"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{INSTANCE_DIR / 'certificates.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

