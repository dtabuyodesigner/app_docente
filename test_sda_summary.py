import json
from app import app

def test_resumen_sda_todos():
    app.config['TESTING'] = True
    client = app.test_client()

    print("Testing /api/evaluacion/resumen_sda_todos...")
    # Using Alumno 11, Trimestre 2
    rv = client.get('/api/evaluacion/resumen_sda_todos?alumno_id=11&trimestre=2')
    
    print(f"Status: {rv.status_code}")
    print(f"Response: {rv.data.decode('utf-8')}")
    
    if rv.status_code == 200:
        data = json.loads(rv.data)
        if isinstance(data, list):
            print(f"SDA summary received with {len(data)} SDAs.")
            for item in data:
                print(f" - {item['area']} > {item['sda']}: {item['media']}")
        else:
            print("Error: Response is not a list")
    else:
        print("Request failed")

if __name__ == "__main__":
    test_resumen_sda_todos()
