import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_flexible_input():
    print("Testing Flexible Subject Input...")
    
    # Simulate data sent by frontend
    entry = {
        "dia": 1, 
        "hora_inicio": "10:00", 
        "hora_fin": "11:00",
        "asignatura": "Matemáticas - 5º Primaria", # Combined string
        "detalles": "Aula 2",
        "tipo": "clase"
    }
    
    # Save
    print("Saving Entry...")
    res = requests.post(f"{BASE_URL}/horario/manual", json=entry)
    if res.status_code != 200:
        print(f"Failed to save: {res.text}")
        return

    # Retrieve
    print("Verifying Retrieval...")
    res = requests.get(f"{BASE_URL}/horario?tipo=clase")
    data = res.json()
    
    found = False
    for e in data['manual']:
        if e['asignatura'] == "Matemáticas - 5º Primaria":
            found = True
            print(f"Found entry: {e}")
            break
            
    if found:
        print("PASS: Entry saved and retrieved correctly.")
    else:
        print("FAIL: Entry not found.")

if __name__ == "__main__":
    test_flexible_input()
