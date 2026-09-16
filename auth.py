"""
Authentication service (JWT) + role-based authorization decorator.
Implements: 'Common Use of Applications' -> shared Authentication service.
"""
import datetime
from functools import wraps

import jwt
from flask import Blueprint, current_app, jsonify, request
from werkzeug.security import check_password_hash

from models import User

auth_bp = Blueprint('auth', __name__)


def create_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'customer_id': user.customer_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8),
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm='HS256')


def decode_token(token):
    return jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])


def login_required(*roles):
    """Require a valid JWT. If roles are given, only those roles (or admin) may pass."""
    def decorator(f):