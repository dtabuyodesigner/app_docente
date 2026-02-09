import requests
import sqlite3
import os

BASE_URL = "http://localhost:5000"

def get_first_student_id():
    conn = sqlite3.connect("app_evaluar.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM alumnos LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def test_pdf_generation():
    uid = get_first_student_id()
    if not uid:
        print("No students found in DB.")
        return

    print(f"Testing PDF for student ID: {uid}")
    url = f"{BASE_URL}/api/informe/pdf_diario/{uid}"
    
    r = requests.get(url)
    
    print(f"Status Code: {r.status_code}")
    print(f"Content-Type: {r.headers.get('Content-Type')}")
    print(f"Content-Disposition: {r.headers.get('Content-Disposition')}")
    print(f"Size: {len(r.content)} bytes")

    if r.status_code == 200 and 'application/pdf' in r.headers.get('Content-Type', ''):
        print("✅ PDF Generation Successful")
        with open("test_diario.pdf", "wb") as f:
            f.write(r.content)
        print("Saved to test_diario.pdf")
    else:
        print("❌ PDF Generation Failed")
        print(r.text)

if __name__ == "__main__":
    test_pdf_generation()
