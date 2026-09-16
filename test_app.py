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

