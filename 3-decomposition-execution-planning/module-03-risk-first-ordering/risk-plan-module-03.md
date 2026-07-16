# Module 03 – Risk-First Ordering (SkillSwap)

This document contains the risk annotations for all 14 work items identified in Module 02, followed by a prioritized, dependency-respecting build order designed to retire the highest-risk items as early as possible.

---

## 1. Risk Annotations

Every work item is annotated with a **Risk Score (1–5)** and **Risk Type(s)**:
*   **Risk Scores**:
    *   `1`: Low uncertainty / Standard CRUD (done this exact thing before)
    *   `2`: Familiar pattern, minor unknowns
    *   `3`: Research required, some novel elements or scaling parameters
    *   `4`: Significant unknowns, concurrency or design risks
    *   `5`: Major unknown (third-party integration, critical path blocker)
*   **Risk Types**: `Integration`, `Novelty`, `Dependency`, `Scale`, `Business` (NEW: External entity/merchant blocker).

| Work Item | Risk Score | Risk Type | Description |
| :--- | :---: | :--- | :--- |
| **WI-01: User Authentication & Accounts** | **1** | Dependency | Well-understood problem with library support, but holds maximum incoming dependency. |
| **WI-02: Provider Profile Setup** | **1** | Dependency | Standard CRUD configuration for provider profiles. Low risk, but foundational. |
| **WI-03: Provider Vetting & Approval** | **2** | Novelty | Multi-step state machine managing vetting status (Pending, Vetted, Rejected). |
| **WI-04: Availability Management** | **3** | Novelty | Complex calendar configuration, draft/active slots, and scheduling rules. |
| **WI-05: Provider Discovery & Search** | **3** | Scale | Requirements for "feel instant" responses with filter/category configurations. |
| **WI-06: Booking Engine** | **4** | Novelty, Dependency | Concurrency control, double-booking prevention, and reservation state machine. |
| **WI-07: Payment Processing (Stubbed)** | **2** | Novelty | Implemented via a stub/mock interface to allow system-wide testing. (Reduced from 5). |
| **WI-08: Commission & Settlement (Mocked)**| **2** | Novelty | Multi-recipient ledger calculations based on stubbed transaction records. |
| **WI-09: Cancellation & Refunds (Mocked)**| **2** | Novelty | Policy enforcement logic built on top of the mock payment contract. |
| **WI-10: Notifications** | **2** | Integration | Third-party email/SMS provider integrations. |
| **WI-11: Provider Dashboard** | **1** | None significant | Aggregation of existing bookings, reviews, and earnings data. |
| **WI-12: Ratings, Reviews & Moderation** | **2** | Novelty | User ratings, review text submissions, flag thresholds, and moderator queue. |
| **WI-13: Admin Review Tool (Minimal)** | **2** | Dependency | Critical path tool enabling admin review of uploaded background/credential checks. |
| **WI-14: Admin Dashboard (Full)** | **2** | Scale | Analytical charts, aggregation queries, and reporting over platform metrics. |
| **WI-15: Stripe Payment Integration (NEW)**| **5** | Business, Integration| **BLOCKED** — Waiting on the client's merchant account and business entity registration. |

---

## 2. Revised Numbered Build Order (Mitigating the Business Blocker)

To prevent the team from grinding to a halt, we have introduced a **mock/stub interface** for payments. This isolates the blocked Stripe code, allowing the Booking Engine, Refunds, and Dashboards to be built and tested end-to-end against a predictable contract.

1.  **WI-01: User Authentication & Accounts** (Risk: 1, Type: Dependency)
    *   *Justification*: Foundational starting point. Low technical risk, but a hard dependency.
2.  **WI-02: Provider Profile Setup** (Risk: 1, Type: Dependency)
    *   *Justification*: Needed to establish provider records in the database. Precursor to scheduling, discovery, and vetting.
3.  **WI-04: Availability Management** (Risk: 3, Type: Novelty)
    *   *Justification*: Pre-vetting setup. Moved up in active focus. Testing calendar data models and scheduling constraints before activation.
4.  **WI-13: Admin Review Tool (Minimal)** (Risk: 2, Type: Dependency)
    *   *Justification*: Hard dependency. Simple interface to review provider submissions.
5.  **WI-03: Provider Vetting & Approval** (Risk: 2, Type: Novelty)
    *   *Justification*: Vetting state machine. Transitioning availability from Draft to Active upon approval.
6.  **WI-05: Provider Discovery & Search** (Risk: 3, Type: Scale)
    *   *Justification*: Gateway to booking. Testing search performance and filters.
7.  **WI-06: Booking Engine** (Risk: 4, Type: Novelty, Dependency)
    *   *Justification*: Concurrency control, double-booking prevention. Highly critical path; will connect to the stubbed payment interface.
8.  **WI-07: Payment Processing (Stubbed Contract)** (Risk: 2, Type: Novelty)
    *   *Justification*: **Plan Adjustment**. We build the interface contract and a stub implementation (always returns success/mocked decline) to unblock the Booking flow.
9.  **WI-09: Cancellation & Refunds (Mocked)** (Risk: 2, Type: Novelty)
    *   *Justification*: Business policy rules for refunds. Built against the payment stub.
10. **WI-08: Commission & Settlement (Mocked)** (Risk: 2, Type: Novelty)
    *   *Justification*: Marketplace accounting logic. Built against mock transaction tables.
11. **WI-12: Ratings, Reviews & Moderation** (Risk: 2, Type: Novelty)
    *   *Justification*: User feedback loops and moderation workflow.
12. **WI-10: Notifications** (Risk: 2, Type: Integration)
    *   *Justification*: Alerts triggered by simulated booking/payment state changes.
13. **WI-11: Provider Dashboard** (Risk: 1, Type: None)
    *   *Justification*: Dashboard displaying analytics based on mocked booking/earning history.
14. **WI-14: Admin Dashboard (Full)** (Risk: 2, Type: Scale)
    *   *Justification*: Platform analytics reporting.
15. **WI-15: Stripe Payment Integration (Real)** (Risk: 5, Type: Business, Integration)
    *   *Justification*: **BLOCKED**. Placed at the very end. The real Stripe Connect API integration, webhook verification, and legal merchant activation will be swapped in once the client resolves the business registration blockers.
