# Failure Mode and Effects Analysis (FMEA)

## 1. Dependency Inventory
- **PostgreSQL**: Primary datastore.
- **Redis**: Cache and rate limiter backing.
- **Celery**: Background analytics processor.
- **Docker/OS DNS**: Resolution for external connections.
- **File System**: Disk space for DB and logs.

## 2. Failure Mode Table (8 Entries)

| ID | Component | Failure Mode | Type | Current Handling | Desired Handling | Simulated? |
|----|-----------|--------------|------|------------------|------------------|------------|
| 1 | PostgreSQL | Connection Refused (Down) | Permanent (Service Down) | `500 Internal Server Error` on all routes. Readiness check fails (`503`). | Fail-Closed. Correctly fails readiness check. App should not mask this. | **Yes** |
| 2 | Redis | Timeout (> 1ms latency) | Transient | Catches exception, logs warning, returns `None`, falls back to DB. | Fail-Open. Current behavior is correct—maintains availability. | **Yes** |
| 3 | PostgreSQL | Connection Timeout (Load) | Transient | Request hangs until SQLAlchemy timeout, then `500`. | Fail-Closed, but with Circuit Breaker to shed load and avoid resource exhaustion. | No |
| 4 | PostgreSQL | Invalid Credentials | Permanent | Application crashes on startup or returns `500` constantly. | Fail-Fast. Should exit immediately on startup if credentials are bad. Do not retry. | No |
| 5 | Redis | Connection Refused (Down) | Permanent | Same as timeout: catches exception, falls back to Postgres. Rate limits may fail open or closed. | Fail-Open for cache. Rate limiting should ideally fail-open (allow traffic) but log heavily. | No |
| 6 | Celery | Redis Broker OOM | Permanent | Analytics tasks fail to enqueue. Logs warning, request continues. | Fail-Open. Correctly implemented: analytics loss should not break redirects. | No |
| 7 | DNS | Resolution Failure | Transient | If external service is called, hangs until timeout. | Fail-Closed for Auth, Fail-Open for non-critical webhooks. Retry with backoff. | No |
| 8 | File System| Disk Full (Postgres Vol)| Permanent | DB halts all writes. `POST /links` returns `500`. | Fail-Closed. Alerts must fire at 80% capacity before this happens. | No |
| 9 | PostgreSQL | Partial Failure (Read-Only Mode) | Permanent | `500 Internal Server Error` on writes. Reads succeed. `/ready` incorrectly reports healthy. | Fail-Closed for writes. Return `503 Service Unavailable` with clear error. `/ready` should check write capability. | **Yes** |

## 3. Top 3 Failure Modes Ranked by Risk
*(Risk = Probability × Impact)*

1. **Redis Timeout / High Latency (High Risk)**
   - **Why**: Caches are notorious for latency spikes during eviction or CPU saturation. Impact is high because it stalls the event loop if timeouts are misconfigured (brownout).
   - **Fix First**: I simulated this. The fix is ensuring strict, low timeouts (e.g., 5ms) so the fallback to Postgres is near-instant, preventing cascading failure.
2. **PostgreSQL Connection Exhaustion/Timeout (Medium-High Risk)**
   - **Why**: Very common during traffic spikes. If the pool is exhausted, the app hangs. Impact is total downtime.
3. **Celery Redis Broker OOM (Medium Risk)**
   - **Why**: Analytics queues can grow unbounded if workers die. Fails open currently, so impact is just lost analytics, but it can crash Redis which also affects rate limiting.

## 4. Discovery and Reflection

**A failure mode I hadn't thought of before:**
I originally didn't consider *Redis Slow Responses (Brownout)* as a distinct failure mode from *Redis Down*. I assumed a failure meant a crashed process. However, simulating a 1ms timeout revealed that a slow dependency is far more dangerous than a dead one. If Redis is down, the OS immediately rejects the connection (Connection Refused). If Redis is slow, the connection stays open, consuming a thread/socket, eventually stalling the entire FastAPI event loop.

**What is the difference between doing this analysis and hoping nothing goes wrong?**
Hoping nothing goes wrong leads to "optimistic coding" where we assume `redis.get()` always returns instantly. This analysis forces us to distinguish between *transient* (retriable, e.g., brief network blip) and *permanent* (requires intervention, e.g., bad credentials). If my table is accurate, the next feature I build (e.g., a webhook sender) will inherently include strict timeouts, a defined failure stance (fail-open vs closed), and no infinite retries for permanent errors.
