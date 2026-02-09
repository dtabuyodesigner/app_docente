import requests
import os

BASE_URL = "http://localhost:5000/api"

def test_photo_upload():
    # 1. Create a dummy student
    print("Creating student...")
    res = requests.post(f"{BASE_URL}/alumnos/nuevo", json={
        "nombre": "Test Student Photo",
        "no_comedor": 0,
        "comedor_dias": ""
    })
    assert res.status_code == 200
    student_id = res.json()["id"]
    print(f"Student created with ID: {student_id}")

    # 2. Create a dummy image file
    with open("test_image.jpg", "wb") as f:
        f.write(os.urandom(1024)) # Random bytes

    # 3. Upload photo
    print("Uploading photo...")
    with open("test_image.jpg", "rb") as f:
        files = {'foto': f}
        res = requests.post(f"{BASE_URL}/alumnos/{student_id}/foto", files=files)
    
    assert res.status_code == 200, f"Upload failed: {res.text}"
    data = res.json()
    assert data["ok"] is True
    filename = data["foto"]
    print(f"Photo uploaded: {filename}")

    # 4. Verify in Student List
    print("Verifying in student list...")
    res = requests.get(f"{BASE_URL}/alumnos")
    alumnos = res.json()
    student = next((a for a in alumnos if a["id"] == student_id), None)
    
    assert student is not None
    assert student["foto"] == filename
    print("Verification successful!")

    # Cleanup
    # requests.delete(f"{BASE_URL}/alumnos/{student_id}")
    # os.remove("test_image.jpg")
    # os.remove(f"static/uploads/{filename}")

if __name__ == "__main__":
    try:
        test_photo_upload()
        print("\nTEST PASSED ✅")
    except Exception as e:
        print(f"\nTEST FAILED ❌: {e}")
