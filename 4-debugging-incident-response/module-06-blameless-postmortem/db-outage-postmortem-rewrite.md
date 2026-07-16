# Blameless Postmortem Rewrite: Database Outage on March 15th

## Summary
A database migration containing a schema defect dropped the primary query index on the `users` table. This degraded database lookup performance and caused all authentication queries to time out, resulting in a complete outage of the authentication service. The incident began on Friday afternoon and normal operations were restored on Saturday morning after rolling back the migration.

## Root Cause
A database migration containing a schema defect dropped the primary query index on the `users` table, which degraded database lookup performance and caused all authentication queries to time out. The deployment pipeline lacked automated validation gates to dry-run migrations against a production-like database schema, allowing the index-drop query to execute in production.

## Contributing Factors
1. Migration deployment tooling does not require local verification or dry-run validation before allowing deployment.
2. The pull request review system does not enforce peer review blockades for changes containing schema modifications, allowing unapproved PRs to be merged.
3. The release pipeline lacks automated deploy-freeze windows, permitting high-risk schema migrations on late Friday afternoons.

## Remediation Items
| # | Action | Owner | Deadline | Status |
|---|--------|-------|----------|--------|
| 1 | Add automated schema migration validation checks in CI/CD pipeline to dry-run migrations against a copy of the staging schema before deployment | Platform Team | End of Sprint 12 | Open |
| 2 | Enforce mandatory branch protection rules requiring at least one senior peer review on all database schema migration PRs | Devops Team | End of Sprint 12 | Open |
| 3 | Implement a hard deployment freeze policy (no production deploys after Friday 12:00 UTC) automated via release pipeline configurations | Release Management | End of Sprint 12 | Open |
