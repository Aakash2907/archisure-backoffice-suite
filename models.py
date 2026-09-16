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