#!/usr/bin/env python3
"""
Post-Deploy Synthetic Smoke Test
=================================
Exercises the full user workflow after deployment:
  Login → Create Link → Verify → Redirect → Delete → Verify Deletion

Exit codes:
  0 = all checks passed
  1 = one or more checks failed

Usage:
  python scripts/smoke_test.py [--base-url http://localhost:8000]
"""

import argparse
import sys
import time
import requests


SYNTHETIC_PREFIX = "__synthetic_test_"


def log(step: str, result: str, detail: str = ""):
    icon = "✅" if result == "PASS" else "❌"
    msg = f"  {icon} {step}: {result}"
    if detail:
        msg += f"  ({detail})"
    print(msg)


def run_smoke_test(base_url: str) -> bool:
    print(f"\n{'='*50}")
    print(f"Smoke Test: {base_url}")
    print(f"{'='*50}\n")

    all_passed = True
    token = None
    created_link_id = None
    created_code = None
    test_url = f"https://example.com/{SYNTHETIC_PREFIX}{int(time.time())}"

    # -----------------------------------------------
    # Step 1: Login
    # -----------------------------------------------
    try:
        resp = requests.post(
            f"{base_url}/auth/login",
            data={
                "username": "admin@example.com",
                "password": "password123"
            },
            timeout=5
        )
        if resp.status_code == 200 and "access_token" in resp.json():
            token = resp.json()["access_token"]
            log("Login", "PASS", f"HTTP {resp.status_code}")
        else:
            log("Login", "FAIL", f"HTTP {resp.status_code}: {resp.text[:100]}")
            all_passed = False
            return all_passed  # Cannot continue without auth
    except Exception as e:
        log("Login", "FAIL", str(e))
        return False

    headers = {"Authorization": f"Bearer {token}"}

    # -----------------------------------------------
    # Step 2: Create synthetic link
    # -----------------------------------------------
    try:
        resp = requests.post(
            f"{base_url}/links",
            headers={**headers, "Content-Type": "application/json"},
            json={"long_url": test_url},
            timeout=5
        )
        if resp.status_code == 201:
            body = resp.json()
            created_link_id = body.get("id")
            created_code = body.get("code")
            log("Create Link", "PASS", f"id={created_link_id} code={created_code}")
        else:
            log("Create Link", "FAIL", f"HTTP {resp.status_code}: {resp.text[:100]}")
            all_passed = False
    except Exception as e:
        log("Create Link", "FAIL", str(e))
        all_passed = False

    # -----------------------------------------------
    # Step 3: Verify link exists via GET
    # -----------------------------------------------
    if created_link_id:
        try:
            resp = requests.get(
                f"{base_url}/links/{created_link_id}",
                headers=headers,
                timeout=5
            )
            if resp.status_code == 200:
                body = resp.json()
                if body.get("long_url") == test_url:
                    log("Verify Link", "PASS", f"long_url matches")
                else:
                    log("Verify Link", "FAIL", f"long_url mismatch: {body.get('long_url')}")
                    all_passed = False
            else:
                log("Verify Link", "FAIL", f"HTTP {resp.status_code}")
                all_passed = False
        except Exception as e:
            log("Verify Link", "FAIL", str(e))
            all_passed = False

    # -----------------------------------------------
    # Step 4: Test redirect
    # -----------------------------------------------
    if created_code:
        try:
            resp = requests.get(
                f"{base_url}/{created_code}",
                allow_redirects=False,
                timeout=5
            )
            if resp.status_code == 302:
                location = resp.headers.get("Location", "")
                if location == test_url:
                    log("Redirect", "PASS", f"302 → {location}")
                else:
                    log("Redirect", "FAIL", f"302 but wrong target: {location}")
                    all_passed = False
            else:
                log("Redirect", "FAIL", f"HTTP {resp.status_code} (expected 302)")
                all_passed = False
        except Exception as e:
            log("Redirect", "FAIL", str(e))
            all_passed = False

    # -----------------------------------------------
    # Step 5: Cleanup — delete synthetic link
    # -----------------------------------------------
    if created_link_id:
        try:
            resp = requests.delete(
                f"{base_url}/links/{created_link_id}",
                headers=headers,
                timeout=5
            )
            if resp.status_code == 204:
                log("Cleanup (Delete)", "PASS", f"link {created_link_id} deleted")
            else:
                log("Cleanup (Delete)", "FAIL", f"HTTP {resp.status_code}")
                all_passed = False
        except Exception as e:
            log("Cleanup (Delete)", "FAIL", str(e))
            all_passed = False

    # -----------------------------------------------
    # Step 6: Verify deletion
    # -----------------------------------------------
    if created_link_id:
        try:
            resp = requests.get(
                f"{base_url}/links/{created_link_id}",
                headers=headers,
                timeout=5
            )
            if resp.status_code == 404:
                log("Verify Deletion", "PASS", "link no longer exists")
            else:
                log("Verify Deletion", "FAIL", f"HTTP {resp.status_code} (expected 404)")
                all_passed = False
        except Exception as e:
            log("Verify Deletion", "FAIL", str(e))
            all_passed = False

    # -----------------------------------------------
    # Summary
    # -----------------------------------------------
    print(f"\n{'='*50}")
    if all_passed:
        print("RESULT: ALL CHECKS PASSED")
    else:
        print("RESULT: ONE OR MORE CHECKS FAILED")
    print(f"{'='*50}\n")

    return all_passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post-deploy synthetic smoke test")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the deployed service"
    )
    args = parser.parse_args()

    success = run_smoke_test(args.base_url)
    sys.exit(0 if success else 1)
