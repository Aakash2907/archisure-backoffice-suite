"""
ArchiSure Back-Office Suite — entrypoint.
Local run:  python app.py   (see README.md)
Serverless (e.g. Vercel): this module exposes a top-level `app` WSGI object.
"""
import os

from flask import Flask, send_from_directory

from api import api_bp
from auth import auth_bp
from models import db
from seed import seed

_db_initialized = False


def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')

    # On Vercel (or any read-only filesystem) only /tmp is writable.
    if os.environ.get('DATABASE_URL'):
        db_uri = os.environ['DATABASE_URL']
    elif os.environ.get('VERCEL'):
        db_uri = 'sqlite:////tmp/archisure.db'
    else:
        db_uri = 'sqlite:///archisure.db'

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET', 'dev-secret-change-me')

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    # Create tables and seed demo data lazily, on first request rather than at
    # import time — a failure here must not crash the module import, which is
    # what serverless platforms look for a top-level `app` object in.
    @app.before_request
    def _init_db_once():
        global _db_initialized
        if not _db_initialized:
            db.create_all()
            seed()
            _db_initialized = True

    return app


# Top-level WSGI app object — required by Vercel's Python runtime
# (and any other WSGI host looking for `app`/`application`/`handler`).
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
