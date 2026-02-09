import requests

BASE_URL = "http://localhost:5000/api"

def reproduce_issue():
    # 1. Create entry with dia as string "0"
    payload = {
        "dia": "0", # String!
        "hora_inicio": "09:00",
        "hora_fin": "10:00",
        "asignatura": "Test String Dia",
        "detalles": "Testing"
    }
    
    print(f"Sending payload: {payload}")
    res = requests.post(f"{BASE_URL}/horario/manual", json=payload)
    print(f"Save status: {res.status_code}")
    print(f"Save response: {res.text}")
    
    if res.status_code != 200:
        print("Failed to save.")
        return

    # 2. Retrieve and check type
    res = requests.get(f"{BASE_URL}/horario")
    data = res.json()
    manual_entries = data["manual"]
    
    entry = next((e for e in manual_entries if e["asignatura"] == "Test String Dia"), None)
    
    if entry:
        print(f"Entry found: {entry}")
        print(f"Type of 'dia': {type(entry['dia'])}")
        
        if isinstance(entry['dia'], int):
             print("Dia is Integer (Good)")
        else:
             print("Dia is String (BAD)")
             
        # Cleanup
        requests.delete(f"{BASE_URL}/horario/manual/{entry['id']}")
    else:
        print("Entry NOT found!")

if __name__ == "__main__":
    reproduce_issue()
