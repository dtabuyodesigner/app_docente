import json
from app import app

def test_observaciones():
    app.config['TESTING'] = True
    client = app.test_client()

    print("Testing observations endpoints...")
    
    # Test POST
    print("\n1. Saving observation...")
    rv = client.post('/api/informe/observacion',
                     json={
                         "alumno_id": 11,
                         "trimestre": 2,
                         "texto": "El alumno muestra buena actitud y progreso notable."
                     },
                     content_type='application/json')
    print(f"Status: {rv.status_code}")
    print(f"Response: {rv.data.decode('utf-8')}")
    
    # Test GET
    print("\n2. Retrieving observation...")
    rv = client.get('/api/informe/observacion?alumno_id=11&trimestre=2')
    print(f"Status: {rv.status_code}")
    data = json.loads(rv.data)
    print(f"Response: {data}")
    print(f"Observation text: {data['texto']}")

if __name__ == "__main__":
    test_observaciones()
