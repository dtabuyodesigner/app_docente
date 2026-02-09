import requests
import os
import datetime

BASE_URL = "http://localhost:5000/api"

def test_dining_history():
    print("Testing Dining Menu History...")
    
    months = ["2023-11", "2023-12", "2024-01"]
    
    for mes in months:
        # Create dummy image
        fname = f"test_menu_{mes}.jpg"
        with open(fname, "wb") as f:
            f.write(os.urandom(1024))

        print(f"Uploading menu for {mes}...")
        with open(fname, "rb") as f:
            files = {'foto': f}
            data = {'mes': mes}
            res = requests.post(f"{BASE_URL}/comedor/menu/upload", files=files, data=data)
        
        assert res.status_code == 200
        assert res.json()["ok"] is True
        print(f"Uploaded {mes}")
        
        os.remove(fname)

    # Verify retrieval
    for mes in months:
        print(f"Retrieving menu for {mes}...")
        res = requests.get(f"{BASE_URL}/comedor/menu?mes={mes}")
        assert res.status_code == 200
        data = res.json()
        assert data["mes"] == mes
        assert "menu_comedor" in data["imagen"]
        assert mes in data["imagen"]
        print(f"Verified {mes}")

    print("Dining Menu History Verified ✅")

if __name__ == "__main__":
    try:
        test_dining_history()
    except Exception as e:
        print(f"\nTEST FAILED ❌: {e}")
