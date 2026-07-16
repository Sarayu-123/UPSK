# Project Case Study: Analytics Dashboard & Operational Runbooks System

This document provides a comprehensive overview of the **Analytics Dashboard & Operational Runbooks System**, describing what was done, how it was done, AI-augmented engineering context setups, technical runbooks, and a simplified walkthrough.

---

## 🏗️ AI-Augmented Engineering & Technical Communication Framework

```
                          +-------------------------+
                          |   Context Engineering   |
                          +------------+------------+
                                       |
                                       v
                          +-------------------------+
                          | Multi-Agent Delegation  |
                          +------------+------------+
                                       |
                                       v
                          +-------------------------+
                          |   Architecture RFCs     |
                          +------------+------------+
                                       |
                                       v
                          +-------------------------+
                          |  Blameless Postmortem   |
                          +------------+------------+
                                       |
                                       v
                          +-------------------------+
                          | Troubleshooting Runbook |
                          +-------------------------+
```

### Detailed Pipeline Explanation
1. **Context Engineering:** We write guidelines and style manuals to define system coding rules so our AI coding assistants write clean, compile-compliant code.
2. **Multi-Agent Task Delegation:** We break down complex coding tasks and delegate files to specialized worker agents, coordinating their changes through interface contracts.
3. **Architecture RFCs:** We document system blueprints and tradeoff matrices to map out design options (like Redis vs local memory) before writing code.
4. **Blameless Postmortem:** Following an outage, we draft a blameless timeline to analyze system failure points without blaming operators.
5. **Troubleshooting Runbooks:** We write emergency manuals with copy-pasteable scripts to ensure system recovery commands include explicit namespace arguments.

---

## ⚠️ Challenges Faced & Rectifications

### 1. Code Drift and Compilation failures in AI-generated code
* **The Challenge:** Our AI generator suffered from context drift during model updates, writing deprecated configurations and invalid database schemas that caused compiler errors.
* **The Proof:** Codebase builds failed and compiler outputs logged syntax errors due to invalid model imports.
* **How it was Rectified:** Created task-specific context packages containing directory-specific conventions and schemas. We added warning banners to prompt windows to block obsolete database libraries.

### 2. Rate-Limiter Outages (RFC Design Decisions)
* **The Challenge:** Our sliding-window rate limiter was configured to write tracking metrics to Redis. When Redis went offline, the rate limiter failed closed, locking all users out of the application.
* **The Proof:** Clients received 500 Server Error pages during Redis database outages.
* **How it was Rectified:** Drafted an architectural RFC setting up a fail-open path. If Redis connection pings fail, the rate limiter falls back to local in-memory sliding counters, preserving API availability while logging warnings to Slack.

### 3. Namespace Rollback Errors during Incident Recoveries
* **The Challenge:** During database outages, operators executed rollback scripts on the default namespace instead of the production namespace, causing a data wipe on staging databases.
* **The Proof:** Staging database tables were wiped during live production recovery drills.
* **How it was Rectified:** Authored troubleshooting runbooks that explicitly declare the namespace flag (`-n orderflow`) on all copy-pasteable commands, securing databases from out-of-scope executions.

---

## Walkthrough

### Part 1: AI-Augmented Engineering (Analogy: Specialized Workers)
> *In this project, I designed the AI-Augmented refactoring pipeline for our Analytics Dashboard. Rather than sending vague prompts to coding assistants, I implemented **Context Engineering**.*
>
> *I created style guidelines and structured them into directory-specific folders. To handle codebase modifications across multiple directories, I used a **Coordinator-Worker pattern**. This is like a project manager dividing task cards and assigning them to specialized workers. The coordinator reviewed worker changes against schemas to ensure that code complied with our conventions before merging.*

### Part 2: Codebase Search & Context Formatting (Analogy: Index Directories)
> *When refactoring database schemas, AI models often wrote outdated code because of too much prompt noise. I resolved this by utilizing regex codebase searches to map file dependencies.*
>
> *This allowed us to build **Task-Specific Context Bundles**, packing only the required database model files into the AI context window. We added warning banners at the top of these context files, reminding the model to avoid obsolete imports. This eliminated compiler syntax errors and reduced token usage.*

### Part 3: Architecture RFC Blueprints (Analogy: Blueprints & Tradeoffs)
> *To design a stable rate-limiting middleware, I authored an **Architecture RFC**. This is a design blueprint describing requirements, rate-limiting algorithms, and tradeoffs.*
>
> *I built a **Tradeoff Matrix** comparing Redis storage (which supports multi-node sync but adds network lag) against local memory (which has zero network lag but doesn't sync across servers). I documented a fail-safe strategy: the rate limiter uses Redis as the primary database, but falls back to local memory if Redis goes offline. This preserved API availability during database outages.*

### Part 4: Operational Postmortems and Runbooks (Analogy: Fire Drills)
> *Following a database incident, I led a **Blameless Postmortem**. We mapped out a timeline of system events using server logs, focusing on system weaknesses rather than pointing fingers at developers. We created owned, deadlined Jira action items to fix replication configurations.*
>
> *To prevent human errors during recoveries, I authored step-by-step **Troubleshooting Runbooks**. We made sure all commands included explicit namespace arguments (`-n orderflow`) to block operators from running scripts in the wrong database environment, securing our databases.*
