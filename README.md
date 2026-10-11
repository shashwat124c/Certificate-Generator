# Bulk Certificate Generator

A Flask API that accepts one bulk certificate request, validates its recipients, generates one PDF per person, and reports the result of each generation.

The project includes a React interface for submitting batches, watching progress, and downloading certificates.

## Requirements

- Python 3.10 or newer
- pip

## Setup

From the project directory, create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, activate the environment with `source .venv/bin/activate`.

## Run the application

```powershell
python run.py
```

The API runs at `http://127.0.0.1:5000`. Check that it is available with `GET /health`; the response is `{"status":"ok"}`.

## Run the React frontend

Keep the Flask API running, then open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local address printed by Vite, usually `http://localhost:5173`. During local development, Vite forwards `/api` requests to Flask at `http://127.0.0.1:5000`. To use another backend address, set `API_PROXY_TARGET` before starting Vite.

## Run the tests

```powershell
python -m pytest
```

The tests cover health, job creation, input validation, PDF generation, job progress, an individual generation failure, and certificate downloads.

## Create a bulk generation job

Send `POST /api/v1/jobs` with JSON like this:

```json
{
  "certificate": {
    "title": "Certificate of Completion",
    "course": "Flask Backend Development",
    "issued_on": "2026-10-11",
    "issuer": "CertGen Academy"
  },
  "recipients": [
    {"name": "Ada Lovelace", "email": "ada@example.com"},
    {"name": "Grace Hopper", "email": "grace@example.com"}
  ]
}
```

Example PowerShell request:

```powershell
$payload = @{
  certificate = @{
    title = "Certificate of Completion"
    course = "Flask Backend Development"
    issued_on = "2026-10-11"
    issuer = "CertGen Academy"
  }
  recipients = @(
    @{ name = "Ada Lovelace"; email = "ada@example.com" },
    @{ name = "Grace Hopper"; email = "grace@example.com" }
  )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/v1/jobs `
  -ContentType "application/json" -Body $payload
```

The API returns HTTP `202` with a `job_id`. It rejects malformed certificate fields, invalid dates, and missing or invalid recipient details with HTTP `400` and a list of errors. Every valid job is queued for background processing.

## Check progress

Poll `GET /api/v1/jobs/<job_id>`. The response includes the job status, percent complete, successful and failed counts, and each recipient's status. Job statuses are `queued`, `running`, `completed`, `partial`, or `failed`. Recipient statuses are `queued`, `running`, `completed`, or `failed`.

## Download certificates

Each completed recipient in the job response includes a `download_url`. Request that URL to download the PDF. A certificate that is still processing or failed is not downloadable. Unknown jobs and recipients return HTTP `404`.

## Preview one certificate

For a single PDF preview, send `POST /api/v1/certificates/preview` with a `certificate` object and one `recipient` object. The response is a PDF file.

## Storage and design decisions

- Flask with an application factory keeps startup and configuration straightforward.
- SQLite is the default relational database. Set `DATABASE_URL` to use another SQLAlchemy-supported database.
- Generated PDFs are stored under `instance/certificates/<job_id>/`. Set `CERTIFICATE_STORAGE_PATH` to change this location.
- One fixed ReportLab template is used for all recipients.
- A process-local thread pool keeps this assignment self-contained. Each recipient is processed independently, and one failure does not stop the remaining recipients. For multiple application instances or durable recovery after restarts, replace it with a task queue such as Celery or RQ.
- For deployment with this in-process worker, run a single application worker and use persistent storage for the database and generated PDFs.

## Deploy on Render

The repository includes a Render Blueprint in `render.yaml`. From the Render dashboard, create a Blueprint and connect this GitHub repository. The Blueprint builds the Python app, starts it with Gunicorn, checks `/health`, and mounts persistent storage at `/var/data` for SQLite and generated PDFs.

This configuration uses Render's Starter web service and a 1 GB persistent disk. Render does not support persistent disks on free web services, so this setup is paid. Check the current Render pricing before creating the service. The app is configured as one instance with one Gunicorn worker because its SQLite database and background thread pool are local to that instance.
