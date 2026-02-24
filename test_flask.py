import subprocess
import time
import requests

proc = subprocess.Popen(["flask", "run", "--port", "5001"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
time.sleep(2)
try:
    r = requests.post("http://localhost:5001/api/tareas", json={
        "titulo": "Corregir libreras",
        "descripcion": "Revisar",
        "prioridad": "alta",
        "fecha_limite": "2024-11-20"
    })
    print("STATUS", r.status_code)
    print("RESPONSE", r.text)
except Exception as e:
    print("ERROR", e)

proc.terminate()
time.sleep(1)
outs, errs = proc.communicate()
print("STDOUT", outs)
print("STDERR", errs)
