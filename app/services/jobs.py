import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .certificates import render_certificate_pdf


executor = ThreadPoolExecutor(max_workers=2)


def submit_job(app, job_id):
    """Schedule a committed job for processing in this application process."""
    executor.submit(process_job, app, job_id)


def process_job(app, job_id):
    """Generate each queued certificate, isolating failures per recipient."""
    # Import here to keep the service independent of application initialization.
    from ..extensions import db
    from ..models import GenerationJob

    with app.app_context():
        job = db.session.get(GenerationJob, job_id)
        if job is None or job.status != "queued":
            return

        job.status = "running"
        recipients = [recipient for recipient in job.recipients if recipient.status == "queued"]
        certificate_data = json.loads(job.certificate_data)
        db.session.commit()

        job_directory = Path(app.config["CERTIFICATE_STORAGE_PATH"]) / job.id
        for recipient in recipients:
            recipient.status = "running"
            db.session.commit()

            output_path = job_directory / f"{recipient.id}.pdf"
            temporary_path = output_path.with_suffix(".pdf.tmp")
            try:
                pdf_data = render_certificate_pdf(recipient.name, certificate_data)
                job_directory.mkdir(parents=True, exist_ok=True)
                temporary_path.write_bytes(pdf_data)
                os.replace(temporary_path, output_path)
                recipient.status = "completed"
                job.success_count += 1
            except Exception as error:
                temporary_path.unlink(missing_ok=True)
                recipient.status = "failed"
                recipient.error_message = str(error)
                job.failure_count += 1

            db.session.commit()

        if job.failure_count == 0:
            job.status = "completed"
        elif job.success_count == 0:
            job.status = "failed"
        else:
            job.status = "partial"
        db.session.commit()
