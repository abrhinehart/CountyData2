# Commission Elections Module Sketch

## Purpose

Set up a module for local commission election tracking so political turnover risk can be understood alongside entitlement and permit activity.

## Core idea

This module should answer: who holds each seat, who is running, when elections happen, and how likely upcoming political changes are to alter the land-use environment?

## Candidate entities

- `election_cycles`
- `commission_seats`
- `candidates`
- `endorsements`
- `race_outcomes`

## Likely integrations

- `cr_commissioners` and vote records from the Commission module
- `jurisdictions` for geography and body ownership
- `cr_entitlement_actions` for linking political posture to project outcomes
- external campaign-finance or ballot data if the module deepens later

## First useful slice

1. Seed seats and incumbents for one pilot body.
2. Add the next election date, filing window, and known candidates.
3. Link incumbents to commission voting history where available.
4. Surface upcoming races and seat-turnover risk.

## Open design questions

- Is the primary use case forecasting land-use posture, or just operational awareness?
- How should multi-member at-large bodies be represented versus district seats?
- Do we want campaign-finance ingestion in the first phase, or is election-calendar tracking enough?
