"""
ArchiSurance-Lite — entrypoint.
Run:  python app.py   (see README.md)
"""
import os

from flask import Flask, send_from_directory

from api import api_bp
from auth import auth_bp
from models import db
from seed import seed


def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///archisurance.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET', 'dev-secret-change-me')

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    with app.app_context():
        db.create_all()
        seed()

    return app

