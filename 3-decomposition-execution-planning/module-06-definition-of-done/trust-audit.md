# Trust Audit

## 1. What is Trusted
- **Folder structure and file locations**: The exact file layout and directory tree matches the physical directory tree on disk.
- **Route signatures**: The HTTP methods and endpoint paths are factual and can be trusted.
- **Library references**: Dependencies specified in `requirements.txt` are accurate indicators of project capabilities.

## 2. What Must Be Verified
- **Auth middleware behavior**: Whether JWT verification is actually enforced on all link routes, and how unauthorized calls are rejected.
- **Database schema details**: The exact column constraints and foreign key mappings.
- **Config loading**: How the application handles missing env variables or defaults locally vs. production.

## 3. Suspicious Areas / Caveats
- **Background queues (Celery/Redis)**: AI agents frequently assume Redis is reachable and properly configured on standard local ports. This must be validated before writing task code.
- **Unused patterns**: Mocks or stub routes left in routers that don't map to actual business functionality.

## 4. Verification Command & Result
- **Command Run**: Listed directories in `api/app/routers` using system directory tools.
- **Result**: Confirmed the existence of separate `auth.py` and `links.py` router files. This verifies the factual claim that the project uses a file-per-route router mapping structure instead of central routing.

## 5. Disproving the Wrong Claim

Claim said: "This starter workspace is only a platform folder with AGENTS.md, CLAUDE.md, reports, and progress/; it has no real application files to test."

Observed: Running `Get-ChildItem api/app` lists real Python application files like `main.py`, `models.py`, `crud.py`, `database.py`, and a `routers` directory containing router modules like `auth.py` and `links.py`. These files implement a fully functioning FastAPI application.

Corrected: The workspace is a functional FastAPI application directory inside the `api` folder, which contains models, schemas, routers, task processing, and database configuration, not just platform metadata/documentation.

## 6. Diagnosis / Why the Agent Got It Wrong

- **Primary Reason**: Insufficient Context / Generalization.
- **Explanation**: The agent made this claim because it only inspected the top-level files of the repository (where only platform metadata files like `AGENTS.md` and `CLAUDE.md` were visible) and did not recursively explore subdirectories. This led it to generalize and assume that no functional application code existed, when in fact a full FastAPI project was nested inside the `api/` directory. Constraining the search context to recursive directories resolves this type of error.

