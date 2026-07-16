# Vertical Slice Definitions: SkillSwap (Updated for Investor Demo)

This document contains our revised vertical slice plan adjusted for the lead investor demo next Friday, alongside the formal communication message to the Product Manager.

---

## Part 1: PM Communication & Justification

### Message to the PM

> **Subject**: RE: Payment Demo for Investor next Friday - Scope Tradeoff Proposal
>
> "Hi [PM Name],
>
> I understand that the lead investor wants to see 'money flow' during next Friday's demo. However, as noted in our Module 3 risk assessment, a real Stripe integration is currently blocked because the client does not yet have a registered business entity or merchant account. 
> 
> To give the investor a realistic demonstration of the booking and revenue split without missing the Friday deadline, I recommend we **implement the Mock Payment Stub in Slice 1**. This will show the customer booking, entering card details, receiving confirmation, and the database recording the 15% platform split—meeting the investor's core expectation.
>
> **Tradeoff / Adjustments:**
> - To absorb this mock payment scope and keep Slice 1 at a **Small (S)** complexity (under 3 hours of build), we are **cutting the Provider Detail Page and multi-slot calendar selection** from Slice 1. Customers will book a pre-selected slot directly from the provider cards on the home page.
> - In parallel, if capacity allows, we will run a isolated Stripe Connect sandbox spike (Slice 1.5) on a temporary developer account to prove technical connectivity. This remains completely decoupled from the booking flow to protect the demo timeline.
>
> Let me know if you approve this scope tradeoff so we can begin execution immediately."

### Tradeoff Assessment
- **What is Added**: Simple mock card form page, mock charge API handler (`POST /payments/mock-charge`), and transaction ledger writing (85% provider, 15% platform fee split).
- **What is Cut**: Separate Provider Details page, category routing, and active calendar slot selection. Customers book a pre-selected slot directly from the list card.
- **Why**: Keeps development complexity low so the demo is 100% buildable and testable by next Friday, while proving the platform's revenue model.

---

## Part 2: Revised Vertical Slices

### Slice 1: Browse and Mock Pay (Seeded Data)
*Thinnest end-to-end thread showing browsing, booking, and platform fee splits.*

- **Scope (What Is In)**:
  - Database: Seed data for 3 providers (name, rating, pre-selected slot, fee). Table `bookings` (persists booking details) and `transactions` (persists gross fee, 85% provider payout, 15% platform fee split).
  - API: `POST /bookings` endpoint that locks a pre-selected slot and calls `POST /payments/mock-charge` stub.
  - UI: Home page listing 3 provider cards (each displaying a single pre-selected slot and booking button). Clicking "Book" redirects to a Mock Checkout page. Entering dummy card data and clicking "Pay" displays an on-screen confirmation screen with booking reference and payment confirmation details.
- **Anti-Scope (What Is Explicitly Out)**:
  - No separate Provider Detail Page (booking starts from list cards).
  - No dynamic calendar slot selection.
  - No user accounts or authentication (anonymous checkout).
  - No real Stripe API calls. No email confirmations.
  - No search, filter, cancellation, or refund logic.
- **Dependencies**: None.
- **Acceptance Criteria**:
  1. Load home page: See 3 provider cards (displaying slot, price).
  2. Click "Book" on card: User is taken to Mock Checkout page showing the provider name and amount.
  3. Enter dummy credentials and click "Confirm Payment".
  4. See confirmation screen with booking ID and payment confirmation message.
  5. Check database: Verify a booking record and transaction ledger records (15% platform split) are successfully saved.
- **Estimated Complexity**: S (3 hours)

---

## Slice 1.5: Stripe Connect Sandbox Spike (Optional / Isolated)
*Standalone spike to validate Stripe API credentials and sandbox checkout.*

- **Scope (What Is In)**:
  - An isolated test script/HTML page showing a simple button linking to Stripe Checkout (sandbox mode) using temporary test keys. Validates webhook receipt on success.
- **Anti-Scope (What Is Explicitly Out)**:
  - Not connected to the booking engine, user database, or dashboard.
- **Dependencies**: None (run in parallel by a separate engineer).
- **Acceptance Criteria**:
  1. Load the spike page: Click "Test Stripe Checkout".
  2. Complete Stripe test page checkout.
  3. Verify Stripe webhooks are received and log a successful charge message on our backend.
- **Estimated Complexity**: S (2 hours)

---

## Slice 2: User Authentication & Accounts (Secure Bookings)
*Introduces secure accounts and links bookings directly to registered customers.*

- **Scope (What Is In)**:
  - User accounts signup, login, and sessions (JWT/cookie). Update bookings and transactions to associate with `user_id`. Customer dashboard listing past bookings.
- **Anti-Scope (What Is Explicitly Out)**:
  - No provider onboarding interfaces. No third-party OAuth.
- **Dependencies**: Slice 1.
- **Estimated Complexity**: M (1 day)

---

## Slice 3: Provider Self-Service & Vetting (Active Supply Side)
*Enables providers to create profiles, submit background checks, and manage availability slots.*

- **Scope (What Is In)**:
  - Provider registration onboarding. Document upload. Admin review queue tool for vet checks (Pending -> Approved). Provider portal for calendar slot generation. Update home page to render ONLY approved provider cards with active slots.
- **Dependencies**: Slice 1, Slice 2.
- **Estimated Complexity**: M (1.5 days)

---

## Slice 4: Booking Engine & Concurrency Control (Preventing Double Booking)
*Implements locking mechanisms to protect availability slots from race conditions.*

- **Scope (What Is In)**:
  - Pessimistic transaction locks (`SELECT FOR UPDATE`) on slots during booking. UI error messaging for concurrent booking failures.
- **Dependencies**: Slice 1, Slice 2, Slice 3.
- **Estimated Complexity**: M (1 day)

---

## Slice 5: Full Refunds & Real Stripe Migration (Operational Payments)
*Migrates mock payments to Stripe Connect and integrates cancellations/refunds.*

- **Scope (What Is In)**:
  - Replace Mock Payment Stub with real Stripe Connect integration using verified client credentials. Implement cancellation policies (100% refund >24h; 50% otherwise) and trigger real payouts/refunds.
- **Dependencies**: Slice 1.5, Slice 2, Slice 3, Slice 4.
- **Estimated Complexity**: L (3 days)
