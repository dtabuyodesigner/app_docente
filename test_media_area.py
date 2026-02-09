import json
from app import app, get_db

def test_media_area():
    app.config['TESTING'] = True
    client = app.test_client()

    print("Testing /api/evaluacion/media_area...")
    # Using Alumno 11, Area 1, Trimestre 2 as a sample.
    # We expect HTTP 200 and a JSON with 'media' key.
    rv = client.get('/api/evaluacion/media_area?alumno_id=11&area_id=1&trimestre=2')
    
    print(f"Status: {rv.status_code}")
    print(f"Response: {rv.data.decode('utf-8')}")
    
    if rv.status_code == 200:
        data = json.loads(rv.data)
        if "media" in data:
            print(f"Media Area received: {data['media']}")
        else:
            print("Error: 'media' key missing")
    else:
        print("Request failed")

if __name__ == "__main__":
    test_media_area()
