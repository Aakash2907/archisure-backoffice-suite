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
        c = Customer(
            name=name,
            email=f"{name.split()[0].lower()}{i}@example.com",
            phone=f"+1-555-01{i:02d}",
            satisfaction_score=round(random.uniform(55, 98), 1),
            retained=random.random() > 0.15,
            created_at=datetime.utcnow() - timedelta(days=random.randint(30, 900)),
        )
        db.session.add(c)
        customers.append(c)
    db.session.flush()  # assign ids

    db.session.add(User(username='customer1', password_hash=generate_password_hash('customer123'),
                         role='customer', customer_id=customers[0].id))

    for c in customers:
        for _ in range(random.randint(1, 3)):
            db.session.add(SmartDevice(
                customer_id=c.id, device_type=random.choice(DEVICE_TYPES),
                status=random.choice(['active', 'active', 'inactive']),
                last_activity=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            ))
        for _ in range(random.randint(3, 10)):
            db.session.add(CustomerBehavior(
                customer_id=c.id, action=random.choice(ACTIONS), service=random.choice(PRODUCTS),
                timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 180)),
            ))
        for _ in range(random.randint(1, 2)):
            premium = round(random.uniform(50, 400), 2)
            p = Policy(
                customer_id=c.id, product=random.choice(PRODUCTS), premium=premium,
                status=random.choice(['active', 'active', 'pending', 'cancelled']),
                created_at=datetime.utcnow() - timedelta(days=random.randint(10, 700)),
                renewal_date=datetime.utcnow() + timedelta(days=random.randint(10, 365)),
            )
            db.session.add(p)
            db.session.flush()
            for m in range(random.randint(1, 6)):
                db.session.add(Payment(policy_id=p.id, amount=premium,
                                        date=datetime.utcnow() - timedelta(days=30 * m)))
            db.session.add(Revenue(source='premium', customer_id=c.id, amount=premium,
                                    date=datetime.utcnow() - timedelta(days=random.randint(0, 180))))

    for m in range(6):
        d = datetime.utcnow() - timedelta(days=30 * m)
        db.session.add(Cost(type='personnel', amount=round(random.uniform(8000, 12000), 2), date=d))
        db.session.add(Cost(type='maintenance', amount=round(random.uniform(2000, 5000), 2), date=d))
        db.session.add(Revenue(source='other', customer_id=None,
                                amount=round(random.uniform(1000, 3000), 2), date=d))

    db.session.commit()
