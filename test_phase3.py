import requests

try:
    print("Testing /api/alumnos/progreso/1")
    r = requests.get("http://localhost:5000/api/alumnos/progreso/1")
    print("Status:", r.status_code)

    print("\nTesting /api/observaciones/1")
    r = requests.get("http://localhost:5000/api/observaciones/1")
    print("Status:", r.status_code)
    
    print("\nTesting /api/reuniones?tipo=PADRES")
    r = requests.get("http://localhost:5000/api/reuniones?tipo=PADRES")
    print("Status:", r.status_code)

except requests.exceptions.ConnectionError:
    print("Server not running on port 5000. Start it first.")
