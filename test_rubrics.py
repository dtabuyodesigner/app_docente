import unittest
import json
from app import app, get_db

class TestRubrics(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Clean rubrics table
        with app.app_context():
            conn = get_db()
            conn.execute("DELETE FROM rubricas")
            conn.commit()
            
            # Ensure we have a dummy criterion for testing
            # We need an existing sda and criterion. 
            # We'll assume ID 1 exists or insert one if not.
            # Ideally we should insert test data here.
            try:
                conn.execute("INSERT OR IGNORE INTO areas (id, nombre) VALUES (999, 'Area Test')")
                conn.execute("INSERT OR IGNORE INTO sda (id, nombre, area_id) VALUES (999, 'SDA Test', 999)")
                conn.execute("INSERT OR IGNORE INTO criterios (id, codigo, descripcion) VALUES (9999, 'CRIT.TEST', 'Desc Test')")
                conn.execute("INSERT OR IGNORE INTO sda_criterios (sda_id, criterio_id) VALUES (999, 9999)")
                conn.commit()
            except:
                pass # If tables structure differs, we might fail, but let's try.
            conn.close()

    def test_save_and_get_rubrica(self):
        criterio_id = 9999
        data = {
            "criterio_id": criterio_id,
            "descriptores": {
                "1": "Nivel 1 Test",
                "2": "Nivel 2 Test",
                "3": "Nivel 3 Test",
                "4": "Nivel 4 Test"
            }
        }
        
        # SAVE
        resp = self.client.post('/api/rubricas', json=data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json['ok'])
        
        # GET
        resp = self.client.get(f'/api/rubricas/{criterio_id}')
        self.assertEqual(resp.status_code, 200)
        rubs = resp.json
        self.assertEqual(rubs['1'], "Nivel 1 Test")
        self.assertEqual(rubs['4'], "Nivel 4 Test")

    def test_pdf_generation(self):
        sda_id = 999
        resp = self.client.get(f'/api/rubricas/pdf/{sda_id}')
        
        # Check if it returns a PDF
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'application/pdf')
        self.assertTrue(len(resp.data) > 0)
        self.assertTrue(b'%PDF' in resp.data)

if __name__ == "__main__":
    unittest.main()
