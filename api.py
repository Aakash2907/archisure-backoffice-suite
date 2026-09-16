"""
REST API. One blueprint keeps the repo small; routes are grouped by the
business capability they implement (see README traceability table).
"""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from auth import login_required
from models import (Cost, Customer, CustomerBehavior, Payment, Policy,
                     Revenue, SmartDevice, db)

api_bp = Blueprint('api', __name__, url_prefix='/api')


# ---------- helpers ----------
def serialize_customer(c, detail=False):
    data = {
        'id': c.id, 'name': c.name, 'email': c.email, 'phone': c.phone,
        'satisfaction_score': c.satisfaction_score, 'retained': c.retained,
        'created_at': c.created_at.isoformat(),
    }
    if detail:
        data['devices'] = [{'id': d.id, 'type': d.device_type, 'status': d.status}
                            for d in c.devices]
        data['policies'] = [{'id': p.id, 'product': p.product, 'premium': p.premium,
                              'status': p.status} for p in c.policies]
        recent = sorted(c.behaviors, key=lambda x: x.timestamp, reverse=True)[:20]
        data['recent_behavior'] = [{'action': b.action, 'service': b.service,
                                     'timestamp': b.timestamp.isoformat()} for b in recent]
    return data


def serialize_policy(p):