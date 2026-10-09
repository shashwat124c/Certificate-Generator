import json

from flask import Blueprint, jsonify, request

from .extensions import db
from .models import GenerationJob, Recipient
from .validation import validate_generation_payload


api = Blueprint("api", __name__)


@api.post("/jobs")
def create_job():
    payload = request.get_json(silent=True)
    errors = validate_generation_payload(payload)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    certificate = payload["certificate"]
    job = GenerationJob(
        total_count=len(payload["recipients"]),
        certificate_data=json.dumps(
            {
                "title": certificate["title"].strip(),
                "course": certificate["course"].strip(),
                "issued_on": certificate["issued_on"].strip(),
                "issuer": certificate.get("issuer", "").strip(),
            }
        ),
    )
    for recipient in payload["recipients"]:
        job.recipients.append(
            Recipient(
                name=recipient["name"].strip(),
                email=recipient["email"].strip().lower(),
            )
        )

    db.session.add(job)
    db.session.commit()
    return jsonify({"job_id": job.id, "status": job.status, "total": job.total_count}), 202
