import pytest

def login_client(client, role='admin'):
    """Auxiliar para loguear al cliente en los tests."""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['username'] = 'admin'
        sess['role'] = role


class TestSecurity:
    """Tests de seguridad básicos."""

    def test_api_requires_auth(self, client):
        """Verifica que endpoints API devuelven 401 sin sesión."""
        response = client.get('/api/areas')
        assert response.status_code == 401
        data = response.get_json()
        assert data['ok'] is False
        assert 'No autorizado' in data['error']

    def test_protected_route_redirect(self, client):
        """Verifica que rutas protegidas redirigen al login."""
        response = client.get('/alumnos')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_login_route_accessible(self, client):
        """Verifica que /login es accesible sin autenticación."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_static_files_accessible(self, client):
        """Verifica que archivos estáticos son accesibles sin auth."""
        response = client.get('/static/css/theme.css')
        assert response.status_code == 200

    def test_uploads_redirects_without_session(self, client):
        """Verifica que /uploads redirige sin sesión (por diseño, no es 404)."""
        response = client.get('/uploads/test.jpg')
        assert response.status_code == 302
        assert '/login' in response.location


class TestCSRFProtection:
    """Tests de protección CSRF."""

    def test_api_post_without_csrf_returns_400(self, client, app):
        """Verifica que POST API sin CSRF token devuelve error."""
        login_client(client)
        
        response = client.post('/api/areas', 
            data='{"nombre": "Test"}',
            content_type='application/json')
        assert response.status_code in [400, 401]

    @pytest.mark.skip(reason="CSRF token se genera en plantilla Jinja2, no en sesión")
    def test_session_has_csrf_token(self, client):
        """Verifica que la sesión incluye CSRF token tras request GET."""
        client.get('/login')
        with client.session_transaction() as sess:
            assert 'csrf_token' in sess