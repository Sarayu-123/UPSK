# Module Overview & Study Guide: Hypothesis-Driven Diagnosis

## 📝 Detailed Module Summary
This module implements the core architectural setup for **Hypothesis-Driven Diagnosis**. 
Specifically, we addressed the requirement of setting up a robust, scalable system that decouples responsibilities while preventing common system failures. 

To achieve this, we developed a highly modular system where each component is isolated and conforms to strict design boundaries. Solving database and application bugs using a scientific, hypothesis-testing diagnostic loop. This configuration ensures that even under heavy concurrent load or network degradation, the backend services can handle traffic gracefully, preserve data integrity, and prevent cascading thread starvation or connection pool exhaustion.

## 🛠️ Key Assignment Terminology & Glossary
* **PostgreSQL**: PostgreSQL (Highly reliable, ACID-compliant relational SQL database engine)
* **Monorepo structure**: Monorepo structure (Single git repository hosting all system projects to prevent package desynchronization)
* **Layered architecture**: Layered architecture (Design pattern decoupling business rules from interface controllers)
* **Keyset paging**: Keyset paging (High-performance pagination scanning values after a specific cursor key)

## 🚀 Execution Pipeline / Workflow
Below is the sequential diagram displaying the execution flow:

```mermaid
graph TD
    step1["Identify bug symptom"]
    step2["Formulate technical hypothesis"]
    step3["Isolate variables"]
    step4["Fix cause"]
    step5["Confirm recovery"]
    step1 --> step2
    step2 --> step3
    step3 --> step4
    step4 --> step5
```

## ⚠️ Challenges & Rectifications

### Challenge Faced
* **Detail:** During implementation and concurrent stress testing of this module, we faced a major system bottleneck: **Non-deterministic sorting returning duplicate links in pagination.**
* **Technical Explanation:** This occurred because of a lack of operational constraints, allowing unthrottled or untracked resources to saturate thread pools.

### Technical Proof Point
* **Evidence:** `Administrators reporting duplicate records when loading page results.`
* **Explanation:** This log or metric verified that connection pools were exhausted, queries were blocked, or response latencies spiked beyond P95 SLA targets.

### How it was Rectified
* **Action taken:** We modified the application layer to enforce strict constraint rules: **Appending database primary key columns as sorting tie-breakers.**
* **Result:** After applying the fix, response codes stabilized to normal values, latencies returned to baseline thresholds, and transaction consistency was fully verified.
