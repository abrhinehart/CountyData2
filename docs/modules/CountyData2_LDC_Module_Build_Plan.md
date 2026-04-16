# CountyData2 LDC Module — Build Plan

## Overview

Land Development Code module for CountyData2. Extracts residential zoning standards from municipal ordinances, integrates with Commission Radar for amendment tracking, and surfaces the product possibility model for internal sales workflows.

**Primary data source:** Municode API (with fallback to American Legal Publishing for non-Municode jurisdictions).

**Pilot jurisdiction:** Bay County, Florida.

---

## Phase 1: Infrastructure & API Layer

### 1.1 Municode API Tree Crawler
- **Goal:** Full mechanical tree walk of Municode document hierarchy for a single jurisdiction.
- **Approach:**
  - Walk every node in the tree, retrieve node metadata (ID, heading, HasChildren, IsUpdated, IsAmended, HasAmendedDescendant flags).
  - Retrieve actual content for each node (no skipping, no inference).
  - Store raw tree structure + content in a staging table for inspection.
- **Output:** Complete tree snapshot with node IDs, headings, and text content.
- **Constraint:** LLM does not interpret or classify nodes during this phase. Pure data retrieval only.
- **Success criteria:** 100 percent tree coverage, no missed branches, all content retrieved.

### 1.2 Change Detection Infrastructure
- **Goal:** Detect when Municode tree structure changes (new nodes, removed nodes, amended content).
- **Approach:**
  - Store tree snapshots per jurisdiction with timestamps.
  - On periodic re-crawl (a few times per year), diff current tree against stored version.
  - Flag nodes with IsUpdated, IsAmended, or HasAmendedDescendant flags set to true.
  - Log structural changes (new nodes, deleted nodes).
- **Output:** Change log per jurisdiction showing what's new, what's gone, what's amended.
- **Dependency:** Phase 1.1 complete.

### 1.3 Jurisdiction Registry
- **Goal:** Map each target Florida jurisdiction to its code hosting platform and root node ID.
- **Approach:**
  - Manual one-time mapping: for each jurisdiction, identify which platform hosts its code (Municode, American Legal, local site) and the root node ID for the residential zoning chapter.
  - Store in a `jurisdictions` table with fields: jurisdiction_name, platform, root_node_id, last_crawled, last_tree_hash.
- **Output:** Jurisdiction registry ready for crawler loop.
- **Pilot:** Bay County on Municode (root node TBD after initial exploration).

---

## Phase 2: Schema Definition & Onboarding

### 2.1 Zoning District Schema Design
- **Goal:** Define what fields get extracted for each zoning district.
- **Approach:**
  - During onboarding, manually review the jurisdiction's code and define the field set for that jurisdiction.
  - Schema is jurisdiction-specific (different codes define different standards).
  - Use flexible storage pattern: `district_attributes` table with (jurisdiction_id, district_id, field_name, field_value) to avoid breaking changes when schema evolves.
- **Output:** Schema definition document per jurisdiction (e.g., Bay County LDC schema v1).
- **Pilot:** Bay County R-1, R-2, R-3, R-4, R-5, R-5A districts.

### 2.2 Onboarding Checklist
- For a new jurisdiction:
  1. Identify platform + root node ID (1.3 registry).
  2. Run full tree crawl (1.1 crawler).
  3. Manually review code and define field set for residential zones.
  4. Approve LLM-proposed schema extraction (see Phase 3.1).
  5. Store schema definition in configuration.
- **Timeline:** One jurisdiction per session, ~1-2 hours per jurisdiction.

---

## Phase 3: LLM-Powered Extraction & Validation

### 3.1 Residential Zoning District Classification
- **Goal:** LLM reads actual tree content (not titles) and tags sections as "this is a residential zoning district section" with high confidence.
- **Approach:**
  - Two-pass classification:
    - **Pass 1 (Verification):** LLM reads actual content of candidate nodes and classifies each.
    - **Pass 2 (Human Review):** Review LLM classifications and approve or correct.
  - Constraint: LLM must justify classification by citing specific text from the content, not relying on node titles or docs.
- **Output:** Approved mapping of tree nodes → zoning districts.
- **Dependency:** Phase 1.1 complete, Phase 2.1 schema defined.

### 3.2 Structured Field Extraction
- **Goal:** Extract zoning standards (lot size, density, setbacks, permitted uses, etc.) from raw code text into structured fields.
- **Approach:**
  - LLM reads the code section for a district and extracts field values according to the jurisdiction's schema (defined in 2.1).
  - Output is staged with confidence scores.
  - Human review step: compare extracted values against source text, approve or correct.
  - Store approved values in `district_attributes` table.
- **Output:** One record per zoning district per jurisdiction, with all defined fields populated.
- **Constraint:** All source text must be cited — if extracted value can't be traced to actual code, it gets flagged for manual review.
- **Pilot success:** Bay County 6 residential districts, all fields extracted and validated.

### 3.3 New District Detection
- **Goal:** When an amendment creates a new zoning district, detect it and stage for onboarding.
- **Approach:**
  - LLM detects new district in amendment text.
  - Stages proposed schema for new district (based on similar existing districts in the jurisdiction).
  - Review and approve schema.
  - Extraction proceeds as per 3.2.
  - Eventually: full automation once extraction confidence is validated.
- **Output:** New district record created, all fields extracted.
- **Timeline:** Manual review phase for pilot; revisit after 3-5 new districts.

---

## Phase 4: Commission Radar Integration

### 4.1 Amendment Detection & Parsing
- **Goal:** When Commission Radar flags an LDC text amendment, automatically parse it to identify affected districts and field changes.
- **Approach:**
  - Commission Radar passes amendment text to LDC module.
  - LLM identifies which section(s) of the code are being changed.
  - Match sections to stored tree nodes and district records.
  - Extract proposed new field values from amendment text.
- **Output:** Staged amendment record with proposed changes.
- **Dependency:** Phase 3.1 (district classification) and Phase 4.2 (node-to-district mapping) complete.

### 4.2 Node-to-District Lookup
- **Goal:** Map Municode tree node IDs to stored zoning district records.
- **Approach:**
  - During Phase 3.1 classification, create lookup table: node_id → (jurisdiction_id, district_id).
  - Store in database for amendment matching.
- **Output:** Lookup table ready for amendment matching in 4.1.

### 4.3 Amendment Validation & Staging
- **Goal:** Stage proposed amendments for human review before applying to stored data.
- **Approach:**
  - Display diff: current field values vs. proposed new values.
  - Flag if amendment creates schema changes (new field type or new district).
  - Review and approve.
  - Eventually: auto-commit once parsing accuracy is proven.
- **Output:** Amendment staged and ready for approval or rejection.
- **Timeline:** Manual approval for all amendments during pilot; revisit after 10-20 amendments.

---

## Phase 5: Dashboard & Product Model Integration

### 5.1 Zoning District Lookup UI
- **Goal:** Make extracted standards accessible to internal teams for product planning.
- **Approach:**
  - Simple lookup: select jurisdiction → select district → view all extracted fields.
  - Export to CSV or API for downstream use.
- **Output:** Read-only UI for zoning data.
- **Timeline:** Post-pilot, once extraction is stable.

### 5.2 Product Possibility Model Feed
- **Goal:** Zoning standards inform what product types are feasible on a parcel.
- **Approach:**
  - Link this module to existing product models (density limits, unit type constraints, etc.).
  - TBD in coordination with sales/product workflow.
- **Output:** Integration spec (deferred pending product team input).

---

## Data Model & Storage

### Tables

**jurisdictions**
- jurisdiction_id (PK)
- jurisdiction_name
- state
- platform (Municode, AmericanLegal, etc.)
- root_node_id
- last_crawled (timestamp)
- last_tree_hash (for change detection)
- schema_version

**municode_tree**
- node_id (PK, from API)
- jurisdiction_id (FK)
- parent_node_id
- heading
- content (raw text)
- doc_order_id
- is_updated (from API)
- is_amended (from API)
- has_amended_descendant (from API)
- retrieved_at (timestamp)

**zoning_districts**
- district_id (PK)
- jurisdiction_id (FK)
- district_name (e.g., "R-1")
- node_id (FK to municode_tree, for linkage)
- schema_version
- created_at

**district_attributes**
- attribute_id (PK)
- district_id (FK)
- field_name (e.g., "min_lot_size", "max_density")
- field_value
- field_type (string, number, enum, etc.)
- source_text (citation to code section)
- confidence (high, medium, low)
- updated_at

**amendments** (for Commission Radar integration)
- amendment_id (PK)
- commission_action_id (FK to Commission Radar)
- jurisdiction_id (FK)
- amendment_text
- affected_node_ids (array or JSON)
- affected_districts (array or JSON)
- proposed_changes (JSON: {field_name → old_value, new_value, source_text})
- status (staged, approved, rejected, applied)
- reviewed_by (user)
- reviewed_at (timestamp)
- applied_at (timestamp)

**tree_change_log**
- change_id (PK)
- jurisdiction_id (FK)
- crawl_timestamp
- change_type (node_added, node_removed, node_amended)
- node_id
- details (JSON)

---

## Build Sequence

1. **Phase 1.1** — Municode tree crawler (standalone Python script, no UI yet).
2. **Phase 1.3** — Jurisdiction registry setup.
3. **Phase 2.1 + 2.2** — Bay County onboarding (manual schema definition).
4. **Phase 3.1 + 3.2** — Classification + extraction pipeline for Bay County (with human review steps).
5. **Phase 1.2** — Change detection infrastructure (non-blocking, can run in parallel).
6. **Phase 4.1 + 4.2 + 4.3** — Commission Radar integration (amendment pipeline).
7. **Phase 5.1** — Dashboard UI (post-pilot).

---

## Open Questions & Notes

- **American Legal Publishing fallback:** Design deferred pending pilot success with Municode. Will require HTML scraping instead of API.
- **Scale:** Plan assumes Municode covers most Florida jurisdictions. Verify platform coverage early.
- **Schema auto-creation (Phase 3.3):** Manual approval in pilot; revisit after validation.
- **Amendment auto-commit (Phase 4.3):** Manual approval in pilot; auto-commit after 10-20 amendments with 95+ percent accuracy.
- **Product model integration:** Coordinate with sales/product team once this module is stable.
