import requests

s = requests.Session()

# Test 1: Accessing protected page (should redirect to login or get 401 via API)
r = s.get("http://127.0.0.1:5000/api/tareas")
print("1. Protected API access (no auth):", r.status_code, r.text)

r2 = s.get("http://127.0.0.1:5000/alumnos", allow_redirects=False)
print("2. Protected HTML access (no auth):", r2.status_code, "Redirect to:", r2.headers.get('Location'))

# Test 2: Login failure
r3 = s.post("http://127.0.0.1:5000/login", json={"password": "wrong"})
print("3. Login failure:", r3.status_code, r3.json())

# Test 3: Login success
r4 = s.post("http://127.0.0.1:5000/login", json={"password": "secreto123"})
print("4. Login success:", r4.status_code, r4.json())

# Test 4: Accessing protected page (with auth)
r5 = s.get("http://127.0.0.1:5000/api/gestor_tareas")
print("5. Protected API access (with auth):", r5.status_code)

