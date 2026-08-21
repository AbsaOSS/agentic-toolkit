# Payment Flow — Living Documentation
# Feature: FEAT-002
# User Story: US-021 — Make a payment
# Used by: living-doc-update file-based eval

## Purpose
Enables a customer to make a payment from their current account to a
beneficiary. Covers intra-bank (same bank) and inter-bank (external)
payments.

## Acceptance Criteria

- **AC-1** — The customer must be authenticated (biometric or PIN) before
  initiating a payment.
  *Linked scenario*: `checkout.feature:23 — Scenario: Authenticated customer initiates payment`

- **AC-2** — Payment must complete within 3 seconds under normal load
  (p99 SLA).
  *Linked scenario*: `checkout.feature:41 — Scenario: Payment completes within SLA`

- **AC-3** — If the payment amount exceeds R 50 000, a second-factor
  approval step is required.
  *Linked scenario*: `checkout.feature:58 — Scenario: High-value payment requires second-factor approval`

- **AC-4** — The customer receives an in-app notification within 5 seconds
  of a successful payment.
  *Linked scenario*: `notifications.feature:12 — Scenario: Customer receives payment confirmation notification`

## Out of Scope
- Scheduled/recurring payments (covered by FEAT-scheduled-payments)
- Payments to international beneficiaries (not yet implemented)

## Owner
team-payments
