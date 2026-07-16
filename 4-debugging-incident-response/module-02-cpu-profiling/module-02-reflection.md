# Module 02 Reflection — Reading Logs Like a Story

## Comprehension Questions

### 1. What core problem does this module solve in reading logs like a story?
It solves the problem of logs as a trust boundary and lack of trace integrity. Without log sanitization, attackers can inject newline characters (`\n`) into input fields, allowing them to forge arbitrary log lines (e.g., fake admin actions or successful logins), compromising audit integrity. Additionally, inconsistencies in log levels and timestamp timezones across components prevent debugging teams from building a clear, coherent timeline of incidents.

### 2. Which decision in this module has the biggest impact, and why?
The choice of log verbosity in production (Option A: Verbose by default vs. Option B: Minimal by default). Option B (Minimal by default) protects the system from log noise and performance degradation but introduces a blind spot in recording normal execution flow (INFO events), which can hide evidence of attacks. Option A ensures maximum context is recorded but can overwhelm log indexes, making anomalies harder to find and creating extra camouflage for attackers.

### 3. What evidence proves the implementation works end-to-end?
The field validators `validate_long_url` in both `LinkCreate` and `LinkUpdate` (located in `api/app/schemas.py`) replace `\n` and `\r` with empty strings and return a parsed `HttpUrl` object. When creating a link with a payload containing newlines, the newlines are stripped, and the logs record a single sanitized log line without forging new log lines.

---

## Mini Practical Task Proof
Verified that creating a link with newline characters does not result in log injection and that the url is correctly sanitized.

### Verification Action
Curled the link creation endpoint with newlines in long_url and verified that the response stripped the newlines and did not result in newline logs in the application container logs.

### Proof
```json
{
  "long_url": "https://example.com/path?param=val"
}
```
Validation strips all `\n` and returns the sanitized HTTP URL.
