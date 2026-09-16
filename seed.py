"""
Seeds realistic mock data (customers, smart devices, behavior events, policies,
payments, revenue and cost records) so the dashboard works immediately.
"""
import random
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from models import (Cost, Customer, CustomerBehavior, Payment, Policy,
                     Revenue, SmartDevice, User, db)

NAMES = ['Alice Nguyen', 'Bob Smith', 'Carla Ruiz', 'David Kim', 'Elena Petrova',
         'Farid Khan', 'Grace Lee', 'Hassan Ali', 'Ivy Chen', 'Jack Brown',
         'Karen Wu', 'Liam OBrien', 'Mia Torres', 'Noah Davis', 'Olga Ivanova']
DEVICE_TYPES = ['Smart Car Tracker', 'Home Sensor', 'Wearable Health Monitor', 'Smart Thermostat']
PRODUCTS = ['Auto Insurance', 'Home Insurance', 'Life Insurance', 'Health Insurance']
ACTIONS = ['login', 'view_policy', 'file_claim', 'update_profile', 'contact_support', 'browse_offers']


def seed():
    if User.query.first():
        return  # already seeded

    for username, pw, role in [
        ('admin', 'admin123', 'admin'),
        ('crm_manager', 'crm123', 'crm_manager'),
        ('policy_officer', 'policy123', 'policy_officer'),
        ('finance_manager', 'finance123', 'finance_manager'),
    ]:
        db.session.add(User(username=username, password_hash=generate_password_hash(pw), role=role))

    customers = []
    for i, name in enumerate(NAMES):