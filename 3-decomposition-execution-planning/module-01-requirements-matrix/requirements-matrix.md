# Requirements Matrix - SkillSwap

This requirements document uses a **Categorized Matrix** structure, organizing the extracted requirements by **Stakeholder** and **Requirement Type** (Functional, Constraint, and Quality Attribute).

---

## Stakeholder: User (Learner)

### Functional Requirements
*   **REQ-01: Browse Providers by Category**
    *   *Description:* Learners must be able to filter and browse service providers by their predefined categories.
    *   *Source:* Paragraph 1 (Explicit)
    *   *Confidence:* High
*   **REQ-02: View Provider Profiles and Ratings**
    *   *Description:* Learners must be able to view details of a provider's profile, including services, pricing, availability, and rating/review history.
    *   *Source:* Paragraph 1 (Explicit)
    *   *Confidence:* High
*   **REQ-03: Book Time Slots**
    *   *Description:* Learners must be able to reserve a specific, available time slot on a provider's schedule.
    *   *Source:* Paragraph 1 (Explicit)
    *   *Confidence:* High
*   **REQ-04: Pay Through Platform**
    *   *Description:* Learners must be able to pay for the booked sessions using integrated payment gateways on the platform.
    *   *Source:* Paragraph 1 (Explicit)
    *   *Confidence:* High
*   **REQ-05: Receive Confirmations**
    *   *Description:* Learners must receive confirmation notifications (e.g., email) immediately after a booking is successfully made and paid.
    *   *Source:* Paragraph 1 (Explicit)
    *   *Confidence:* High
*   **REQ-06: Cancel Booking [BLOCKED - pending PM decision]**
    *   *Description:* Learners must be able to cancel bookings. This is currently blocked due to a logical contradiction between provider-level cancellation policies and a platform-wide 24-hour refund mandate.
    *   *Source:* Paragraph 1 (Explicit)
    *   *Confidence:* High

### Constraints
*   **REQ-07: Guest Browsing Restriction**
    *   *Description:* Unauthenticated users (guests) can browse and view profiles, but must authenticate/create an account before booking or paying.
    *   *Source:* Implicit (Silence Pass)
    *   *Confidence:* Medium

### Quality Attributes
*   **REQ-08: Instant Search Performance**
    *   *Description:* Search and filtering of providers should feel instant (latency under a defined threshold, e.g., < 200ms) under target load.
    *   *Source:* Paragraph 2 (Explicit)
    *   *Confidence:* High

---

## Stakeholder: Provider (Instructor)

### Functional Requirements
*   **REQ-09: Publish Services and Profile Descriptions**
    *   *Description:* Providers can publish their list of services, pricing, availability calendars, and biography/profile descriptions.
    *   *Source:* Paragraph 1 & 2 (Explicit)
    *   *Confidence:* High
*   **REQ-10: Set Availability and Pricing**
    *   *Description:* Providers must have full autonomy to configure their own session pricing rates and active calendar availability.
    *   *Source:* Paragraph 2 (Explicit)
    *   *Confidence:* High
*   **REQ-11: Set Cancellation Policies [BLOCKED - pending PM decision]**
    *   *Description:* Providers can configure their own custom cancellation policies. This is blocked pending the selection of the platform refund policy model (Option A removes provider autonomy; Option B retains it with a platform safeguard floor).
    *   *Source:* Paragraph 2 (Explicit)
    *   *Confidence:* High
*   **REQ-12: View Bookings, Earnings, and Reviews**
    *   *Description:* Providers must have a dashboard that shows current/past bookings, earnings summary, and ratings/reviews left by learners.
    *   *Source:* Paragraph 2 (Explicit)
    *   *Confidence:* High
*   **REQ-13: Flag No-Show Users**
    *   *Description:* Providers must have a mechanism to flag or report learners who do not show up for scheduled sessions.
    *   *Source:* Paragraph 2 (Explicit)
    *   *Confidence:* High

### Constraints
*   **REQ-14: Vetting Approval Required**
    *   *Description:* Providers cannot publish services or be visible in search results until they have been successfully vetted and approved by platform administrators.
    *   *Source:* Paragraph 2 (Explicit)
    *   *Confidence:* High

---

## Stakeholder: Platform / Operations (Admin)

### Functional Requirements
*   **REQ-15: Vet New Providers**
    *   *Description:* Admins/Ops must have a workflow to review credentials, verify profiles, and approve/reject new providers.
    *   *Source:* Paragraph 2 (Explicit)
    *   *Confidence:* High
*   **REQ-16: Resolve Disputes**
    *   *Description:* Admins must have a dispute resolution workflow to handle escalated booking or cancellation disputes between users and providers.
    *   *Source:* Paragraph 3 (Explicit)
    *   *Confidence:* High
*   **REQ-17: Track and Measure Platform Analytics**
    *   *Description:* The platform must capture metrics on all search actions, bookings, transaction values, and user engagement.
    *   *Source:* Paragraph 3 (Explicit)
    *   *Confidence:* High
*   **REQ-18: Manage Provider Payouts**
    *   *Description:* The platform must process payouts of the remaining 85% of transaction values to providers on a set schedule.
    *   *Source:* Implicit (Silence Pass)
    *   *Confidence:* Medium

### Constraints
*   **REQ-19: 15% Platform Commission**
    *   *Description:* The platform must automatically deduct a flat 15% commission from provider earnings on all successful bookings.
    *   *Source:* Paragraph 2 (Explicit)
    *   *Confidence:* High
*   **REQ-20: Prevent Time-Slot Double-Booking**
    *   *Description:* The system must prevent double-booking of any time slots via database transaction locks (e.g., serializable isolation).
    *   *Source:* Paragraph 2 (Explicit)
    *   *Confidence:* High
*   **REQ-21: Multi-City Database Architecture (No Rebuild)**
    *   *Description:* The database schema and code must support expanding from one city to five cities within six months without requiring a complete rebuild.
    *   *Source:* Paragraph 3 (Explicit)
    *   *Confidence:* High
*   **REQ-22: Security and Role-Based Access Control**
    *   *Description:* The system must secure endpoints, encrypt sensitive payment data, and enforce role separation (Learner, Provider, Admin).
    *   *Source:* Implicit (Silence Pass)
    *   *Confidence:* High

### Quality Attributes
*   **REQ-23: Platform Scalability**
    *   *Description:* The platform must support at least a few thousand active concurrent users in each city while maintaining search and booking performance.
    *   *Source:* Paragraph 3 (Explicit)
    *   *Confidence:* High

---

## Ambiguities and Open Questions

1.  **Timezone Handling for Multi-City Schedule Alignment**
    *   *Question:* As the system expands to multiple cities, how will time zones be standardized? When a provider in City A (e.g., Eastern Time) schedules a session with a learner in City B (e.g., Pacific Time), will the time slots be presented in the user's local timezone, the provider's timezone, or a single platform timezone?
2.  **Commission Structure Uniformity**
    *   *Question:* Does the 15% platform commission apply uniformly to all categories and providers, or does the system need to support custom commission rates (e.g., promotional periods, or higher rates for unvetted/new providers)?
3.  **Cancellation Policy Enforcement and Refund Automation [BLOCKED - pending PM decision]**
    *   *Question:* How should the platform resolve the contradiction between the provider's cancellation policy and the platform's refund policy? Proposing two options:
        *   *Option A (Platform-First):* Flat policy (100% refund < 24 hours, no refund after). Affects REQ-06, REQ-11, and simplifies UI/UX/refund automation, but removes provider autonomy.
        *   *Option B (Provider Policy with Platform Floor):* Provider defines policy, but platform guarantees a safety window (e.g., 1-hour cooling off period). Increases implementation complexity (policy engine, dynamic UI rules, commission logic).
    *   *Impacted Flows:* REQ-11 (Provider policy configuration), REQ-18 (Provider payout calculations & commission refunds), and the Provider Dashboard.
4.  **Escrow and Payout Timing**
    *   *Question:* When is the provider's portion (85%) disbursed? Is it transferred immediately upon learner payment, or is it held in escrow until the session is completed or verified?
