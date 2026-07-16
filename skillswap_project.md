# Project Case Study: SkillSwap Platform Booking & Onboarding Engine

This document provides a comprehensive planning overview of the **SkillSwap Platform Onboarding & Booking Engine**, describing what was done, how it was done, dependency graph planning, quality checkpoints, and a simplified walkthrough.

---

## 🏗️ Project Breakdown & Planning Framework

```
                          +-------------------------+
                          |  Requirements Analysis  |
                          +------------+------------+
                                       |
                                       v
                          +-------------------------+
                          | Dependency Graph (DAG)  |
                          +------------+------------+
                                       |
                                       v
                          +-------------------------+
                          |   Risk-First Timeline   |
                          +------------+------------+
                                       |
                                       v
                          +-------------------------+
                          |  Thin Vertical Slices   |
                          +------------+------------+
                                       |
                                       v
                          +-------------------------+
                          |   Definition of Done    |
                          +-------------------------+
```

### Detailed Pipeline Explanation
1. **Requirements Analysis:** We build a table mapping stakeholder demands, finding and resolving logic contradictions (like refund cancellation windows) before code is written.
2. **Dependency Graph (DAG):** We build a map showing which modules depend on other modules to ensure the team knows the development critical path and circular loops are avoided.
3. **Risk-First Timeline:** We schedule the scariest or hardest integration tasks (like Stripe payments) at the beginning of the project using mock placeholders so we aren't blocked by external approvals.
4. **Thin Vertical Slices:** We build minimal end-to-end pathways connecting database tables directly to UI screens first. This allows us to verify data flow before building complex dashboards.
5. **Definition of Done:** A final checklist verifying that all merged code passes formatting, unit tests, and PostgreSQL database queries before it can be merged.

---

## ⚠️ Challenges Faced & Rectifications

### 1. Circular Reference blocks in Task dependency graph
* **The Challenge:** The onboarding registration setup and the metrics database reference systems had circular dependencies. Onboarding needed tracking metrics online, while metrics needed completed user profiles. This stalled developer tasks.
* **The Proof:** Task graphs mapped circular loops, showing onboarding tasks blocked by dashboard modules.
* **How it was Rectified:** We decoupled analytics logging from user registration. We created staging databases where registrations write immediately, allowing metrics to load asynchronously without blocking onboarding.

### 2. Testing Database Environment Mismatches
* **The Challenge:** Code passing unit tests on lightweight SQLite databases crashed during staging deployments because production databases were PostgreSQL, which has stricter constraints.
* **The Proof:** Local runs passed successfully, but staging deployments threw database syntax exceptions.
* **How it was Rectified:** Updated the Definition of Done to ban SQLite from unit testing. We mandated that all local integration verification runs execute against Dockerized PostgreSQL databases matching production parameters.

### 3. Stripe payment gateway blocker (Timeline Risks)
* **The Challenge:** Building payment checkouts was blocked because Stripe merchant account setups required credential verifications and took weeks to approve, delaying the project timeline.
* **The Proof:** Payment integration checks failed and code merges were delayed due to missing API keys.
* **How it was Rectified:** Created mock payment stubs that simulate Stripe success/failure payloads locally. This allowed developers to verify booking database states without waiting for Stripe approvals.

---

## Walkthrough

### Part 1: Requirements Mapping (Analogy: Pre-Construction Blueprint)
> *Before building a house, you need a blueprint. In our project, we built a **Requirements Matrix** to extract and evaluate stakeholder rules. We faced a conflict: mentors wanted a 48-hour cancellation notice to protect their time, while students wanted full refunds up to 12 hours before bookings.*
>
> *Instead of writing code that would crash or cause user disputes, we designed a hybrid cancellation policy. We mapped this rule inside our requirements sheet, charging minor cancellation fees on late changes, which satisfied both sides and gave us a clean blueprint to follow.*

### Part 2: Task Graphs and Critical Paths (Analogy: Map Directions)
> *To map out our development schedule, we modeled all system components as a **Directed Acyclic Graph (DAG)**. This is like planning a travel route: you can't visit city C until you pass city B. This graph revealed a circular dependency loop where user registration was blocked by the analytics dashboard, which itself needed user profiles to load.*
>
> *I decoupled this by creating a registration staging table. This allowed registration to complete immediately, while metrics loaded in the background. By clearing this loop, we unblocked developers and shortened our project schedule by two weeks.*

### Part 3: Vertical Slicing and Risk Management (Analogy: Thin Slices)
> *Our biggest risk was Stripe credit card integration, as getting business approvals took weeks. Rather than delay testing, we used a **Risk-First** strategy. We built a mock payment stub that returned simulated checkout approvals locally.*
>
> *This allowed us to construct **Thin Vertical Slices** of our booking system. We built a basic, working pipeline connecting database tables directly to API endpoints, bypassing complex calendar interfaces. This verified database writes and email notifications in week two, rather than waiting for Stripe approvals.*

### Part 4: Enforcing the 'Definition of Done' (Analogy: Safety Inspections)
> *To maintain code quality, I created a strict **Definition of Done (DoD)** checklist. A major risk was database testing inconsistency. Developers tested code using SQLite databases for convenience, which caused PostgreSQL staging databases to throw syntax errors on deployment.*
>
> *I updated the DoD to mandate that all local integration scripts execute against Dockerized PostgreSQL instances. We also required automated verification scripts that assert actual database row changes rather than just checking for HTTP 200 OK headers, ensuring that every merge was fully production-ready.*
