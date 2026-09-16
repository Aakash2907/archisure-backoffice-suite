"""Minimal smoke tests. Run with: pytest test_app.py"""
import os
import tempfile

import pytest


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c
    os.close(db_fd)
    os.unlink(db_path)


def login(client, username='admin', password='admin123'):
    res = client.post('/api/auth/login', json={'username': username, 'password': password})
    assert res.status_code == 200
    return res.get_json()['token']


def test_login_success(client):
    token = login(client)
    assert token


def test_login_failure(client):
    res = client.post('/api/auth/login', json={'username': 'admin', 'password': 'wrong'})
    assert res.status_code == 401


def test_dashboard_requires_auth(client):
    res = client.get('/api/dashboard')
    assert res.status_code == 401


def test_dashboard_with_auth(client):
    token = login(client)
    res = client.get('/api/dashboard', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    data = res.get_json()
    assert 'revenue' in data and 'profit' in data


def test_customers_list(client):
    token = login(client)
    res = client.get('/api/customers', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    assert res.get_json()['total'] > 0


def test_role_restriction(client):
    token = login(client, 'customer1', 'customer123')
    res = client.get('/api/costs', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 403


def test_risk_score(client):
    token = login(client)
    res = client.get('/api/insurance/risk/1', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    assert 0 <= res.get_json()['risk_score'] <= 100
