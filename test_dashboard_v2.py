import json
from app import app, get_db
import datetime

def test_dashboard_v2():
    app.config['TESTING'] = True
    client = app.test_client()

    print("--- Testing Dashboard V2 Analytics ---")

    # 1. Fetch Dashboard Data
    print("\n1. Fetching dashboard summary...")
    rv = client.get('/api/dashboard/resumen')
    
    print(f"Status: {rv.status_code}")
    if rv.status_code != 200:
        print("Failed to fetch dashboard.")
        return

    data = json.loads(rv.data)
    
    # 2. Verify Weekly Attendance
    print(f"\n[Weekly Attendance]: {len(data.get('asistencia_semanal', []))} days")
    for day in data.get('asistencia_semanal', []):
        print(f" - {day['fecha']}: {day['porcentaje']}%")

    # 3. Verify Grade Distribution
    print(f"\n[Grade Distribution]:")
    dist = data.get('distribucion_notas', {})
    for rango, count in dist.items():
        print(f" - {rango}: {count}")

    # 4. Verify Alerts
    print(f"\n[Alerts]: {len(data.get('alertas', []))}")
    for alerta in data.get('alertas', []):
        print(f" - {alerta}")

    # 5. Verify Upcoming Activities
    print(f"\n[Upcoming Activities]: {len(data.get('proximas_actividades', []))}")
    for act in data.get('proximas_actividades', []):
        print(f" - {act['fecha']}: {act['actividad']}")

if __name__ == "__main__":
    test_dashboard_v2()
