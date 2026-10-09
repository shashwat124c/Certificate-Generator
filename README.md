# Bulk Certificate Generator

## Current milestone: single certificate PDF

The Flask app exposes a health endpoint, accepts validated bulk job requests, and can render one certificate PDF using a fixed template. Bulk job execution and progress updates are upcoming milestones.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

```powershell
python run.py
```

The server starts at `http://127.0.0.1:5000`. Check the health endpoint at:

```text
GET http://127.0.0.1:5000/health
```

Expected response:

```json
{"status": "ok"}
```

## Create a job

Send `POST /api/v1/jobs` with certificate details and at least one recipient:

```json
{
  "certificate": {
    "title": "Certificate of Completion",
    "course": "Flask Backend Development",
    "issued_on": "2026-10-09",
    "issuer": "CertGen Academy"
  },
  "recipients": [
    {"name": "Ada Lovelace", "email": "ada@example.com"}
  ]
}
```

The API checks required fields, the date format, and recipient email addresses. Invalid requests return HTTP `400` with a list of validation errors. Valid requests are saved and return HTTP `202` with a `job_id` and `queued` status.

Set `DATABASE_URL` to use another SQLAlchemy-supported relational database. By default, the app stores its SQLite database at `instance/certificates.db`.

## Preview one certificate

Send `POST /api/v1/certificates/preview` with one recipient and the certificate details. The response is a downloadable PDF.

```json
{
  "certificate": {
    "title": "Certificate of Completion",
    "course": "Flask Backend Development",
    "issued_on": "2026-10-09",
    "issuer": "CertGen Academy"
  },
  "recipient": {"name": "Ada Lovelace", "email": "ada@example.com"}
}
```
