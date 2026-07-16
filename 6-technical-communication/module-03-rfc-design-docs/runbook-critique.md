# Critique of OrderFlow Service Incident Runbook

This critique outlines the three major failures in the provided runbook that would cause issues for an on-call engineer at 3 AM.

---

## 1. Stale Environment Variable Reference

*   **Location**: Step 3 (Database Connection Failure), line 3:
    ```bash
    python -c "import psycopg2; psycopg2.connect('$DB_CONNECTION_STRING')"
    ```
    and line 9:
    ```bash
    kubectl exec -n production deployment/orderflow-api -- printenv DB_CONNECTION_STRING
    ```
*   **On-Call Impact**: The actual database connection environment variable defined in the service specifications is `DATABASE_URL`, not `DB_CONNECTION_STRING`. Running these commands will return empty outputs or fail with a python connect error. This will mislead a tired engineer into thinking the credentials/variables are completely missing from the environment, causing them to search Helm values for configuration bugs when the database pod itself might just be restarting.
*   **Correct Fix**: Replace the stale reference with `DATABASE_URL` and use the safe python extraction:
    ```bash
    kubectl exec -n production deployment/orderflow-api -- python -c "import os, psycopg2; psycopg2.connect(os.environ['DATABASE_URL'])"
    ```
    and to inspect the variable:
    ```bash
    kubectl exec -n production deployment/orderflow-api -- printenv DATABASE_URL
    ```

---

## 2. Broken Rollback Command (Rolling Forward Instead of Back)

*   **Location**: Step 6 (Application Bug (500 Errors)), line 5:
    ```bash
    helm upgrade orderflow deploy/charts/orderflow --namespace production --set image.tag=latest
    ```
*   **On-Call Impact**: Running `helm upgrade` with `image.tag=latest` does not perform a rollback. Instead, it attempts to roll forward by building/deploying whatever image is currently tagged as `latest` in the registry. Since the previous deployment just introduced the application bug, deploying `latest` will either redeploy the exact same broken code or deploy unverified code from main. This prolongs the outage and introduces further configuration drift.
*   **Correct Fix**: Use the native `helm rollback` command to revert immediately to the last known stable release version:
    ```bash
    helm rollback orderflow --namespace production
    ```

---

## 3. Missing Critical Prerequisites (Redis & Celery Worker Checks)

*   **Location**: Entire Runbook (Missing intermediate troubleshooting sections between Step 2/3/4).
*   **On-Call Impact**: The service description explicitly states that OrderFlow uses Redis for rate limiting and as the Celery broker for processing refunds asynchronously. If Redis is down, or if the Celery worker has crashed, the API responds slower, rate limiting breaks, and refunds queue up indefinitely. Because this runbook lacks any steps to check Redis connectivity or Celery worker pod health/logs, the on-call engineer would find all other steps (DB connection, Auth timeouts, API health) "green" and remain completely blind to the root cause, delaying remediation.
*   **Correct Fix**: Add a dedicated diagnostic section for Redis and Celery worker health:
    ```bash
    # Check Redis connectivity from the API pod
    kubectl exec -n production deployment/orderflow-api -- redis-cli -u "$REDIS_URL" ping
    
    # Check Celery worker pod logs
    kubectl logs -n production deployment/orderflow-worker --tail=50
    
    # Restart the Celery worker if crashed
    kubectl rollout restart deployment/orderflow-worker -n production
    ```
