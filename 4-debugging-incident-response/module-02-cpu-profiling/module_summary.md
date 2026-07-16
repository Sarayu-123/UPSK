# Module Overview & Study Guide: CPU Bottleneck Profiling

## 📝 Detailed Module Summary
This module implements the core architectural setup for **CPU Bottleneck Profiling**. 
Specifically, we addressed the requirement of setting up a robust, scalable system that decouples responsibilities while preventing common system failures. 

To achieve this, we developed a highly modular system where each component is isolated and conforms to strict design boundaries. Locating CPU-pinning bottlenecks under concurrent traffic using stack trace profilers. This configuration ensures that even under heavy concurrent load or network degradation, the backend services can handle traffic gracefully, preserve data integrity, and prevent cascading thread starvation or connection pool exhaustion.

## 🛠️ Key Assignment Terminology & Glossary
* **cProfile stacks**: cProfile stacks
* **Monorepo structure**: Monorepo structure (Single git repository hosting all system projects to prevent package desynchronization)
* **Layered architecture**: Layered architecture (Design pattern decoupling business rules from interface controllers)
* **APIRouters**: APIRouters (FastAPI modules that namespace routes to split large routing setups into files)

## 🚀 Execution Pipeline / Workflow
Below is the sequential diagram displaying the execution flow:

```mermaid
graph TD
    step1["Inject concurrent traffic"]
    step2["Run profile tracing"]
    step3["Identify recursive backtrack functions"]
    step4["Rewrite with standard library parser"]
    step1 --> step2
    step2 --> step3
    step3 --> step4
```

## ⚠️ Challenges & Rectifications

### Challenge Faced
* **Detail:** During implementation and concurrent stress testing of this module, we faced a major system bottleneck: **Backtracking recursion loops pinning CPU at 100% under concurrent traffic.**
* **Technical Explanation:** This occurred because of a lack of operational constraints, allowing unthrottled or untracked resources to saturate thread pools.

### Technical Proof Point
* **Evidence:** `Load tests showing connection timeouts and high CPU usage.`
* **Explanation:** This log or metric verified that connection pools were exhausted, queries were blocked, or response latencies spiked beyond P95 SLA targets.

### How it was Rectified
* **Action taken:** We modified the application layer to enforce strict constraint rules: **Replacing nested recursions with standard Python libraries.**
* **Result:** After applying the fix, response codes stabilized to normal values, latencies returned to baseline thresholds, and transaction consistency was fully verified.
