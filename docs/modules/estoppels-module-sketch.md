# Estoppels Module Sketch

## Purpose

Provide a clear operating surface for estoppel requests, responses, fees, and closing blockers tied to communities, associations, and transactions.

## Core idea

This module should answer: which estoppels are outstanding, what money or violations are attached, when do they expire, and what is still blocking close?

## Candidate entities

- `estoppel_requests`
- `association_contacts`
- `estoppel_documents`
- `estoppel_findings`
- `transaction_estoppel_links`

## Likely integrations

- `transactions` for deal-level tracking
- `subdivisions` for community context
- `builders` or counterparties if requests should roll up by operator
- document storage patterns already used in Commission Radar

## First useful slice

1. Create an estoppel request manually.
2. Attach it to a transaction, subdivision, or HOA.
3. Track status, due date, response date, and key findings.
4. Flag closing blockers and expiring responses.

## Open design questions

- Do we need one estoppel per association, or bundled packages per transaction?
- Should the first iteration focus on workflow only, or document extraction too?
- Where should HOA/association master data live if it becomes reusable across modules?
