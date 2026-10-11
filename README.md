# Bulk Certificate Generator

## Current milestone: background bulk generation

The Flask app exposes a health endpoint, accepts validated bulk job requests, renders a single certificate PDF, and processes saved jobs in a background thread pool. Each recipient is handled independently: a generation failure is recorded and processing continues for the rest of the job. Job status and per-recipient outcomes are stored in SQLite; the status endpoint is the next milestone.

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

After returning the response, the app generates one PDF per recipient under `instance/certificates/<job_id>/`. Set `CERTIFICATE_STORAGE_PATH` to choose another storage directory. The built-in thread pool is process-local and suited to this assignment's single-instance deployment; a multi-instance production deployment should use a durable queue.

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
