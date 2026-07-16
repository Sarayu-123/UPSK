import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Login
resp = client.post(
    "/auth/login",
    data={"username": "admin@example.com", "password": "password123"}
)
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

for length in [10, 20, 25, 28, 30, 32]:
    bad_url = "http://example.com/" + ("a" * length) + "!"
    start = time.perf_counter()
    r = client.post(
        "/links",
        json={"long_url": bad_url},
        headers=headers
    )
    duration = time.perf_counter() - start
    print(f"Length {length}: Status={r.status_code}, Time={duration:.4f} seconds")
