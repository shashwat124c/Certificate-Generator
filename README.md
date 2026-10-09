# Bulk Certificate Generator

## Step 1: Flask foundation

This milestone sets up the Flask application and a health endpoint. The job, database, and certificate modules from the initial draft remain in the project for later milestones; they are not connected to the running app yet.

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
