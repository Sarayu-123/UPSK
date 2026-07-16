# RFC: API Rate Limiting Infrastructure

## Problem Statement

Over the last month, a single customer accidentally generated approximately 50,000 requests per minute, degrading API performance for all customers. The on-call engineer had to manually block the customer by modifying configuration files and redeploying the service at 2 AM.

The current platform has no automated throttling mechanism, making the API vulnerable to accidental abuse, misconfigured clients, and denial-of-service scenarios. Additionally, the product team plans to introduce paid subscription tiers with different usage limits, which cannot be enforced with the current architecture.

## Proposed Approach

Implement rate limiting at the API Gateway so requests are evaluated before reaching backend services.

The system will use a Token Bucket algorithm. Each customer receives a bucket containing a predefined number of tokens. Each request consumes one token. Tokens are replenished at a fixed rate based on the customer's subscription tier. This allows short bursts while enforcing a long-term request rate.

Rate limit counters will be stored in Redis because it provides low-latency access and supports distributed deployments.

To prevent race conditions, the token validation and token consumption logic will execute through a single atomic Redis Lua script.

If a customer exceeds their limit, the gateway will return HTTP 429 (Too Many Requests) along with rate-limit headers.

If Redis becomes unavailable or exceeds the latency budget of 2 milliseconds, the system will fail open and allow requests to proceed while generating critical alerts for on-call responders.

Rate limits will initially be enforced using API keys. User IDs and IP addresses may be used as fallback identifiers where appropriate.

## Alternatives Considered

### Application-Level Rate Limiting

Each backend service could enforce its own limits.

**Pros**

* No additional gateway logic.
* Service-specific control.

**Cons**

* Duplicated implementation across services.
* Inconsistent enforcement.
* Traffic reaches backend infrastructure before being rejected.

### Database-Backed Counters

Store rate-limit counters in PostgreSQL.

**Pros**

* Reuses existing infrastructure.
* Strong durability guarantees.

**Cons**

* Higher latency.
* Additional database load on every request.
* Poor fit for high-frequency counter updates.

### Fixed Window Algorithm

Track request counts within fixed time windows.

**Pros**

* Simple implementation.
* Easy to understand.

**Cons**

* Unfair boundary behavior.
* Allows request spikes at window transitions.
* Less flexible than Token Bucket.

## Risks and Mitigations

| Risk                                       | Mitigation                                                                             |
| ------------------------------------------ | -------------------------------------------------------------------------------------- |
| Redis outage causes rate-limiting failures | Fail open and generate critical alerts                                                 |
| Redis latency increases request latency    | Enforce 2ms latency budget and monitor continuously                                    |
| Incorrect limits impact customers          | Roll out gradually and monitor rejection rates                                         |
| Lua script bugs cause incorrect throttling | Add automated integration and load testing                                             |
| No rate limiting is implemented            | Continued service degradation, manual intervention, and inability to launch paid tiers |

## Open Questions

1. What default limits should be assigned to Free, Pro, and Enterprise tiers?
2. Should burst limits differ from sustained limits for paid customers?
3. Does Product require self-service visibility into rate-limit usage?
4. Should customers receive notifications when approaching their limits?
5. Should rate-limit metrics be exposed through the customer dashboard?
6. What alert thresholds should trigger on-call escalation for Redis latency or failure?
