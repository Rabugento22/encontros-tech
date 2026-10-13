from flask import Blueprint, jsonify

from services import health_service
from core.database import get_db

bp = Blueprint('health', __name__)

@bp.route("/health", methods=['GET'])
def health():
    return jsonify(health_service.check_liveness())

@bp.route("/ready", methods=['GET'])
def ready():
    with get_db() as db:
        is_ready, reason = health_service.check_readiness(db)

    if is_ready:
        return jsonify({"status": "ready"})

    return jsonify({"status": "not ready", "reason": reason}), 503
