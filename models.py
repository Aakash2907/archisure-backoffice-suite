"""
Data model for the ArchiSure Back-Office Suite CRM/Policy/Financial platform.
Each class below is the DB implementation of an ArchiMate element from the
source flowchart (see README.md traceability table).
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # admin | crm_manager | policy_officer | finance_manager | customer
    role = db.Column(db.String(32), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(32))
    satisfaction_score = db.Column(db.Float, default=80.0)
    retained = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    devices = db.relationship('SmartDevice', backref='customer', lazy=True,
                               cascade='all, delete-orphan')
    behaviors = db.relationship('CustomerBehavior', backref='customer', lazy=True,
                                 cascade='all, delete-orphan')
    policies = db.relationship('Policy', backref='customer', lazy=True,
                                cascade='all, delete-orphan')


class SmartDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    device_type = db.Column(db.String(64))
    status = db.Column(db.String(32), default='active')
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)


class CustomerBehavior(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    action = db.Column(db.String(64))
    service = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Policy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product = db.Column(db.String(64))
    premium = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(32), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    renewal_date = db.Column(db.DateTime)

    payments = db.relationship('Payment', backref='policy', lazy=True,
                                cascade='all, delete-orphan')


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)


class Revenue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(64))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)


class Cost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(32))  # personnel | maintenance | other
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)
