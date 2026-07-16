# OrderFlow Service -- Incident Runbook

**Last verified:** June 12, 2026 by Shiva -- all steps executed against production  
**Last updated:** June 12, 2026  
**Owner:** Platform Payments Team  
**Review cadence:** Monthly, or after any infrastructure change  

#### Prerequisites

- Access to the production Kubernetes cluster (kubectl configured)
- Access to Datadog dashboards (search "OrderFlow" in Dashboards)
- Slack access to #orderflow-oncall

#### Step 1: Verify Service Health

Check the health endpoint:

```bash
curl -s https://orderflow.prod.company.com/health | jq .
```

Expected healthy response:

```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected",
  "worker": "running"
}
```

If the response is anything other than the above, proceed to Step 2.

If you get no response at all (timeout or connection refused), skip to Step 6.

#### Step 2: Check Application Logs

Pull the last 100 lines of API logs:

```bash
kubectl logs -n production deployment/orderflow-api --tail=100
```

Look for:
- `ConnectionRefusedError` -- database or cache is down (go to Step 3)
- `TimeoutError` -- downstream service is slow (go to Step 5)
- `500 Internal Server Error` -- application bug (go to Step 7)

#### Step 3: Database Connection Failure

Check if PostgreSQL is reachable:

```bash
kubectl exec -n production deployment/orderflow-api -- \
  python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')"
```

If the connection fails:

1. Check the database pod status:
   ```bash
   kubectl get pods -n production -l app=orderflow-db
   ```
2. If the pod is in CrashLoopBackOff, check its logs:
   ```bash
   kubectl logs -n production -l app=orderflow-db --tail=50
   ```
3. If the database pod is healthy but the API cannot connect, verify the environment variable:
   ```bash
   kubectl exec -n production deployment/orderflow-api -- printenv DATABASE_URL
   ```
   This should output the PostgreSQL connection string. If it is empty or wrong, the deployment configuration needs updating.

#### Step 4: Redis / Worker Failure

Check if Redis is reachable:

```bash
kubectl exec -n production deployment/orderflow-api -- \
  redis-cli -u "$REDIS_URL" ping
```

Expected response: `PONG`

If Redis is not responding:

1. Check the Redis pod:
   ```bash
   kubectl get pods -n production -l app=orderflow-redis
   ```
2. If the pod is down, check events:
   ```bash
   kubectl describe pods -n production -l app=orderflow-redis
   ```
3. Escalate to #data-eng if Redis cannot be recovered.

Check if the Celery worker is processing refunds:

```bash
kubectl logs -n production deployment/orderflow-worker --tail=50
```

Look for:
- `Task received` -- worker is picking up jobs (healthy)
- `Connection refused` to Redis -- worker cannot reach the broker
- No recent log output -- worker may have crashed

If the worker is down:

```bash
kubectl rollout restart deployment/orderflow-worker -n production
```

Impact while Redis is down:
- Rate limiting is disabled. The API will accept all requests, which could cause overload. Consider enabling maintenance mode if traffic is high.
- Refund processing stops. Refunds will queue and process automatically when Redis recovers. No data is lost, but customers will see delays.

#### Step 5: Downstream Service Timeout

Check if the auth service is responding:

```bash
curl -s -o /dev/null -w "%{http_code}" https://auth.internal.company.com/health
```

If the auth service is down, OrderFlow cannot validate tokens. Mitigation:

1. Check #auth-team in Slack for known issues
2. If no known issue, page the Auth team: `pd trigger --service auth-primary`
3. OrderFlow will return 503 to all authenticated requests until auth recovers. No action needed on OrderFlow side.

#### Step 6: Complete Service Outage

If the service is unreachable:

1. Check pod status:
   ```bash
   kubectl get pods -n production -l app=orderflow-api
   ```
2. If zero pods are running, check the deployment:
   ```bash
   kubectl describe deployment -n production orderflow-api
   ```
3. If pods are stuck in ImagePullBackOff, the Docker image is missing or the registry is down. Escalate to #platform-infra.

#### Step 7: Application Bug (500 Errors)

If the logs show application errors after a recent deployment:

1. Check when the last deployment happened:
   ```bash
   helm history orderflow --namespace production
   ```
2. If the errors started after the last deployment, roll back:
   ```bash
   helm rollback orderflow --namespace production
   ```
   *This reverts the deployment to the previous Helm release. It does not deploy new code -- it restores the exact image and configuration from the last successful deployment.*
3. Confirm the rollback succeeded:
   ```bash
   helm history orderflow --namespace production
   ```
4. Verify the service recovers:
   ```bash
   curl -s https://orderflow.prod.company.com/health | jq .
   ```

#### Step 8: Escalation

If the service is still unhealthy after following the steps above:

1. Page the OrderFlow on-call: `pd trigger --service orderflow-primary`
2. Post in #orderflow-oncall with:
   - What you tried
   - What the current state is
   - Links to relevant logs/dashboards

---

#### Known Failure Modes

| Symptom | Likely Cause | Quick Fix |
|---|---|---|
| Health endpoint returns `"cache": "disconnected"` but API works | Redis pod restarted, connection pool stale | Restart API pods: `kubectl rollout restart deployment/orderflow-api -n production` |
| Refunds stuck in "pending" for > 10 minutes | Celery worker crashed or Redis broker full | Check worker logs, restart worker if needed |
| Spike in 429 (rate limit) errors | Rate limit config changed in last deploy | Check `RATE_LIMIT_PER_MINUTE` env var, rollback if wrong |
| Database connection errors after deploy | Alembic migration failed or was skipped | Check migration status: `kubectl exec -n production deployment/orderflow-api -- alembic current` |
