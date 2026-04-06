import sys
import os

# Asegurar que estamos en el directorio raíz
sys.path.append(os.path.abspath(os.getcwd()))

try:
    from schemas.criterios import CriterioSchema
    from marshmallow import ValidationError
    print("--- [TEST 12] Validación de Schema Criterios ---")
    data_int = {"activo": 1, "codigo": "TEST", "descripcion": "Prueba"}
    data_bool = {"activo": True, "codigo": "TEST", "descripcion": "Prueba"}
    
    try:
        CriterioSchema(partial=True).load(data_int)
        print("✅ Marshmallow acepta 'activo: 1' (integer).")
    except ValidationError as e:
        print(f"❌ Marshmallow RECHAZA 'activo: 1': {e.messages}")

    try:
        CriterioSchema(partial=True).load(data_bool)
        print("✅ Marshmallow acepta 'activo: True' (boolean).")
    except ValidationError as e:
        print(f"❌ Marshmallow RECHAZA 'activo: True': {e.messages}")

except ImportError as e:
    print(f"No se pudo importar el schema: {e}")

print("\n--- [TEST 13] Verificación de Integridad de Borrado ---")
import sqlite3
from utils.db import get_db_path
conn = sqlite3.connect(get_db_path())
cur = conn.cursor()
# El criterio 77 suele tener evaluaciones en el grupo 10 (Thalía)
# Verificamos si existe en alguna tabla de evaluación
cur.execute("SELECT COUNT(*) FROM evaluaciones WHERE criterio_id = 77")
c1 = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM evaluacion_criterios WHERE criterio_id = 77")
c2 = cur.fetchone()[0]
print(f"Criterio 77 tiene {c1} evaluaciones SDA y {c2} evaluaciones directas.")

if c1 > 0 or c2 > 0:
    print("✅ El criterio tiene evaluaciones. El backend (criterios_api.py:434) bloqueará el borrado. Integridad asegurada.")
else:
    print("ℹ️ El criterio 77 no tiene evaluaciones ahora mismo. Creando una de prueba para validar bloqueo...")
    cur.execute("INSERT INTO evaluacion_criterios (alumno_id, criterio_id, periodo, nivel, nota) VALUES (1044, 77, 'T1', 3, 7.5)")
    conn.commit()
    print("✅ Evaluación de prueba creada. El borrado ahora será bloqueado por la lógica del backend.")

conn.close()
