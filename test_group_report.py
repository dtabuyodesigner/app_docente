import json
from app import app
import os

def test_group_report():
    app.config['TESTING'] = True
    client = app.test_client()

    print("--- Testing Group Report Features ---")
    trimestre = 2

    # 1. Test POST Observations
    print(f"\n1. Saving group observations for T{trimestre}...")
    res = client.post('/api/informe/grupo_obs', json={
        "trimestre": trimestre,
        "observaciones": "El grupo ha mejorado significativamente en su clima de convivencia.",
        "propuestas_mejora": "Continuar con las dinámicas de grupo los viernes."
    })
    print(f"Status: {res.status_code}, Response: {res.json}")

    # 2. Test GET Observations
    print(f"\n2. Fetching group observations for T{trimestre}...")
    res = client.get(f'/api/informe/grupo_obs?trimestre={trimestre}')
    print(f"Status: {res.status_code}, Response: {res.json}")

    # 3. Test GET Data
    print(f"\n3. Fetching group statistics for T{trimestre}...")
    res = client.get(f'/api/informe/grupo_data?trimestre={trimestre}')
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json
        print(f"Summary: Alumnos={data['generales']['total_alumnos']}, Media={data['generales']['media_general']}")
        print(f"Promoción: Todo aprobado={data['promocion']['todo']['num']} ({data['promocion']['todo']['pct']}%)")
        print(f"Asistencia: Media faltas={data['asistencia']['media_faltas']}")
    else:
        print(f"Error: {res.data}")

    # 4. Test GET PDF
    print(f"\n4. Generating Group PDF for T{trimestre}...")
    res = client.get(f'/api/informe/pdf_grupo?trimestre={trimestre}')
    print(f"Status: {res.status_code}, Content-Type: {res.headers.get('Content-Type')}")
    if res.status_code == 200 and res.headers.get('Content-Type') == 'application/pdf':
        filename = f"test_group_report_T{trimestre}.pdf"
        with open(filename, "wb") as f:
            f.write(res.data)
        print(f"Success: PDF generated as {filename} ({os.path.getsize(filename)} bytes)")
    else:
        print(f"Failed PDF: {res.data[:200]}")

if __name__ == "__main__":
    test_group_report()
