import os
import pytest
from utils.db import get_app_data_dir

def login_client(client):
    """Auxiliar para loguear al cliente en los tests."""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['username'] = 'admin'
        sess['role'] = 'admin'

def test_serve_uploads_route(client):
    """Verifica que la ruta /uploads/ sirve archivos correctamente."""
    login_client(client)
    
    uploads_dir = os.path.join(get_app_data_dir(), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    test_filename = "test_file_pytest.txt"
    test_content = "Hola Mundo Pytest"
    test_path = os.path.join(uploads_dir, test_filename)
    
    logos_dir = os.path.join(uploads_dir, "logos")
    logo_filename = "test_logo.txt"
    logo_path = os.path.join(logos_dir, logo_filename)
    
    with open(test_path, "w", encoding="utf-8") as f:
        f.write(test_content)
        
    try:
        # 2. Intentar acceder via la ruta de Flask
        response = client.get(f'/uploads/{test_filename}')
        
        # 3. Verificar respuesta
        assert response.status_code == 200
        assert response.data.decode('utf-8') == test_content
        
        # 4. Verificar subdirectorios (necesita <path:filename>)
        os.makedirs(logos_dir, exist_ok=True)
        with open(logo_path, "w") as f:
            f.write("CONTENIDO LOGO")
            
        response_logo = client.get(f'/uploads/logos/{logo_filename}')
        assert response_logo.status_code == 200
        assert response_logo.data.decode('utf-8') == "CONTENIDO LOGO"
        
    finally:
        # Limpiar
        if os.path.exists(test_path):
            os.remove(test_path)
        if os.path.exists(logo_path):
            os.remove(logo_path)

def test_serve_uploads_404(client):
    """Verifica que devuelve 404 para archivos inexistentes estando logueado."""
    login_client(client)
    response = client.get('/uploads/archivo_que_no_existe_123456.jpg')
    assert response.status_code == 404

def test_serve_uploads_redirect_if_not_logged_in(client):
    """Verifica que redirige al login si no hay sesión."""
    response = client.get('/uploads/cualquier_cosa.jpg')
    assert response.status_code == 302
    assert '/login' in response.location
