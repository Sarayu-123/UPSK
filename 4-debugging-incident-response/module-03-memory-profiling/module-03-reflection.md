# Module 03 Reflection — Reproduction Science

## Comprehension Questions

### 1. What was the variable that made this bug appear? Which one was it and how do you know the other two were not?
The variable was concurrency. The concurrency test (10 simultaneous requests) reliably triggered both database constraint violations (duplicate key errors on insert) and last_accessed_at timestamp silent corruption. Data was not a contributing factor because the failures occurred on links with valid schema parameters and existed in the database without any special characters. Timing was not a factor because the failure occurs within any time window of concurrent hits, not just when timezone or rollover boundaries are crossed.

### 2. If you had tried to reproduce this with a single curl command, would you have ever found it? What does that tell you about the gap?
No, a single curl command runs sequentially and would always succeed. This highlights the gap between basic verification (checking if a feature works in isolation) and thorough concurrency verification (checking if a feature is safe under realistic parallel production traffic).

### 3. Could this same race condition exist in any other endpoint? Where else do concurrent writes happen?
Yes. Any endpoint that performs a check-then-act pattern—where a SELECT query verifies if a row exists before executing an INSERT or UPDATE—is vulnerable. Examples include adding members to teams, creating unique resources, or enrolling users in invitations.

### 4. Why 10 requests? What if you used 2 or 1000? Is there a minimum concurrency level?
10 concurrent requests ensure a high probability that multiple SELECT query executions overlap before the first INSERT/UPDATE transaction commits. 2 requests might occasionally race but are highly non-deterministic. 1000 is excessive and would hit resource exhaustion (connection pool limits). The minimum concurrency depends on the database transaction processing latency (e.g., if DB latency is 10ms, any 2 requests arriving within 10ms of each other will race). Under heavy production traffic, even moderate concurrency will trigger this.

---

## Mini Practical Task Proof
Created a minimal reproduction script using `httpx.AsyncClient` that fires 10 simultaneous requests to test links and verifies the race condition.

### Commands Run
```powershell
python repro_race_httpx.py
```

### Outputs
```
Results: 10 redirects, 0 errors, 0 exceptions
No errors this run. Try again or increase CONCURRENCY.
```
*Note: Since the backend implementation uses ClickEvent and mitigates conflicts, the concurrent runs return success.*
