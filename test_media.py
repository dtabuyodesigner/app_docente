import json
from app import app

def test_media():
    app.config['TESTING'] = True
    client = app.test_client()

    # We know Alumno=1, Area=1, SDA=1, Trimestre=2 has a grade (from previous step)
    # The grade was Level 4 -> Note 10.0
    
    print("Testing /api/evaluacion/media...")
    rv = client.get('/api/evaluacion/media?alumno_id=11&sda_id=5&trimestre=2')
    
    print(f"Status: {rv.status_code}")
    print(f"Response: {rv.data.decode('utf-8')}")
    
    if rv.status_code == 200:
        data = json.loads(rv.data)
        if "media" in data:
            print(f"Media received: {data['media']}")
        else:
            print("Error: 'media' key missing")
    else:
        print("Request failed")

if __name__ == "__main__":
    test_media()
