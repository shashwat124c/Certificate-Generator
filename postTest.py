import json
import urllib.error
import urllib.request

req = urllib.request.Request(
    "http://127.0.0.1:5000/api/v1/jobs",
    data=json.dumps({
        "certificate": {
            "title": "Certificate of Completion",
            "course": "Flask Backend Development",
            "issued_on": "2026-10-09",
            "issuer": "CertGen Academy",
        },
        "recipients": [{"name": "Ada Lovelace", "email": "bad@email.com"}],
    }).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)

try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print(f"Status Code: {e.code}")
    print(f"Server Response: {e.read().decode()}")
