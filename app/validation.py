import re
from datetime import date


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_generation_payload(payload):
    """Return a list of request errors; an empty list means the payload is valid."""
    if not isinstance(payload, dict):
        return ["Request body must be a JSON object."]

    errors = []
    certificate = payload.get("certificate")
    recipients = payload.get("recipients")

    if not isinstance(certificate, dict):
        errors.append("certificate must be an object.")
    else:
        for field in ("title", "course", "issued_on"):
            value = certificate.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"certificate.{field} is required.")
        issued_on = certificate.get("issued_on")
        if isinstance(issued_on, str) and issued_on.strip():
            try:
                date.fromisoformat(issued_on)
            except ValueError:
                errors.append("certificate.issued_on must use YYYY-MM-DD format.")
        issuer = certificate.get("issuer")
        if issuer is not None and not isinstance(issuer, str):
            errors.append("certificate.issuer must be a string.")

    if not isinstance(recipients, list) or not recipients:
        errors.append("recipients must be a non-empty list.")
    else:
        for index, recipient in enumerate(recipients):
            label = f"recipients[{index}]"
            if not isinstance(recipient, dict):
                errors.append(f"{label} must be an object.")
                continue

            name = recipient.get("name")
            email = recipient.get("email")
            if not isinstance(name, str) or not name.strip():
                errors.append(f"{label}.name is required.")
            if not isinstance(email, str) or not EMAIL_PATTERN.fullmatch(email.strip()):
                errors.append(f"{label}.email must be a valid email address.")

    return errors
