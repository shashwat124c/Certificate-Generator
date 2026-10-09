import os


class Config:
    ENV = os.getenv("FLASK_ENV", "development")

