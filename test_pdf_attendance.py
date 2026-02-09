from app import app
import os

def test_pdf_attendance():
    app.config['TESTING'] = True
    client = app.test_client()

    print("Testing /api/informe/pdf_individual with attendance...")
    alumno_id = 11
    trimestre = 2
    
    rv = client.get(f'/api/informe/pdf_individual?alumno_id={alumno_id}&trimestre={trimestre}')
    
    print(f"Status: {rv.status_code}")
    print(f"Content-Type: {rv.headers.get('Content-Type')}")
    
    if rv.status_code == 200 and rv.headers.get('Content-Type') == 'application/pdf':
        filename = f"test_attendance_report_{alumno_id}.pdf"
        with open(filename, "wb") as f:
            f.write(rv.data)
        print(f"Success: PDF generated successfully as {filename}")
        print(f"File size: {os.path.getsize(filename)} bytes")
    else:
        print(f"Failed: {rv.data.decode('utf-8', errors='ignore')[:200]}")

if __name__ == "__main__":
    test_pdf_attendance()
