import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_custom_schedule_config():
    print("Testing Custom Schedule Config...")

    # 1. Get initial config (should be default)
    res = requests.get(f"{BASE_URL}/horario")
    assert res.status_code == 200
    data = res.json()
    assert "config" in data
    print("Initial config retrieved.")

    # 2. Set new config
    new_rows = [
        {"start": "08:30", "end": "09:25"},
        {"start": "09:25", "end": "10:20"},
        {"start": "10:20", "end": "11:15"}
    ]
    
    res = requests.post(f"{BASE_URL}/horario/config", json={"rows": new_rows})
    assert res.status_code == 200
    assert res.json()["ok"] is True
    print("New config saved.")

    # 3. Verify new config
    res = requests.get(f"{BASE_URL}/horario")
    data = res.json()
    config = data["config"]
    assert len(config) == 3
    assert config[0]["start"] == "08:30"
    assert config[0]["end"] == "09:25"
    print("New config verified.")

    # 4. Create an entry in the new slot
    entry_payload = {
        "dia": 0,
        "hora_inicio": "08:30",
        "hora_fin": "09:25",
        "asignatura": "Custom Start",
        "detalles": "Testing custom slot"
    }
    res = requests.post(f"{BASE_URL}/horario/manual", json=entry_payload)
    assert res.status_code == 200
    
    # 5. Verify entry retrieval
    res = requests.get(f"{BASE_URL}/horario")
    entries = res.json()["manual"]
    # Check if entry with 08:30 exists
    entry = next((e for e in entries if e["hora_inicio"] == "08:30"), None)
    assert entry is not None
    assert entry["asignatura"] == "Custom Start"
    print("Entry with custom time verified.")
    
    # Clean up entry
    requests.delete(f"{BASE_URL}/horario/manual/{entry['id']}")
    print("Entry cleaned up.")

    print("Custom Schedule Config Verified ✅")

if __name__ == "__main__":
    try:
        test_custom_schedule_config()
    except Exception as e:
        print(f"\nTEST FAILED ❌: {e}")
