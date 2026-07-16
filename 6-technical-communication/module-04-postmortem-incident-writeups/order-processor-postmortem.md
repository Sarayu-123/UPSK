# Incident Postmortem: OrderProcessor Silent Order Loss Outage (March 15)

## Summary

On Wednesday, March 15, the OrderProcessor service experienced a 2-hour outage during which customer checkout requests completed with HTTP 200 OK responses but failed to persist orders to the database. The incident began at 14:00 UTC following the deployment of version 2.14, which removed a deprecated configuration field. Because the service swallowed database write errors and returned false success pages, monitoring systems did not detect the drop in order creation rate. Approximately 1,400 orders were silently dropped, affecting an estimated $186,000 in revenue. Normal operations were restored at 15:34 UTC after a manual rollback to version 2.13.

## Timeline (all times UTC)

* **14:00** -- Deployment of OrderProcessor v2.14 is completed. The release removes the deprecated `warehouse_routing` configuration field from the service config.
* **14:00 - 14:22** -- Automated health checks pass and the deployment dashboard reports healthy state. The service responds with HTTP 200 OK status codes to all incoming checkout requests.
* **14:22** -- Customer reports emerge on social media regarding missing order confirmation emails, and customer support begins receiving tickets.
* **14:23** -- Support agent flags the customer reports in the incident communication channel. The on-call responder observes the notification but attributes it to a transient email delivery delay, delaying the start of the investigation.
* **14:38** -- A second escalation wave of support tickets arrives. The on-call responder initiates an active investigation.
* **14:42** -- The on-call responder reviews the service dashboard. HTTP response codes show 100% success (200 OK), and CPU, memory, and latency metrics appear normal.
* **14:55** -- The on-call responder queries the order database directly and discovers zero database writes since 14:00 UTC.
* **15:02** -- The on-call responder identifies the v2.14 deployment as the trigger and attempts an automated rollback.
* **15:08** -- The automated rollback fails because the script contains outdated deployment artifact paths following a recent infrastructure migration.
* **15:15** -- The on-call responder escalates the failure to the platform team.
* **15:34** -- The platform team completes a manual rollback to v2.13. Database writes resume, and healthy order creation is verified.
* **15:45** -- The engineering team initiates manual reconciliation and reprocessing of the 1,400 dropped orders using payment processor logs.
* **16:02** -- Reprocessing is completed, all missing orders are created, confirmation emails are sent, and the incident is declared resolved.

## Root Causes

This incident was made possible by three systemic design and validation failures:

1. **Silent Exception Swallowing:** The OrderProcessor service captured missing configuration field exceptions in a broad `try/except` block, logged them at the `DEBUG` level, and returned an HTTP 200 OK success response. This prevented the application from failing loudly or generating error logs when database persistence failed.
2. **Monitoring Gaps:** The monitoring dashboard only tracked system availability (HTTP status codes and system resource utilization) instead of business-level metrics (e.g., successful database writes or orders created per minute). Consequently, the complete cessation of order creation went undetected.
3. **Environment Disparity:** The staging and production environments used different configuration schemas. The `warehouse_routing` field was already absent from the staging config schema, which prevented pre-release integration tests from flagging the missing config dependency.

## Contributing Factors

1. **Verification Delay:** The incident escalation process did not distinguish between email delivery failures and order persistence outages, leading to an initial assumption of transient email delays and a 15-minute delay in initiating the investigation.
2. **Untested Rollback Tooling:** Rollback scripts were not validated following the infrastructure migration four months ago, causing the automated rollback attempt to fail due to outdated path references.

## Action Items

| # | Action Item Description | Owner | Deadline | Definition of Done |
|---|-------------------------|-------|----------|--------------------|
| 1 | Add a backwards-compatibility check to the CI pipeline that fails the build if a configuration field is removed while any running service version still references it. | CI/CD Platform Lead | April 1 | Build fails in test suite when deprecated fields in active use are removed. |
| 2 | Add a required pre-deploy checklist in the deployment tool that blocks deployment execution until backwards-compatibility is confirmed. | Release Manager | April 1 | Deployment pipeline prompts and blocks until verified checklist payload is submitted. |
| 3 | Add an orders-per-minute metric with an alert that fires to `#ops-alerts` when the rate drops below the trailing-7-day average by more than 50% for 5 consecutive minutes. | Observability Lead | March 25 | Prometheus alert rule active and firing into Slack when order rate falls below threshold. |
| 4 | Audit and test all rollback scripts monthly; add a rollback dry-run step to the deployment pipeline. | Platform Engineering Lead | March 30 | Dry-run verification script runs successfully on every CI build. |
| 5 | Require automated config-diff analysis in the Pull Request pipeline that flags removed or renamed configuration fields. | DevOps Lead | March 25 | PR check automatically comments with a diff of changed keys on all config updates. |

## Lessons Learned

* **Verification of Deprecations:** Relying on policy-based deprecation timelines without runtime tracking and automated dependency verification is insufficient to prevent compatibility errors.
* **System-Level Visibility:** HTTP success rates are a poor proxy for business transaction health; checking transaction success at the database boundary is critical.
* **Rollback Readiness:** Recovery procedures must be treated as active software products that require continuous testing and automated verification, rather than static scripts.
