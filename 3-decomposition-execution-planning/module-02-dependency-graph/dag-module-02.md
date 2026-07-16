# Module 02 – Dependency Mapping (SkillSwap)

## Work Items

### WI-01: User Authentication & Accounts
* User registration
* User login
* Session management

### WI-02: Provider Profile Setup
* Provider profile creation
* Service descriptions
* Pricing configuration

### WI-03: Provider Vetting & Approval
* Vetting workflow
* Approval/rejection process
* Provider activation status

### WI-04: Availability Management
* Calendar setup
* Time slot creation
* Availability updates
* Draft vs Active scheduling

### WI-05: Provider Discovery & Search
* Category browsing
* Search functionality
* Profile viewing
* Ratings display

### WI-06: Booking Engine
* Slot reservation
* Booking lifecycle
* Double-booking prevention

### WI-07: Payment Processing
* Payment collection
* Payment status tracking
* Transaction records

### WI-08: Commission & Settlement
* Platform commission calculation
* Provider earnings
* Settlement reporting

### WI-09: Cancellation & Refunds
* Cancellation workflow
* Refund calculation
* Policy enforcement

### WI-10: Notifications
* Booking confirmations
* Cancellation emails
* Payment notifications

### WI-11: Provider Dashboard
* Upcoming bookings
* Earnings dashboard
* Reviews dashboard

### WI-12: Ratings, Reviews & Moderation
* Ratings
* Reviews
* No-show flagging
* Moderation workflow

### WI-13: Admin Review Tool (Minimal)
* View pending provider applications
* View uploaded credentials
* View background check status
* Approve / Reject provider

### WI-14: Admin Dashboard (Full)
* Analytics
* Provider management
* Dispute management
* Operational reporting
* Administrative charts

---

# Visual DAG

```text
                              [WI-01 Auth]
                                     |
                                     | H
                                     v
                     +-----------------------------+
                     | WI-02 Provider Setup        |
                     +-----------------------------+
                         | H                 | H
                         |                   |
                         v                   v
            +------------------+   +----------------------+
            | WI-04 Availability|   | WI-13 Admin Review   |
            | (Draft State)     |   | Tool (Minimal)       |
            +------------------+   +----------------------+
                                            |
                                            | H
                                            v
                                 +----------------------+
                                 | WI-03 Provider       |
                                 | Vetting & Approval   |
                                 +----------------------+
                                            |
                                            | H
                                            v
                                 +----------------------+
                                 | Provider Activation  |
                                 +----------------------+
                                            |
                                            | H
                                            v
                                 +----------------------+
                                 | WI-05 Discovery      |
                                 +----------------------+
                                            |
                                            | H
                                            v
                                 +----------------------+
                                 | WI-06 Booking Engine |
                                 +----------------------+
                                      /    |      \
                                     /     |       \
                                    H      S        S
                                   /       |         \
                                  v        v          v
                        +--------------+ +--------------+
                        | WI-07 Payment| | WI-10 Notify |
                        +--------------+ +--------------+
                                |
                                | H
                                v
                        +------------------+
                        | WI-08 Commission |
                        +------------------+
                                |
                                | S
                                v
                        +------------------+
                        | WI-11 Dashboard  |
                        +------------------+

WI-06 Booking ------------------> WI-09 Cancellation (H)
WI-09 Cancellation -------------> WI-07 Payment (H)

WI-06 Booking ------------------> WI-12 Reviews (H)
WI-12 Reviews ------------------> WI-05 Discovery (S)

WI-02 Provider Setup -----------> WI-14 Admin Dashboard (S)
WI-03 Provider Vetting ---------> WI-14 Admin Dashboard (S)
```

---

# Dependency List

## Hard Dependencies (H)
* WI-01 → WI-02
* WI-02 → WI-13
* WI-13 → WI-03
* WI-03 → Provider Activation
* WI-02 → WI-04
* WI-04 → Provider Activation
* Provider Activation → WI-05
* WI-05 → WI-06
* WI-06 → WI-07
* WI-06 → WI-09
* WI-09 → WI-07
* WI-07 → WI-08
* WI-06 → WI-12

## Soft Dependencies (S)
* WI-06 → WI-10
* WI-07 → WI-10
* WI-08 → WI-11
* WI-12 → WI-05
* WI-12 → WI-11
* WI-02 → WI-14
* WI-03 → WI-14

---

# Critical Path

The primary revenue-generating critical path is:
Auth
→ Provider Setup
→ Admin Review Tool (Minimal)
→ Provider Vetting
→ Provider Activation
→ Discovery
→ Booking Engine
→ Payment Processing
→ Commission & Settlement

This path determines the minimum viable marketplace launch.

---

# Contract Boundaries (Critical Path Optimization)

To shorten the critical path, publish these contracts early:

### Booking Contract
* Create booking
* Cancel booking
* Booking states

### Payment Contract
* Charge payment
* Refund payment
* Payment status

### Commission Contract
* Commission calculation rules
* Settlement interface

### Notification Contract
* Booking confirmation events
* Cancellation events
* Payment events

### Provider Activation Contract
* DRAFT
* PENDING_REVIEW
* APPROVED
* ACTIVE
* REJECTED

### Admin Review Contract
* Query pending providers
* Set provider approval status

These contracts allow parallel implementation across teams before full backend completion.

---

# Starting Points (No Incoming Dependencies)
* WI-01 User Authentication & Accounts

---

# Ending Points (No Outgoing Dependencies)
* WI-10 Notifications
* WI-11 Provider Dashboard
* WI-12 Ratings, Reviews & Moderation
* WI-14 Admin Dashboard (Full)

---

# Key Optimization Decisions

### Separating Calendar and Vetting
Availability Management was intentionally separated from Provider Vetting. Providers may configure schedules in DRAFT mode before approval. Only Provider Activation requires both Approved Vetting Status and Configured Availability.

### Node Splitting for Admin Dashboard
We resolved a circular dependency cycle (Provider Vetting -> Admin Dashboard -> Provider Data -> Provider Vetting) by splitting the Admin Dashboard. We created a minimal `Admin Review Tool (Minimal) (WI-13)` which unblocks provider vetting and activation, and moved the `Admin Dashboard (Full) (WI-14)` off the critical path as a non-blocking parallel endpoint.
