
import unittest
import json
import sqlite3
import os
from datetime import date
from app import app, get_db

class TestMonthlyHistory(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Insert test data
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO alumnos (id, nombre, no_comedor) VALUES (999, 'Test Student', 0)")
        today = date.today().strftime("%Y-%m-%d")
        cur.execute("INSERT OR REPLACE INTO asistencia (alumno_id, fecha, estado, comedor) VALUES (999, ?, 'retraso', 0)", (today,))
        conn.commit()
        conn.close()

    def tearDown(self):
        # Clean up
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM asistencia WHERE alumno_id = 999")
        cur.execute("DELETE FROM alumnos WHERE id = 999")
        conn.commit()
        conn.close()
        self.app_context.pop()

    def test_monthly_endpoint(self):
        month = date.today().strftime("%Y-%m")
        rv = self.client.get(f'/api/asistencia/mes?mes={month}')
        data = rv.get_json()
        
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(len(data) > 0)
        
        entry = next((x for x in data if x['nombre'] == 'Test Student'), None)
        self.assertIsNotNone(entry)
        self.assertTrue(entry['retrasos'] >= 1)
        self.assertEqual(entry['detalles'][0]['estado'], 'retraso')
        print("\nTest passed successfully!")

if __name__ == '__main__':
    unittest.main()
