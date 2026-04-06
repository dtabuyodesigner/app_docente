import sys
import json
import sqlite3
import os

# Asegurar que estamos en el directorio raíz
sys.path.append(os.path.abspath(os.getcwd()))

from app import app
from utils.db import get_db

def run_tests():
    print("🚀 Iniciando validación de lógica de evaluación y criterios...")
    with app.test_client() as client:
        # Mock Session para bypass require_auth
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['logged_in'] = True
            sess['role'] = 'admin'
            sess['username'] = 'admin'

        print("\n--- [TEST 8] Guardado Infantil (Modo Directo) ---")
        # Usamos Thalía (1044) y su criterio de Armonía (77)
        payload = {
            "alumno_id": 1044,
            "criterio_id": 77,
            "nivel": 2,
            "periodo": "T1",
            "modo": "POR_CRITERIOS_DIRECTOS"
        }
        res = client.post('/api/evaluacion/guardar_unificado', json=payload)
        data = res.get_json()
        print(f"Status: {res.status_code}, Response: {data}")
        
        if not data or not data.get('ok'):
            print("❌ Error en Test 8")
        else:
            print("✅ Test 8: Respuesta OK")

        # Verificación en BD física
        with app.app_context():
            db = get_db()
            row = db.execute("SELECT * FROM evaluacion_criterios WHERE alumno_id = 1044 AND criterio_id = 77 AND periodo = 'T1'").fetchone()
            if row and row['nivel'] == 2:
                print(f"🔎 BD: Registro encontrado con nivel {row['nivel']}. ✅")
            else:
                print("🔎 BD: Registro no encontrado o incorrecto. ❌")

        print("\n--- [TEST 10] Borrado de evaluación (Click en activa) ---")
        payload['nivel'] = 0 # En el frontend, 0 o null lanza el borrado
        res = client.post('/api/evaluacion/guardar_unificado', json=payload)
        print(f"Status: {res.status_code}, Response: {res.get_json()}")
        
        with app.app_context():
            db = get_db()
            row = db.execute("SELECT * FROM evaluacion_criterios WHERE alumno_id = 1044 AND criterio_id = 77 AND periodo = 'T1'").fetchone()
            if not row:
                print("🔎 BD: Registro eliminado correctamente. ✅")
            else:
                print("🔎 BD: El registro todavía existe. ❌")

        print("\n--- [TEST 12] Edición de Criterio (Marshmallow bug) ---")
        # El bug reportado era que al enviar 'activo' como número (1/0) desde JS, Marshmallow fallaba.
        payload_edit = {
            "activo": 1,
            "descripcion": "Verificación final Test 12 - Descripción editada"
        }
        res = client.put('/api/criterios/77', json=payload_edit)
        data_edit = res.get_json()
        print(f"Status: {res.status_code}, Response: {data_edit}")
        
        if data_edit and data_edit.get('ok'):
            print("✅ Test 12: El backend acepta 'activo: 1' (integer) correctamente. Fix confirmado.")
        else:
            print("❌ Test 12: El backend rechazó la edición. Posible bug persistente.")
            if 'details' in data_edit:
                print(f"Detalles: {data_edit['details']}")

        print("\n--- [TEST 13] Borrado de Criterio con Evaluaciones (Integridad) ---")
        # Re-creamos una evaluación para el criterio 77
        client.post('/api/evaluacion/guardar_unificado', json={"alumno_id": 1044, "criterio_id": 77, "nivel": 3, "periodo": "T1", "modo": "POR_CRITERIOS_DIRECTOS"})
        
        # Intentamos borrar el criterio 77 (debe fallar)
        res_del = client.delete('/api/criterios/77')
        data_del = res_del.get_json()
        print(f"Status: {res_del.status_code}, Response: {data_del}")
        
        if res_del.status_code == 400 and not data_del.get('ok'):
            print("✅ Test 13: El sistema bloqueó correctamente el borrado por integridad referencial.")
        else:
            print("❌ Test 13: El sistema permitió borrar un criterio con evaluaciones. PELIGRO.")

        # Cleanup final para dejar la BD limpia
        client.post('/api/evaluacion/guardar_unificado', json={"alumno_id": 1044, "criterio_id": 77, "nivel": 0, "periodo": "T1", "modo": "POR_CRITERIOS_DIRECTOS"})

if __name__ == "__main__":
    run_tests()
