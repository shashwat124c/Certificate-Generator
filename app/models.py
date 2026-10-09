import json
import uuid
from datetime import datetime, timezone

from .extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class GenerationJob(db.Model):
    __tablename__ = "generation_jobs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = db.Column(db.String(20), nullable=False, default="queued")
    total_count = db.Column(db.Integer, nullable=False)
    success_count = db.Column(db.Integer, nullable=False, default=0)
    failure_count = db.Column(db.Integer, nullable=False, default=0)
    certificate_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    recipients = db.relationship(
        "Recipient", back_populates="job", cascade="all, delete-orphan"
    )

    def certificate_details(self):
        return json.loads(self.certificate_data)


class Recipient(db.Model):
    __tablename__ = "recipients"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.String(36), db.ForeignKey("generation_jobs.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="queued")
    error_message = db.Column(db.Text)

    job = db.relationship("GenerationJob", back_populates="recipients")
