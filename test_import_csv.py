import requests
import io
import csv

BASE_URL = "http://localhost:5000"

def test_csv_import():
    # 1. Download template
    print("Testing template download...")
    resp = requests.get(f"{BASE_URL}/api/alumnos/plantilla")
    if resp.status_code == 200:
        print("OK: Template downloaded.")
    else:
        print(f"FAIL: {resp.status_code}")
        return

    # 2. Prepare test CSV
    fieldnames = [
        "Nombre", 
        "Fecha Nacimiento", 
        "Dirección", 
        "Madre Nombre", 
        "Madre Teléfono", 
        "Padre Nombre", 
        "Padre Teléfono", 
        "Observaciones Generales", 
        "Personas Autorizadas",
        "Días Comedor (0-4 separados por comas)"
    ]
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow({
        "Nombre": "Alumno Importado 1",
        "Fecha Nacimiento": "2015-01-01",
        "Dirección": "Calle Test 123",
        "Madre Nombre": "Maria",
        "Madre Teléfono": "111",
        "Padre Nombre": "Juan",
        "Padre Teléfono": "222",
        "Observaciones Generales": "Obs test",
        "Personas Autorizadas": "Autorizado 1",
        "Días Comedor (0-4 separados por comas)": "0,2,4"
    })
    
    # 3. Upload CSV
    print("Testing CSV upload...")
    files = {'file': ('test.csv', output.getvalue(), 'text/csv')}
    resp = requests.post(f"{BASE_URL}/api/alumnos/importar", files=files)
    
    if resp.status_code == 200:
        res = resp.json()
        if res.get("ok"):
            print(f"OK: Imported {res.get('count')} students.")
        else:
            print(f"FAIL: {res.get('error')}")
    else:
        print(f"FAIL HTTP: {resp.status_code}")

if __name__ == "__main__":
    test_csv_import()
