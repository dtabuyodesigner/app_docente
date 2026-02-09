import json
from app import app, get_db

def test_save_grade():
    app.config['TESTING'] = True
    client = app.test_client()

    # Payload matching what frontend sends (note strings vs ints)
    # Frontend sends strings for IDs because they come from <select> value
    data = {
        "alumno_id": "1",
        "area_id": "1",
        "sda_id": "1",
        "criterio_id": 1, 
        "trimestre": 2,
        "nivel": 4
    }

    print(f"Sending data: {data}")

    try:
        rv = client.post('/api/evaluacion', json=data)
        print(f"Status Code: {rv.status_code}")
        print(f"Response: {rv.data.decode('utf-8')}")
        
        if rv.status_code == 200:
            print("Success! Checking DB...")
            with app.app_context():
                conn = get_db()
                cur = conn.cursor()
                cur.execute("""
                    SELECT * FROM evaluaciones 
                    WHERE alumno_id=1 AND area_id=1 AND sda_id=1 AND criterio_id=1
                """)
                row = cur.fetchone()
                print(f"DB Row: {row}")
                conn.close()
        else:
            print("Request failed.")

    except Exception as e:
        print(f"Exception: {e}")
        # Debug: list tables
        with app.app_context():
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            print(f"Tables in DB: {cur.fetchall()}")
            conn.close()

if __name__ == "__main__":
    test_save_grade()
