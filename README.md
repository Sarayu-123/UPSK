# CAW / UPSK System Assignment Repository

This repository contains the structured modules and files corresponding to the CAW/UPSK system assignments. The repository is organized by skill folders, containing subdirectories mapping the work completed for each module.

Each module directory contains:
* `module_summary.md` -> An overview of the module containing key terminologies, workflows, and challenges.
* `architecture.md` -> The 7-step architectural review framework (Context, Decide, Build, Verify, Break, Fix, Reflect).

## 📂 Folder Matrix

* **[1-system-design-fundamentals](./1-system-design-fundamentals)**
  * `module-01-repository-bootstrap/`: FastAPI server initialization bootstrap.
  * `module-02-database-design/`: SQLAlchemy DB schema design configuration mapping.
  * `module-03-core-api-crud/`: Redirect router operations resolving short slugs.
  * `module-04-authentication-idor/`: JWT stateless encryption scopes.
  * `module-05-structured-logging-exceptions/`: Unified exception mappings.
  * `module-06-caching-redis/`: Redis client setup configurations.
  * `module-07-background-workers/`: Out-of-band Celery worker setups.
  * `module-08-keyset-pagination/`: Keyset sorting rules.
  * `module-09-transaction-isolation/`: Test isolation rollbacks.
  * `module-10-ready-probe/`: Lifespan boot checks.
* **[2-production-readiness](./2-production-readiness)**
  * `module-01-docker-configuration/`: Dockerfile configurations.
  * `module-02-cicd-gating/`: GitHub Actions workflows.
  * `module-03-secret-management/`: Pydantic environments configuration.
  * `module-04-observability/`: Metrics scrapers.
  * `module-05-failure-mode-mapping/`: Service degradation plans.
  * `module-06-circuit-breakers/`: pybreaker logic checks.
  * `module-07-incident-runbooks/`: Recovery runbooks.
  * `module-08-readiness-probe/`: Readiness probe setups.
* **[3-decomposition-execution-planning](./3-decomposition-execution-planning)**
  * `module-01-requirements-matrix/`: Requirements extraction tables.
  * `module-02-dependency-graph/`: DAG critical paths.
  * `module-03-risk-first-ordering/`: Timeline maps.
  * `module-04-vertical-slicing/`: Stripe slice scopes.
  * `module-05-task-granularity/`: Decomposed plans.
  * `module-06-definition-of-done/`: DoD checklist.
  * `module-07-verification-scripting/`: Automated verification scripts.
  * `module-08-retrospective-iteration/`: RETRO metrics.
* **[4-debugging-incident-response](./4-debugging-incident-response)**
  * `module-01-hypothesis-diagnosis/`: Scientific logs resolving startup and pagination bugs.
  * `module-02-cpu-profiling/`: cProfile allocations.
  * `module-03-memory-profiling/`: Database connection OOM leaks.
  * `module-04-redos-protection/`: ReDoS validator script.
  * `module-05-websocket-scoping/`: WebSocket auth scripts.
  * `module-06-blameless-postmortem/`: Postmortem incident writeups.
  * `module-07-alerting-slas/`: Alert limits.
  * `incident-case-studies/`: Outage case study reports.
* **[5-ai-augmented-engineering](./5-ai-augmented-engineering)**
  * `module-01-context-engineering/`: System architectural constraints.
  * `module-02-task-specific-context/`: Reference templates.
  * `module-03-automated-code-search/`: Automated search findings.
  * `module-04-targeted-code-edits/`: Unique constraints reviews.
  * `module-05-test-driven-validation/`: E2E WebSocket test runs.
  * `module-06-static-linting/`: Static analysis self-ratings.
  * `module-07-multi-agent-task-delegation/`: Coordinator workflows.
  * `module-08-self-correction-reflection/`: Retrospective loop reflections.
* **[6-technical-communication](./6-technical-communication)**
  * `module-01-constructive-critique/`: PR review refactorings.
  * `module-02-technical-writing/`: Scannable manuals.
  * `module-03-rfc-design-docs/`: RFC blueprints.
  * `module-04-postmortem-incident-writeups/`: Blameless postmortem timelines.
  * `module-05-stakeholder-communication/`: Decision memos.
  * `module-06-troubleshooting-runbooks/`: Namespace rollbacks.
