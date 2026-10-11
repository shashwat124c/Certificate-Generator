import json
from io import BytesIO
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file, url_for

from .extensions import db
from .models import GenerationJob, Recipient
from .services.certificates import render_certificate_pdf
from .services.jobs import submit_job
from .validation import (
    validate_generation_payload,
    validate_job_payload,
    validate_recipient,
)


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
    errors = validate_job_payload(payload)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    certificate = payload["certificate"]
    recipient_results = [
        (recipient, validate_recipient(recipient, index))
        for index, recipient in enumerate(payload["recipients"])
    ]
    job = GenerationJob(
        total_count=len(recipient_results),
        certificate_data=json.dumps(
            {
                "title": certificate["title"].strip(),
                "course": certificate["course"].strip(),
                "issued_on": certificate["issued_on"].strip(),
                "issuer": certificate.get("issuer", "").strip(),
            }
        ),
    )
    for index, (recipient, errors) in enumerate(recipient_results):
        if errors:
            name = recipient.get("name") if isinstance(recipient, dict) else None
            email = recipient.get("email") if isinstance(recipient, dict) else None
            job.recipients.append(
                Recipient(
                    name=name.strip()[:255] if isinstance(name, str) and name.strip() else f"Invalid row {index + 1}",
                    email=email.strip().lower()[:255] if isinstance(email, str) else "",
                    status="failed",
                    error_message="; ".join(errors),
                )
            )
            job.failure_count = (job.failure_count or 0) + 1
            continue

        job.recipients.append(
            Recipient(
                name=recipient["name"].strip(),
                email=recipient["email"].strip().lower(),
            )
        )

    db.session.add(job)
    db.session.commit()
    submit_job(current_app._get_current_object(), job.id)
    return jsonify({"job_id": job.id, "status": job.status, "total": job.total_count}), 202


@api.get("/jobs/<job_id>")
def get_job(job_id):
    job = db.session.get(GenerationJob, job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404

    processed_count = job.success_count + job.failure_count
    progress = round(processed_count / job.total_count * 100) if job.total_count else 0
    return jsonify(
        {
            "job_id": job.id,
            "status": job.status,
            "total": job.total_count,
            "processed": processed_count,
            "successful": job.success_count,
            "failed": job.failure_count,
            "progress_percent": progress,
            "recipients": [
                {
                    "recipient_id": recipient.id,
                    "name": recipient.name,
                    "email": recipient.email,
                    "status": recipient.status,
                    "error": recipient.error_message,
                    "download_url": (
                        url_for(
                            "api.download_certificate",
                            job_id=job.id,
                            recipient_id=recipient.id,
                        )
                        if recipient.status == "completed"
                        else None
                    ),
                }
                for recipient in job.recipients
            ],
        }
    )


@api.get("/jobs/<job_id>/certificates/<recipient_id>/download")
def download_certificate(job_id, recipient_id):
    recipient = db.session.get(Recipient, recipient_id)
    if recipient is None or recipient.job_id != job_id:
        return jsonify({"error": "Certificate not found"}), 404
    if recipient.status != "completed":
        return jsonify({"error": "Certificate is not available"}), 409

    file_path = (
        Path(current_app.config["CERTIFICATE_STORAGE_PATH"])
        / job_id
        / f"{recipient_id}.pdf"
    )
    if not file_path.is_file():
        return jsonify({"error": "Certificate file is missing"}), 404

    return send_file(
        file_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"certificate-{recipient_id}.pdf",
    )
