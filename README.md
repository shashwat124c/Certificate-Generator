# Bulk Certificate Generator

**Live demo:** [Open CertGen](http://13.233.136.216)

The application is deployed on a single AWS EC2 instance running Ubuntu 24.04. Nginx serves the React frontend and proxies API requests to Flask running under Gunicorn. A live smoke test generated two sample certificates successfully and displayed their download links.

The demo currently uses HTTP and the instance's public IP address; it has no custom domain or HTTPS. The public IP may change if the instance is stopped and started.

A Flask API for submitting bulk certificate-generation jobs. The application validates recipient rows, creates a personalized PDF for each valid recipient, tracks each row's result, and provides a download link for every successfully generated certificate. A React frontend is also included for submitting jobs, following progress, and downloading PDFs.

## Features completed

- Bulk certificate generation from one predefined ReportLab template.
- Recipient-specific certificate PDFs.
- Per-recipient validation and failure reporting.
- Mixed-validity batch handling: an invalid recipient does not cancel valid recipients. Invalid rows are marked failed with an explanation, while valid rows continue through generation and remain downloadable.
- Background processing with job-level progress and per-recipient statuses.
- PDF preview for a single recipient.
- React interface for creating jobs, checking progress, and downloading completed certificates.
- Automated tests for the main API and generation workflows.

## Requirements

- Python 3.10 or newer and pip
- Node.js and npm (only needed to run the React frontend)

## Set up the backend

From the project root, create and activate a virtual environment, then install the Python dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

## Run the backend

```bash
python run.py
```

The API is available at `http://127.0.0.1:5000`. Confirm it is running with:

```http
GET /health
```

The health endpoint returns `{"status":"ok"}`.

## Run the React frontend

Leave the backend running and open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite (typically `http://localhost:5173`). During local development, Vite forwards `/api` requests to the Flask server at `http://127.0.0.1:5000`. Set `API_PROXY_TARGET` if the backend runs at a different address.

## Submit a bulk generation job

Send a JSON request to `POST /api/v1/jobs`:

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

Example using PowerShell:

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

$job = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/v1/jobs `
  -ContentType "application/json" -Body $payload
$job
```

The API responds with HTTP `202 Accepted` and a `job_id`. Invalid certificate details or a missing/empty recipients list are rejected with HTTP `400`. Recipient data is checked row by row: invalid rows are reported as failed, but do not prevent valid rows in the same request from being generated. For example, if one recipient has an invalid email and another has a valid email, the valid recipient's certificate is still generated and can be downloaded.

## Check job progress and results

Poll `GET /api/v1/jobs/<job_id>` using the returned job ID:

```powershell
$jobId = $job.job_id
$status = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/jobs/$jobId"
$status
```

The response reports the total, processed, successful, and failed counts, the percentage complete, and each recipient's status and any error message. Job statuses are `queued`, `running`, `completed`, `partial`, or `failed`. Recipient statuses are `queued`, `running`, `completed`, or `failed`. A batch containing both successful and failed rows ends with `partial` status.

## Download generated certificates

Each completed recipient in the job status response has a `download_url`. Use that URL to retrieve the corresponding PDF:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:5000$($status.recipients[0].download_url)" `
  -OutFile "certificate.pdf"
```

Only successfully completed certificates are downloadable. A failed or still-processing recipient has no download link. Unknown jobs or certificates return HTTP `404`; a certificate that is not yet available returns HTTP `409`.

## Preview a single certificate

Send `POST /api/v1/certificates/preview` with a `certificate` object and one `recipient` object. A successful response is a PDF (`application/pdf`) downloaded as `certificate.pdf`.

## Run the tests

From the project root with the virtual environment activated:

```bash
python -m pytest
```

The test suite covers health checks, job creation, request and recipient validation, PDF preview and generation, job progress, per-recipient failure isolation (including a valid row alongside an invalid one), certificate downloads, and not-found responses.

## Design choices

- **Framework:** Flask was selected for the API, using an application factory and blueprints to keep setup and routes organized.
- **Database:** SQLite is the default relational database. Set `DATABASE_URL` to use another SQLAlchemy-supported database.
- **Certificate template:** All certificates use one predefined ReportLab template populated with the recipient's name and certificate details.
- **Batch validation:** Certificate-level errors prevent a job from being created. Recipient rows are validated independently; invalid rows are recorded as failed and valid rows continue. This keeps a single bad entry from blocking the rest of the batch.
- **Processing:** A process-local thread pool runs generation in the background so the API can return a job ID immediately. Each recipient is processed independently, and one generation error does not stop the remaining recipients. This keeps the assignment self-contained; durable queueing and recovery across process restarts would require a task queue such as Celery or RQ.
- **File storage:** Generated PDFs are stored under `instance/certificates/<job_id>/` by default. Set `CERTIFICATE_STORAGE_PATH` to change the location. The download endpoint serves these stored files.
