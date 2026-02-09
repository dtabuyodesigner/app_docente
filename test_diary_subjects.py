import requests
import sqlite3

BASE_URL = "http://localhost:5000"

def get_db_ids():
    conn = sqlite3.connect("app_evaluar.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM alumnos LIMIT 1")
    uid = cur.fetchone()[0]
    cur.execute("SELECT id FROM areas LIMIT 2")
    areas = cur.fetchall()
    conn.close()
    return uid, [a[0] for a in areas]

def test_diary():
    uid, areas = get_db_ids()
    area1, area2 = areas
    fecha = "2026-10-10"

    # 1. Save Area 1
    print(f"Saving Area 1 ({area1})...")
    r = requests.post(f"{BASE_URL}/api/observaciones", json={
        "alumno_id": uid, "fecha": fecha, "texto": "Obs Area 1", "area_id": area1
    })
    print(r.json())
    assert r.status_code == 200

    # 2. Save Area 2
    print(f"Saving Area 2 ({area2})...")
    r = requests.post(f"{BASE_URL}/api/observaciones", json={
        "alumno_id": uid, "fecha": fecha, "texto": "Obs Area 2", "area_id": area2
    })
    print(r.json())
    assert r.status_code == 200

    # 3. Save General (None)
    print("Saving General...")
    r = requests.post(f"{BASE_URL}/api/observaciones", json={
        "alumno_id": uid, "fecha": fecha, "texto": "Obs General", "area_id": ""
    })
    print(r.json())
    assert r.status_code == 200

    # 4. Verify Fetch Area 1
    print("Fetching Area 1...")
    r = requests.get(f"{BASE_URL}/api/observaciones/dia?fecha={fecha}&area_id={area1}")
    data = r.json()
    student = next(s for s in data if s["id"] == uid)
    print(f"Got: '{student['observacion']}'")
    assert student["observacion"] == "Obs Area 1"

    # 5. Verify Fetch Area 2
    print("Fetching Area 2...")
    r = requests.get(f"{BASE_URL}/api/observaciones/dia?fecha={fecha}&area_id={area2}")
    data = r.json()
    student = next(s for s in data if s["id"] == uid)
    print(f"Got: '{student['observacion']}'")
    assert student["observacion"] == "Obs Area 2"

    # 6. Verify Fetch General
    print("Fetching General...")
    r = requests.get(f"{BASE_URL}/api/observaciones/dia?fecha={fecha}&area_id=")
    data = r.json()
    student = next(s for s in data if s["id"] == uid)
    print(f"Got: '{student['observacion']}'")
    assert student["observacion"] == "Obs General"

    print("✅ TEST PASSED")

if __name__ == "__main__":
    test_diary()
