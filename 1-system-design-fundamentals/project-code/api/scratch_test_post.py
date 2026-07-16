import requests
import time

BASE_URL = "http://127.0.0.1:8000"

# Login
resp = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": "admin@example.com", "password": "password123"}
)
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

for length in [10, 20, 25, 28, 30]:
    bad_url = "http://example.com/" + ("a" * length) + "!"
    start = time.perf_counter()
    r = requests.post(
        f"{BASE_URL}/links",
        json={"long_url": bad_url},
        headers=headers
    )
    duration = time.perf_counter() - start
    print(f"Length {length}: Status={r.status_code}, Time={duration:.4f} seconds")
