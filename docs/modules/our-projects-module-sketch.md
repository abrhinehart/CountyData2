# Our Projects Module Sketch

## Purpose

Create a home for the projects the team is actively pursuing or shepherding so they do not disappear across spreadsheets, emails, and memory.

## Core idea

This module should answer: what are we working on, where is each project in its lifecycle, what is blocked, and what external signals from CountyData2 matter right now?

## Candidate entities

- `projects`
- `project_stage_history`
- `project_assignments`
- `project_notes`
- `project_links`

## Likely integrations

- `subdivisions` for canonical geography
- `transactions` for land acquisition and close history
- `pt_permits` for vertical progress after acquisition
- `cr_entitlement_actions` for pre-development activity

## First useful slice

1. Create a project record manually.
2. Attach a subdivision or county.
3. Show current owner, stage, next action, and blocker.
4. Render a project detail timeline with linked CountyData2 signals.

## Open design questions

- Is a project always tied to a subdivision, or can it begin as a looser market lead?
- Should this module include valuation and deal assumptions, or stay operational?
- Do we want one project per subdivision, per phase, or per internal opportunity?
