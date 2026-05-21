# Raw Feature Notes — Notifications Centre
# Used by: living-doc-create-feature file-based eval
#
# These are rough notes from a discovery session. The agent must convert
# them into a canonical Feature entity JSON.

## What is it?
A screen inside the mobile banking app where customers can see all their
recent alerts (balance updates, payment confirmations, security notices).
The screen is called the "Notifications Centre".

## Who owns it?
team-notifications (primary owner)
team-security also contributes for security alert types

## What does it depend on?
- notification-service (backend API that stores and delivers alerts)
- customer-profile-service (to fetch customer preferences for notification types)

## Surface type
UI — it's a screen in the mobile app

## Status
In development — expected to go live in Q3

## Linked user stories
Not known yet — to be linked during sprint planning

## Atomic behaviors (functionalities)
- Mark a notification as read
- Filter notifications by type (payments, security, promotions)
- Delete a notification
(These are candidates — not formally defined yet)
