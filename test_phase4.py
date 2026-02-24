import requests

try:
    print("Testing /api/gestor_tareas (POST)")
    r1 = requests.post("http://localhost:5000/api/gestor_tareas", json={
        "titulo": "Corregir libretas de Lengua",
        "descripcion": "Revisar los ejercicios de la página 45",
        "prioridad": "alta",
        "fecha_limite": "2024-11-20"
    })
    print("Status:", r1.status_code, r1.json())
    new_id = r1.json().get('id')
    
    print("\nTesting /api/gestor_tareas (GET)")
    r2 = requests.get("http://localhost:5000/api/gestor_tareas")
    print("Status:", r2.status_code)
    print("Tasks count:", len(r2.json()))

except requests.exceptions.ConnectionError:
    print("Server not running on port 5000. Start it first.")
except Exception as e:
    print("Error:", e)
