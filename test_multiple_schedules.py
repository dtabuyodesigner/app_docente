import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_multiple_schedules():
    print("Testing Multiple Schedules...")
    
    # 1. Define distinct entries for same slot
    class_entry = {
        "dia": 0, "hora_inicio": "09:00", "hora_fin": "10:00",
        "asignatura": "Matematicas (Clase)", "detalles": "Aula 1",
        "tipo": "clase"
    }
    
    prof_entry = {
        "dia": 0, "hora_inicio": "09:00", "hora_fin": "10:00",
        "asignatura": "Reunion (Profesor)", "detalles": "Sala Profesores",
        "tipo": "profesor"
    }
    
    # 2. Save Class Entry
    print("Saving Class Entry...")
    res = requests.post(f"{BASE_URL}/horario/manual", json=class_entry)
    if res.status_code != 200:
        print(f"Failed to save class entry: {res.text}")
        return
    
    # 3. Save Professor Entry
    print("Saving Professor Entry...")
    res = requests.post(f"{BASE_URL}/horario/manual", json=prof_entry)
    if res.status_code != 200:
        print(f"Failed to save professor entry: {res.text}")
        return

    # 4. Verify Independence
    print("Verifying Class Schedule...")
    res = requests.get(f"{BASE_URL}/horario?tipo=clase")
    data = res.json()
    found_class = any(e['asignatura'] == "Matematicas (Clase)" for e in data['manual'])
    found_prof_in_class = any(e['asignatura'] == "Reunion (Profesor)" for e in data['manual'])
    
    if found_class and not found_prof_in_class:
        print("PASS: Class schedule contains only class entries.")
    else:
        print(f"FAIL: Class schedule invalid. Found Class: {found_class}, Found Prof: {found_prof_in_class}")

    print("Verifying Professor Schedule...")
    res = requests.get(f"{BASE_URL}/horario?tipo=profesor")
    data = res.json()
    found_prof = any(e['asignatura'] == "Reunion (Profesor)" for e in data['manual'])
    found_class_in_prof = any(e['asignatura'] == "Matematicas (Clase)" for e in data['manual'])
    
    if found_prof and not found_class_in_prof:
        print("PASS: Professor schedule contains only professor entries.")
    else:
        print(f"FAIL: Professor schedule invalid. Found Prof: {found_prof}, Found Class: {found_class_in_prof}")

if __name__ == "__main__":
    test_multiple_schedules()
