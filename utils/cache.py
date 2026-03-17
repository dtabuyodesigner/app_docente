import time
from functools import wraps
from flask import request

# Diccionario para almacenar la caché en memoria (dict básico)
# Formato: { "clave": {"timestamp": 123456789.0, "data": (...) } }
_CACHE = {}

def simple_cache(timeout=300):
    """
    Decorador simple para cachear respuestas completas de Flask por un tiempo limitado.
    Usa la ruta de la petición y sus parámetros como clave del caché.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # No cachear si no es GET (por seguridad, aunque solo se aplique a endpoints de lectura)
            if request.method != 'GET':
                return f(*args, **kwargs)
                
            # Generar clave única: "/api/criterios?area_id=1&etapa=Primaria"
            cache_key = f"{request.path}?{request.query_string.decode('utf-8')}"
            
            # Verificar si existe en caché y si es válida
            cached_entry = _CACHE.get(cache_key)
            if cached_entry:
                timestamp = cached_entry.get("timestamp", 0)
                if (time.time() - timestamp) < timeout:
                    # Devolver valor de caché
                    return cached_entry.get("data")
                    
            # Si no está en caché o expiró, ejecutar la función real
            response = f(*args, **kwargs)
            
            # Solo guardamos en caché si la respuesta fue exitosa (código 200)
            if getattr(response, 'status_code', 200) == 200:
                _CACHE[cache_key] = {
                    "timestamp": time.time(),
                    "data": response
                }
                
            return response
        return decorated_function
    return decorator

def clear_cache():
    """Limpia todo el caché almacenado en memoria. Útil para invalidarlo desde test o tras updates masivos."""
    _CACHE.clear()
