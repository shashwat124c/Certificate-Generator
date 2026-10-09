from flask import jsonify


def health():
    return jsonify({"status": "ok"})
