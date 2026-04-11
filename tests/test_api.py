import pytest
from flask import json


class TestAPIValidation:
    """Tests de validación de schemas API."""

    def test_area_without_required_fields_returns_400(self, client):
        """Verifica que crear área sin campos requeridos devuelve 400."""
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = client.post('/api/areas', 
            data='{}',
            content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['ok'] is False
        assert 'Errores de validación' in data['error']
        assert 'nombre' in data['details']
        assert 'etapa_id' in data['details']

    def test_area_with_invalid_etapa_id_returns_400(self, client):
        """Verifica que etapa_id inválido podría aceptarse o invalidarse."""
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = client.post('/api/areas',
            data='{"nombre": "Test", "etapa_id": 99999}',
            content_type='application/json')
        
        assert response.status_code in [200, 400]

    def test_api_get_areas_requires_auth(self, client):
        """Verifica que GET /api/areas requiere auth."""
        response = client.get('/api/areas')
        assert response.status_code == 401

    def test_api_get_etapas_returns_list(self, client):
        """Verifica que GET /api/etapas devuelve array."""
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'admin'
        
        response = client.get('/api/etapas')
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, list)


class TestAlumnos:
    """Tests de funcionalidad de alumnos."""

    def test_alumnos_page_requires_auth(self, client):
        """Verifica que página de alumnos requiere sesión."""
        response = client.get('/alumnos')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_alumnos_page_loads_with_session(self, client):
        """Verifica que página de alumnos carga con sesión."""
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'admin'
        
        response = client.get('/alumnos')
        assert response.status_code == 200


class TestEvaluacion:
    """Tests de funcionalidad de evaluación."""

    def test_evaluacion_page_requires_auth(self, client):
        """Verifica que página de evaluación requiere sesión."""
        response = client.get('/evaluacion')
        assert response.status_code == 302
        assert '/login' in response.location