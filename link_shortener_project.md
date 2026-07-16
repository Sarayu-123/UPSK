# Project Case Study: Link Shortener API & Redirect Router System

This document provides a comprehensive, end-to-end overview of the **Link Shortener API & Redirect Router System**, describing what was done, how it was done, the architectural layout, real production outages, and a simplified walkthrough.

---

## 🏗️ System Architecture & Data Flow

```
                      +-------------------+
                      |   Client Browser  |
                      +---------+---------+
                                |
             GET /slug          |         HTTP 302 Redirect
             (User Click)       |         (Target URL)
                                v
                      +---------+---------+
                      |   FastAPI Router  |
                      +----+---------+----+
                           |         ^
          1. Query Cache   |         | 2. Cache Hit (Fast Return)
                           v         |
                      +----+---------+----+
                      |    Redis Cache    |
                      +----+---------+----+
                           |         
          3. Cache Miss    |         
          (Read Postgres)  v         
                      +----+---------+----+
                      | PostgreSQL DB     |
                      +----+---------+----+
                           |
          4. Record Hit    | (Writeback Cache & Dispatch Event)
                           v
                      +----+---------+----+
                      |    Redis Broker   |
                      +---------+---------+
                                |
                                | (Out-of-band Message Task)
                                v
                      +---------+---------+
                      |   Celery Worker   |
                      +---------+---------+
                                |
                                | (Async analytics write)
                                v
                      +---------+---------+
                      | PostgreSQL DB     |
                      +-------------------+
```

### Detailed Pipeline Explanation
1. **User Request (GET /slug):** The user clicks a short link. The request goes to our FastAPI application.
2. **Step 1 (Check Quick Cache Memory):** The application looks inside our Redis Cache (a very fast temporary memory helper) to see if we already know where this link goes.
3. **Step 2 (Immediate Return):** If the cache knows it, we immediately forward the user to their target site. This takes less than 2 milliseconds!
4. **Step 3 & 4 (Check Main Filing Cabinet):** If the cache doesn't know it, we query our PostgreSQL Database (our main filing cabinet). We retrieve the link, write a copy of it into our Redis cache so the next request is super fast, and redirect the user.
5. **Step 5 (Background Recording):** At the same time, we send a quick message to our Redis Broker (a task dispatcher). A separate Celery Worker (a background helper) picks up this message and writes details about the click (like IP and time) into the database, without making the user wait.

---

## ⚠️ Challenges Faced & Rectifications

### 1. CPU Starvation loops from Wildcard URL Searches (ReDoS)
* **The Challenge:** Our search helper verifying target URLs got stuck in infinite loops when users entered malformed URLs with nested patterns, pinning the CPU at 100% and crashing the application.
* **The Proof:** Gunicorn log outputs showed `WORKER TIMEOUT` errors and CPU usage spiked to 100% on Gunicorn threads.
* **How it was Rectified:** We set a 2048-character length limit on all URL inputs to prevent long strings from overloading the system, and replaced complex regular expressions with standard Python web-address checkers (`urllib.parse`), ensuring linear execution times.

### 2. Saturated Database Connection memory leaks (OOM)
* **The Challenge:** Database sessions created during API queries were not closed when requests encountered errors. The connection pool saturated, locked database files, and crashed containers with Out-Of-Memory (OOM) errors.
* **The Proof:** Server prints logged `FATAL: remaining connection slots are reserved` errors and containers exited with OOM codes.
* **How it was Rectified:** We wrapped all database connection queries in automatic context managers (`with get_db()`) and FastAPI dependencies, guaranteeing that connections close immediately under all success and exception paths.

### 3. Concurrent Write Race Conditions (Duplicate Slugs)
* **The Challenge:** Multiple threads attempting to generate the same short slug concurrently threw database unique constraint failures, locking database session commits.
* **The Proof:** Database logs recorded `sqlalchemy.exc.IntegrityError: duplicate key value violates unique constraint`.
* **How it was Rectified:** We created unique database constraints on slug code columns. We added try-except blocks that execute `db.rollback()` on IntegrityError failures, clearing database locks and running a retry loop to generate a fresh slug.

---

## Walkthrough

### Part 1: System Concept & Background (Analogy: High-Speed Memo Memory)
> *Imagine a busy receptionist forwarding calls. In my project, I built a high-speed system that redirects users to target URLs in under 2 milliseconds. To do this, I used **FastAPI** (a high-speed web gateway) and **Redis** (a super-fast, temporary memo memory pad).*
>
> *When a request arrives, the receptionist checks the memo pad first. If it's written there, they forward the call immediately. If not, they open the main **PostgreSQL** filing cabinet, find the file, write a sticky note on the Redis memo pad so they remember it next time, and forward the call. To prevent the receptionist from getting bogged down writing log details, we used a background assistant called **Celery** to write down analytics details asynchronously, ensuring the client receives their redirect immediately.*

### Part 2: Database and Caching Decisions (Analogy: Constant-Time Sorting)
> *To track our database models and updates, we used a version-control tool called **Alembic**. When users request lists of their links, standard systems scan all files from start to finish, which gets slower as more files are added. To prevent this, I built **Keyset Pagination**, which acts like a catalog cursor. It queries records starting precisely after the last seen index, ensuring loading times remain identical whether you are loading page 1 or page 1000.*
>
> *Additionally, we configured the background worker system with a fail-safe fallback timeout. If the Redis task dispatcher drops connection or slows down, the API receptionist waits for only 200 milliseconds before skipping logging and completing the client's redirect. This keeps the core redirect flow online even during background database failures.*

### Part 3: Overcoming Heavy Load Crashes (Analogy: Input Constraints & Auto-Closes)
> *During load testing, we faced two critical failures. First, malformed input URLs caused Gunicorn workers to freeze and pinned the CPU at 100%. I used profiling tools and isolated the issue to a regular expression validator getting stuck in backtrack loops. I resolved this by capping inputs to 2048 characters and replacing complex regex rules with standard Python URL checkers.*
>
> *Second, we ran out of database connection slots under high load, causing memory leaks and container crashes. I traced the issue to unclosed database session variables in exception handlers. I wrapped all database handlers inside automatic context managers, which act like self-closing doors, guaranteeing that connections close immediately when requests finish or fail.*

### Part 4: Production Operations (Analogy: Multi-Stage Security Gates)
> *For hosting, I built a secure **multi-stage Docker container**. This is like a security checkpoint where compiler tools build python wheels inside a secure zone, and then copy only the lightweight, compiled files into a **Debian slim** container running under a restricted non-root user (`appuser`). This reduced the container footprint to 180MB and secured it against unauthorized shell escapes.*
>
> *Lastly, we integrated a **Readiness Probe** route `/ready`. Unlike basic checkers that just verify the server is running, `/ready` actively asserts read and write connectivity against both Redis and PostgreSQL database files. If database writes fail or replica databases freeze in read-only modes, the probe returns HTTP 503, signaling the load balancer to cleanly isolate the pod from client traffic.*
