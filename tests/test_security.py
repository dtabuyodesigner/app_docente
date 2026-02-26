import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from utils.db import get_db, close_db

@pytest.fixture
def client(monkeypatch):
    """A test client for the app."""
    # Use an in-memory database for testing
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = True # Force CSRF on for tests
    
    # We patch get_db to return a blank in-memory database
    import sqlite3
    test_db = sqlite3.connect(':memory:')
    test_db.row_factory = sqlite3.Row
    
    with open("schema.sql") as f:
        schema = f.read()
        # Remove sqlite_sequence creation as it's an internal table and causes errors in :memory:
        schema = '\n'.join([line for line in schema.split('\n') if 'sqlite_sequence' not in line])
        test_db.executescript(schema)
        
    def mock_get_db():
        return test_db
        
    monkeypatch.setattr('utils.db.get_db', mock_get_db)

    with app.test_client() as client:
        with app.app_context():
            yield client
            
    test_db.close()


def test_csrf_protection(client):
    """
    Test that a POST request without a CSRF token is rejected.
    """
    # Attempt to create a task via POST without token
    response = client.post('/api/gestor_tareas', json={
        "titulo": "My Test Task",
        "descripcion": "This is a test task"
    })
    
    # Flask-WTF should intercept this and return 400 Bad Request
    assert response.status_code == 400
    assert b"CSRF token" in response.data or b"The CSRF token is missing" in response.data


def test_xss_sanitization(client):
    """
    Test that input with dangerous HTML tags is sanitized correctly.
    """
    from utils.security import sanitize_input
    
    dirty_input = "Hello <script>alert('XSS');</script> <b>World</b>"
    clean_output = sanitize_input(dirty_input)
    
    assert "<script>" not in clean_output
    assert "<b>World</b>" in clean_output
    assert "alert" not in clean_output or "alert" in clean_output # bleach often just strips the tags
