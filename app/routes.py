import json
from io import BytesIO

from flask import Blueprint, jsonify, request, send_file

from .extensions import db
from .models import GenerationJob, Recipient
from .services.certificates import render_certificate_pdf
from .validation import validate_generation_payload


api = Blueprint("api", __name__)


@api.post("/certificates/preview")
def preview_certificate():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("recipient"), dict):
        return (
            jsonify(
                {
                    "error": "Validation failed",
                    "details": ["recipient must be an object."],
                }
            ),
            400,
        )

    normalized_payload = {
        "certificate": payload.get("certificate"),
        "recipients": [payload["recipient"]],
    }
    errors = validate_generation_payload(normalized_payload)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    pdf_data = render_certificate_pdf(
        payload["recipient"]["name"].strip(),
        payload["certificate"],
    )
    return send_file(
        BytesIO(pdf_data),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="certificate.pdf",
    )


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
