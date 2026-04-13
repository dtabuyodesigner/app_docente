import pytest
import os
import tempfile

# SECRET_KEY required for app.py
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"

from app import app as flask_app
from utils.db import get_db

@pytest.fixture
def app():
    # Setup temporary database
    db_fd, db_path = tempfile.mkstemp()
    os.environ["DATABASE_PATH"] = db_path
    
    flask_app.config.update({
        "TESTING": True,
        "DATABASE": db_path,
        "WTF_CSRF_ENABLED": False,
    })

    # Initialize DB (Simple version for tests)
    with flask_app.app_context():
        db = get_db()
        with open("schema.sql") as f:
            db.executescript(f.read())

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
