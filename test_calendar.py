import unittest
import json
from app import app, get_db

class TestCalendar(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        with app.app_context():
            conn = get_db()
            conn.execute("DELETE FROM programacion_diaria")
            conn.commit()
            conn.close()

    def test_calendar_crud(self):
        # 1. Create Event
        resp = self.client.post('/api/programacion', json={
            "fecha": "2026-05-20",
            "actividad": "Examen Matemáticas",
            "observaciones": "Tema 5 y 6",
            "tipo": "examen",
            "color": "#dc3545"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json['ok'])

        # 2. Read Events (FullCalendar Format)
        resp = self.client.get('/api/programacion')
        self.assertEqual(resp.status_code, 200)
        data = resp.json
        self.assertEqual(len(data), 1)
        event = data[0]
        self.assertEqual(event['title'], "Examen Matemáticas")
        self.assertEqual(event['start'], "2026-05-20")
        self.assertEqual(event['color'], "#dc3545")
        self.assertEqual(event['tipo'], "examen")
        
        event_id = event['id']

        # 3. Update Event (Move Date)
        resp = self.client.put(f'/api/programacion/{event_id}', json={
            "fecha": "2026-05-21",
            "actividad": "Examen Matemáticas",
            "tipo": "examen",
            "color": "#dc3545"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json['ok'])

        # Verify Update
        resp = self.client.get('/api/programacion')
        self.assertEqual(resp.json[0]['start'], "2026-05-21")

        # 4. Delete Event
        resp = self.client.delete(f'/api/programacion/{event_id}')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json['ok'])

        # Verify Delete
        resp = self.client.get('/api/programacion')
        self.assertEqual(len(resp.json), 0)

if __name__ == "__main__":
    unittest.main()
