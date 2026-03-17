def test_inicio_redirect(client):
    """Verifica que la raíz redirija al login si no hay sesión."""
    response = client.get('/')
    # Como es una app con pywebview + Flask, a veces devuelve index.html directamente o redirige
    # Según require_auth en app.py: redirige a '/login' (main.login_page)
    assert response.status_code == 302
    assert response.location.endswith('/login')

def test_login_page_load(client):
    """Verifica que la página de login cargue correctamente."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Login" in response.data or b"Acceder" in response.data

def test_cache_functionality(client, app):
    """Verifica que el decorador simple_cache funciona y no rompe los endpoints."""
    # First request
    with app.test_request_context('/api/etapas'):
        response1 = client.get('/api/etapas')
        assert response1.status_code in [200, 401] # Depends on auth, we just check it doesn't crash 500
        
    # Second request (should hit cache if it was 200, or just not crash)
    with app.test_request_context('/api/etapas'):
        response2 = client.get('/api/etapas')
        assert response2.status_code == response1.status_code

def test_marshmallow_validation_area(client, app):
    """Verifica que la creación de área sin datos requeridos devuelva error de validación 400."""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['username'] = 'admin'
        sess['role'] = 'admin'
    
    # Enviar objeto vacío para forzar error de validación
    response = client.post('/api/areas', data='{}', content_type='application/json')
    print("RESPONSE STATUS:", response.status_code)
    print("RESPONSE BODY:", response.data)
    assert response.status_code == 400
    
    data = response.get_json()
    print("PAYLOAD ERROR:", data)
    assert data is not None
    assert data["ok"] is False
    assert "Errores de validación" in data["error"]
    assert "nombre" in data["details"]
    assert "etapa_id" in data["details"]
