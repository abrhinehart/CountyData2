# Notice of Commencement Module Sketch

## Purpose

Establish a module for notices of commencement so the team can see early construction starts, contractor relationships, and expiring work authorizations in one place.

## Core idea

This module should answer: which notices were recorded, what work do they authorize, who is involved, when do they expire, and how do they connect to active permits or projects?

## Candidate entities

- `notice_of_commencement_records`
- `notice_document_pages`
- `notice_parties`
- `notice_permit_links`
- `notice_expiration_events`

## Likely integrations

- `transactions` for ownership context
- `pt_permits` for permit matching and work classification
- `subdivisions` for subdivision rollups
- county clerk ingestion patterns from the Sales side of the codebase

## First useful slice

1. Ingest a notice record manually or from a clerk export.
2. Parse or store core fields: owner, contractor, legal description, recording date, expiration date.
3. Match it to a permit or subdivision when possible.
4. Surface expiring or unmatched notices.

## Open design questions

- Should this module live closer to Sales ingestion or Permit Tracker ingestion?
- How much OCR/document parsing is needed before the module is useful?
- Are notices mainly a construction-start signal, or also a workflow tool for closings and ops?
