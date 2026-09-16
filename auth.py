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
@wraps(f)
        def wrapped(*args, **kwargs):
            header = request.headers.get('Authorization', '')
            if not header.startswith('Bearer '):
                return jsonify({'error': 'missing bearer token'}), 401
            try:
                payload = decode_token(header.split(' ', 1)[1])
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'token expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'invalid token'}), 401
            if roles and payload['role'] not in roles and payload['role'] != 'admin':
                return jsonify({'error': 'forbidden for this role'}), 403
            request.user = payload
            return f(*args, **kwargs)
        return wrapped
    return decorator


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    user = User.query.filter_by(username=data.get('username', '')).first()
    if not user or not check_password_hash(user.password_hash, data.get('password', '')):
        return jsonify({'error': 'invalid credentials'}), 401
    return jsonify({
        'token': create_token(user),
        'username': user.username,
        'role': user.role,
        'customer_id': user.customer_id,
    })


@auth_bp.route('/api/auth/me', methods=['GET'])
@login_required()
def me():
    return jsonify(request.user)
