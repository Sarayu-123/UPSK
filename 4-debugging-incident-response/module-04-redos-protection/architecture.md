# 7-Step Architectural Lifecycle Sheet: ReDoS Protection

This sheet maps the architectural execution lifecycle of **ReDoS Protection** using the 7-step system framework.

---

## 🔴 1. Context
We initiated this module to resolve architectural demands in the CAW monorepo:
* **Background:** Hardening inputs against Regular Expression Denial of Service (ReDoS) backtracking attacks.
* **Goal:** Build a highly stable component integration that complies with system requirements and operates within safe latency thresholds.

---

## 🔵 2. Decide
We evaluated design alternatives and made the following technical decisions:
* **Primary Design Driver:** We chose **Catastrophic regex backtracking (CPU starvation loops caused by nested wildcards in regex engines)** to enforce structural boundaries.
* **Alternative Considered:** We rejected alternative looser designs to prevent data inconsistencies, route collisions, or cascading latency spikes.
* **Reasoning:** Track CPU pinning provides a deterministic, type-checked contract that simplifies debugging and guarantees data consistency.

---

## 🟢 3. Build
We built and structured the following elements in the codebase:
* **Implementation Plan:** We executed **Set 2048-character length limits**.
* **Files Affected:** We created or modified the core Python files and schemas, implementing declarative schemas, configuration settings, and clean middleware hooks.

---

## 🟣 4. Verify
We validated the build using the following verification steps:
* **Verification Method:** Replace regex with linear string matching
* **Successful Proof:** The execution log printed successful response codes and confirmed that transactions were processed within SLA boundaries.

---

## 🟡 5. Break
Under concurrent stress tests or invalid payloads, the system encountered this failure mode:
* **Incident Mode:** **Regex backtracking allowing malicious inputs to lock up the API.**
* **Technical Evidence:** `Malicious inputs with trailing characters causing CPU usage spikes.`
* **Impact:** Threads locked, connections saturated, or execution was temporarily blocked, leading to performance drops.

---

## 🔵 6. Fix
We resolved the system failure mode by applying the following hotfix:
* **Mitigation / Repair:** **Rejecting inputs exceeding 2048 characters and using linear string matching.**
* **Result:** Re-running the validation suite showed clean exit codes, stable latencies, and confirmed that threads were protected from resource starvation.

---

## 💗 7. Reflect
* **Key Architecture Lesson:** Always enforce **Catastrophic regex backtracking** constraints dynamically. When designing high-throughput systems, isolating dependencies and using explicit type validation prevents bugs from propagating through the application.
* **Future Recommendation:** Integrate these constraint validations directly in the pre-commit checks and CI pipelines to prevent regression drift.
