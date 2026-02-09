import requests
import os

BASE_URL = "http://localhost:5000/api"

def test_schedule_manual():
    print("Testing Schedule Manual Entries...")
    
    # 1. Create Entry
    payload = {
        "dia": 0, # Lunes
        "hora_inicio": "09:00",
        "hora_fin": "10:00",
        "asignatura": "Matemáticas Test",
        "detalles": "Aula 101"
    }
    res = requests.post(f"{BASE_URL}/horario/manual", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    entry_id = data["id"]
    print(f"Created entry ID: {entry_id}")

    # 2. Get Schedule
    res = requests.get(f"{BASE_URL}/horario")
    assert res.status_code == 200
    schedule = res.json()["manual"]
    entry = next((e for e in schedule if e["id"] == entry_id), None)
    assert entry is not None
    assert entry["asignatura"] == "Matemáticas Test"
    print("Entry verified in schedule.")

    # 3. Delete Entry
    res = requests.delete(f"{BASE_URL}/horario/manual/{entry_id}")
    assert res.status_code == 200
    print("Entry deleted.")

    # 4. Verify Deletion
    res = requests.get(f"{BASE_URL}/horario")
    schedule = res.json()["manual"]
    entry = next((e for e in schedule if e["id"] == entry_id), None)
    assert entry is None
    print("Deletion verified.")

def test_schedule_image():
    print("\nTesting Schedule Image Upload...")
    
    # Create dummy image
    with open("test_schedule.jpg", "wb") as f:
        f.write(os.urandom(1024))

    with open("test_schedule.jpg", "rb") as f:
        files = {'foto': f}
        res = requests.post(f"{BASE_URL}/horario/upload", files=files)
    
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    filename = data["imagen"]
    print(f"Schedule image uploaded: {filename}")

    # Verify Get
    res = requests.get(f"{BASE_URL}/horario")
    assert res.json()["imagen"] == filename
    print("Schedule image verified.")
    
    # Cleanup
    if os.path.exists(f"static/uploads/{filename}"):
        os.remove(f"static/uploads/{filename}")
    os.remove("test_schedule.jpg")

def test_dining_menu():
    print("\nTesting Dining Menu Upload...")
    
    # Create dummy image
    with open("test_menu.jpg", "wb") as f:
        f.write(os.urandom(1024))

    with open("test_menu.jpg", "rb") as f:
        files = {'foto': f}
        res = requests.post(f"{BASE_URL}/comedor/menu/upload", files=files)
    
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    filename = data["imagen"]
    print(f"Menu image uploaded: {filename}")

    # Verify Get
    res = requests.get(f"{BASE_URL}/comedor/menu")
    assert res.json()["imagen"] == filename
    print("Menu image verified.")
    
    # Cleanup
    if os.path.exists(f"static/uploads/{filename}"):
        os.remove(f"static/uploads/{filename}")
    os.remove("test_menu.jpg")

if __name__ == "__main__":
    try:
        test_schedule_manual()
        test_schedule_image()
        test_dining_menu()
        print("\nALL TESTS PASSED ✅")
    except Exception as e:
        print(f"\nTEST FAILED ❌: {e}")
        import traceback
        traceback.print_exc()
