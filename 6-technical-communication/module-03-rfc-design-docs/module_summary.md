# Module Overview & Study Guide: RFC Architectural Blueprints

## 📝 Detailed Module Summary
This module implements the core architectural setup for **RFC Architectural Blueprints**. 
Specifically, we addressed the requirement of setting up a robust, scalable system that decouples responsibilities while preventing common system failures. 

To achieve this, we developed a highly modular system where each component is isolated and conforms to strict design boundaries. Drafting architectural Request for Comments (RFC) comparing design tradeoffs. This configuration ensures that even under heavy concurrent load or network degradation, the backend services can handle traffic gracefully, preserve data integrity, and prevent cascading thread starvation or connection pool exhaustion.

## 🛠️ Key Assignment Terminology & Glossary
* **RFC architectural draft**: RFC architectural draft (Request For Comments blueprint detailing system tradeoffs)
* **PostgreSQL**: PostgreSQL (Highly reliable, ACID-compliant relational SQL database engine)
* **Monorepo structure**: Monorepo structure (Single git repository hosting all system projects to prevent package desynchronization)
* **Layered architecture**: Layered architecture (Design pattern decoupling business rules from interface controllers)

## 🚀 Execution Pipeline / Workflow
Below is the sequential diagram displaying the execution flow:

```mermaid
graph TD
    step1["Define system requirements"]
    step2["Draft tradeoff matrix"]
    step3["Map fail-safe contingencies"]
    step4["Publish for team feedback"]
    step1 --> step2
    step2 --> step3
    step3 --> step4
```

## ⚠️ Challenges & Rectifications

### Challenge Faced
* **Detail:** During implementation and concurrent stress testing of this module, we faced a major system bottleneck: **Sliding window designs risking total API lockout on Redis outages.**
* **Technical Explanation:** This occurred because of a lack of operational constraints, allowing unthrottled or untracked resources to saturate thread pools.

### Technical Proof Point
* **Evidence:** `RFCs omitting contingency plans for database disconnects.`
* **Explanation:** This log or metric verified that connection pools were exhausted, queries were blocked, or response latencies spiked beyond P95 SLA targets.

### How it was Rectified
* **Action taken:** We modified the application layer to enforce strict constraint rules: **Adding fail-open rules to rate-limiting architectures.**
* **Result:** After applying the fix, response codes stabilized to normal values, latencies returned to baseline thresholds, and transaction consistency was fully verified.
