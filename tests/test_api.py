from app.extensions import db
from app.models import GenerationJob, Recipient
from app.services.jobs import process_job


VALID_PAYLOAD = {
    "certificate": {
        "title": "Certificate of Completion",
        "course": "Flask Backend Development",
        "issued_on": "2026-10-11",
        "issuer": "CertGen Academy",
    },
    "recipients": [
        {"name": "Ada Lovelace", "email": "ada@example.com"},
        {"name": "Grace Hopper", "email": "grace@example.com"},
    ],
}


def create_job(client, payload=None):
    response = client.post("/api/v1/jobs", json=payload or VALID_PAYLOAD)
    assert response.status_code == 202
    return response.get_json()["job_id"]


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_create_job_saves_recipients(client, app):
    job_id = create_job(client)

    with app.app_context():
        job = db.session.get(GenerationJob, job_id)
        assert job.status == "queued"
        assert job.total_count == 2
        assert len(job.recipients) == 2
        assert job.recipients[0].email.endswith("@example.com")


def test_invalid_request_is_rejected(client):
    response = client.post(
        "/api/v1/jobs",
        json={
            "certificate": {"title": "", "course": "Course", "issued_on": "bad-date"},
            "recipients": [{"name": "", "email": "not-an-email"}],
        },
    )

    assert response.status_code == 400
    details = response.get_json()["details"]
    assert any("certificate.title" in item for item in details)
    assert any("issued_on" in item for item in details)
    assert not any("recipients[0]" in item for item in details)


def test_invalid_recipient_does_not_stop_valid_recipients(client, app, monkeypatch):
    import app.routes as routes

    monkeypatch.setattr(routes, "submit_job", lambda app, job_id: None)
    payload = {
        "certificate": VALID_PAYLOAD["certificate"],
        "recipients": [
            {"name": "Ada Lovelace", "email": "ada@example.com"},
            {"name": "Invalid Row", "email": "not-an-email"},
        ],
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.get_json()["job_id"]
    process_job(app, job_id)

    data = client.get(f"/api/v1/jobs/{job_id}").get_json()
    assert data["status"] == "partial"
    assert data["total"] == 2
    assert data["processed"] == 2
    assert data["successful"] == 1
    assert data["failed"] == 1
    good = next(item for item in data["recipients"] if item["email"] == "ada@example.com")
    bad = next(item for item in data["recipients"] if item["email"] == "not-an-email")
    assert good["status"] == "completed"
    assert good["download_url"]
    assert bad["status"] == "failed"
    assert "valid email address" in bad["error"]


def test_preview_generates_a_pdf(client):
    response = client.post(
        "/api/v1/certificates/preview",
        json={
            "certificate": VALID_PAYLOAD["certificate"],
            "recipient": VALID_PAYLOAD["recipients"][0],
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")


def test_job_status_reports_progress_after_processing(client, app):
    job_id = create_job(client)
    process_job(app, job_id)

    response = client.get(f"/api/v1/jobs/{job_id}")
    data = response.get_json()
    assert response.status_code == 200
    assert data["status"] == "completed"
    assert data["total"] == 2
    assert data["processed"] == 2
    assert data["successful"] == 2
    assert data["failed"] == 0
    assert data["progress_percent"] == 100
    assert all(item["status"] == "completed" for item in data["recipients"])


def test_one_recipient_failure_does_not_stop_job(client, app, monkeypatch):
    import app.services.jobs as job_service

    original_generator = job_service.render_certificate_pdf

    def fail_grace(name, certificate_data):
        if name == "Grace Hopper":
            raise RuntimeError("simulated PDF failure")
        return original_generator(name, certificate_data)

    monkeypatch.setattr(job_service, "render_certificate_pdf", fail_grace)
    job_id = create_job(client)
    process_job(app, job_id)

    data = client.get(f"/api/v1/jobs/{job_id}").get_json()
    assert data["status"] == "partial"
    assert data["successful"] == 1
    assert data["failed"] == 1
    failed = next(item for item in data["recipients"] if item["status"] == "failed")
    assert failed["error"] == "simulated PDF failure"
    assert failed["download_url"] is None


def test_successful_certificate_can_be_downloaded(client, app):
    job_id = create_job(client)
    process_job(app, job_id)
    job_data = client.get(f"/api/v1/jobs/{job_id}").get_json()
    download_url = job_data["recipients"][0]["download_url"]

    response = client.get(download_url)
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")


def test_unknown_job_and_certificate_return_not_found(client):
    assert client.get("/api/v1/jobs/missing").status_code == 404
    assert (
        client.get("/api/v1/jobs/missing/certificates/missing/download").status_code
        == 404
    )

