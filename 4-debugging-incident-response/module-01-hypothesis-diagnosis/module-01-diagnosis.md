# Module 01 Diagnosis Notes

## Bug 1
- Symptom: Service crashes on startup with a database connection error.
- Hypothesis A: The database containers are not running or healthy.
  - Command: `docker compose -f infra/docker-compose.yml ps`
  - Observation: Both `linkops-postgres` and `linkops-redis` are up and healthy. (Disproven)
- Hypothesis B: The database connection string in `.env` has an incorrect database name.
  - Command: Checked `api/.env` and found `DATABASE_URL` pointed to `upsk_sdf` while `docker-compose.yml` set `POSTGRES_DB` to `linkops`.
  - Observation: Database name mismatch caused connection failures. (Confirmed)
- Fix: Updated the database name in `api/.env` from `upsk_sdf` to `linkops`, ran `alembic upgrade head` to set up tables, and restarted the application.
- Verification proof: `curl.exe -sS http://localhost:3000/health` returns `{"ok":true}`.

## Bug 2
- Symptom: Users observe duplicate short links appearing across page boundaries when paginating.
- Hypothesis A: The pagination offset calculation is incorrect, causing overlapping query boundaries.
  - Command: Checked the `skip` and `limit` calculation in `api/app/routers/links.py` inside `search_user_links`.
  - Observation: The logic `skip = (page - 1) * page_size` is mathematically correct. (Disproven)
- Hypothesis B: The pagination query has an unstable sort order, causing the database to return records in a non-deterministic order.
  - Command: Checked `api/app/crud.py` to see if pagination queries lack a unique/stable secondary sorting key.
  - Observation: The sort order only used `created_at`, `code`, or `long_url` directly, without a unique secondary tie-breaker like `Link.id`. This allows Postgres to return rows in varying order on subsequent queries. (Confirmed)
- Fix: Added a unique secondary sorting column (`Link.id`) to the `order_by` clauses in `get_links_by_user` and `search_links` functions in `api/app/crud.py`.
- Verification proof: Made API requests for page 1, 2, and 3 with `page_size=5` via `/links/search`. The responses returned links cleanly partitioned: Page 1 (IDs 15-11), Page 2 (IDs 10-6), and Page 3 (IDs 5-1) with zero overlaps or duplicates.
