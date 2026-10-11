# import json
# import urllib.error
# import urllib.request

# # req = urllib.request.Request(
# #     "http://127.0.0.1:5000/api/v1/jobs",
# #     data=json.dumps({
# #         "certificate": {
# #             "title": "Certificate of Completion",
# #             "course": "Flask Backend Development",
# #             "issued_on": "2026-10-09",
# #             "issuer": "CertGen Academy",
# #         },
# #         "recipients": [{"name": "Ada Lovelace", "email": "bad@email.com"}],
# #     }).encode("utf-8"),
# #     headers={"Content-Type": "application/json"},
# # )

# # try:
# #     with urllib.request.urlopen(req) as response:
# #         print(response.read().decode())
# # except urllib.error.HTTPError as e:
# #     print(f"Status Code: {e.code}")
# #     print(f"Server Response: {e.read().decode()}")

# req = urllib.request.Request(
#     "http://127.0.0.1:5000/api/v1/certificates/preview",
#     data=json.dumps({
#         "certificate": {
#             "title": "Certificate of Completion",
#             "course": "Flask Backend Development",
#             "issued_on": "2026-10-09",
#             "issuer": "CertGen Academy",
#         },
#         "recipient": {"name": "Ada Lovelace", "email": "ada@example.com"},
#     }).encode("utf-8"),
#     headers={"Content-Type": "application/json"},
# )

# try:
#     with urllib.request.urlopen(req) as response:
#         pdf_content = response.read()
#         with open("preview.pdf", "wb") as f:
#             f.write(pdf_content)
#         print("Success! Generated preview.pdf (size:", len(pdf_content), "bytes)")
# except urllib.error.HTTPError as e:
#     print(f"Status Code: {e.code}")
#     print(f"Server Response: {e.read().decode()}")

import json
import time
import urllib.request

BASE_URL = "http://127.0.0.1:5000"

# 1. Submit Bulk Job
payload = {
    "certificate": {
        "title": "Certificate of Completion",
        "course": "Flask Backend Development",
        "issued_on": "2026-10-09",
        "issuer": "CertGen Academy",
    },
    "recipients": [
        {"name": "Ada Lovelace", "email": "ada@example.com"},
        {"name": "Alan Turing", "email": "alan@example.com"},
    ],
}

req = urllib.request.Request(
    f"{BASE_URL}/api/v1/jobs",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    job_id = data["job_id"]
    print(f"Created Job ID: {job_id} (Status: {data['status']})")

# 2. Poll until job completes
while True:
    with urllib.request.urlopen(f"{BASE_URL}/api/v1/jobs/{job_id}") as resp:
        job_status = json.loads(resp.read().decode())
        print(f"Status: {job_status['status']} | Progress: {job_status['progress_percent']}%")
        if job_status["status"] in ("completed", "partial", "failed"):
            break
    time.sleep(0.5)

# 3. Download the first certificate
recipient = job_status["recipients"][0]
if recipient.get("download_url"):
    download_url = f"{BASE_URL}{recipient['download_url']}"
    with urllib.request.urlopen(download_url) as resp:
        pdf_bytes = resp.read()
        with open("downloaded_certificate.pdf", "wb") as f:
            f.write(pdf_bytes)
    print(f"Downloaded certificate for {recipient['name']} ({len(pdf_bytes)} bytes)")
