# Commission Radar — Schema Summary

**Database**: SQLite, `commission_radar.db`  
**ORM**: SQLAlchemy + Alembic (5 revisions)  
**LLM**: Claude (Anthropic API) for extraction

## Tables

### jurisdictions
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| slug | String(100) | UNIQUE, nullable |
| name | String(255) | UNIQUE, NOT NULL |
| state | String(2) | NOT NULL |
| county | String(100) | NOT NULL |
| municipality | String(100) | nullable |
| commission_type | String(50) | NOT NULL — city_commission/bcc/planning_board/planning_commission/boa/lpa |
| agenda_source_url | String(500) | nullable |
| agenda_platform | String(100) | nullable — civicplus/civicclerk/legistar/manual |
| has_duplicate_page_bug | Boolean | default False |
| pinned | Boolean | default False |
| config_json | Text | nullable — keywords, extraction_notes, detection_patterns |
| created_at | DateTime(tz) | default utc_now |
| updated_at | DateTime(tz) | default utc_now, onupdate |

~60 jurisdictions across Florida. Configured via YAML files per jurisdiction.

### source_documents
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| jurisdiction_id | Integer | FK -> jurisdictions.id, NOT NULL |
| filename | String(255) | NOT NULL |
| file_hash | String(64) | nullable (SHA-256) |
| source_url | String(1000) | nullable |
| external_document_id | String(255) | nullable |
| file_format | String(10) | nullable — pdf/html/docx |
| document_type | String(50) | NOT NULL — agenda/minutes |
| meeting_date | Date | nullable |
| page_count | Integer | nullable |
| extracted_text_length | Integer | nullable |
| keyword_filter_passed | Boolean | nullable |
| extraction_attempted | Boolean | default False |
| extraction_successful | Boolean | nullable |
| items_extracted | Integer | nullable |
| items_after_filtering | Integer | nullable |
| processing_status | String(50) | NOT NULL, default 'detected' |
| failure_stage | String(50) | nullable |
| failure_reason | Text | nullable |
| processing_notes | Text | nullable |
| created_at | DateTime(tz) | default utc_now |
| updated_at | DateTime(tz) | default utc_now, onupdate |

### projects (development projects — analogous to subdivisions)
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| jurisdiction_id | Integer | FK -> jurisdictions.id, NOT NULL |
| name | String(255) | NOT NULL |
| entitlement_status | String(50) | default 'not_started' |
| location_description | Text | nullable |
| acreage | Float | nullable |
| lot_count | Integer | nullable |
| proposed_land_use | String(100) | nullable |
| proposed_zoning | String(100) | nullable |
| lifecycle_stage | String(50) | nullable — planning_board/first_reading/second_reading/subdivision/complete |
| last_action_date | Date | nullable |
| next_expected_action | String(100) | nullable |
| notes | Text | nullable |
| created_at | DateTime(tz) | default utc_now |
| updated_at | DateTime(tz) | default utc_now, onupdate |

### project_aliases
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| project_id | Integer | FK -> projects.id CASCADE, NOT NULL |
| alias | String(255) | NOT NULL |
| source | String(20) | NOT NULL, default 'extracted' — extracted/manual/inferred |
| created_at | DateTime(tz) | default utc_now |

**Unique**: (project_id, alias)

### phases
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| project_id | Integer | FK -> projects.id, NOT NULL |
| jurisdiction_id | Integer | FK -> jurisdictions.id, NOT NULL |
| name | String(255) | NOT NULL |
| entitlement_status | String(50) | default 'not_started' |
| acreage | Float | nullable |
| lot_count | Integer | nullable |
| proposed_land_use | String(100) | nullable |
| proposed_zoning | String(100) | nullable |
| created_at | DateTime(tz) | default utc_now |
| updated_at | DateTime(tz) | default utc_now, onupdate |

### entitlement_actions (central fact table)
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| source_document_id | Integer | FK -> source_documents.id, nullable |
| project_id | Integer | FK -> projects.id, nullable |
| phase_id | Integer | FK -> phases.id, nullable |
| linked_action_id | Integer | FK -> entitlement_actions.id (self-ref), nullable |
| case_number | String(100) | nullable |
| ordinance_number | String(100) | nullable |
| parcel_ids | Text | nullable (JSON array) |
| address | String(500) | nullable |
| approval_type | String(50) | NOT NULL — annexation/land_use/zoning/development_review/subdivision/developer_agreement/conditional_use/text_amendment |
| outcome | String(50) | nullable — recommended_approval/recommended_denial/approved/denied/tabled/deferred/withdrawn/modified/remanded |
| vote_detail | String(100) | nullable |
| conditions | Text | nullable |
| reading_number | String(20) | nullable — first/second_final |
| scheduled_first_reading_date | Date | nullable |
| scheduled_final_reading_date | Date | nullable |
| action_summary | Text | nullable |
| applicant_name | String(255) | nullable |
| current_land_use | String(100) | nullable |
| proposed_land_use | String(100) | nullable |
| current_zoning | String(100) | nullable |
| proposed_zoning | String(100) | nullable |
| acreage | Float | nullable |
| lot_count | Integer | nullable |
| project_name | String(255) | nullable |
| phase_name | String(100) | nullable |
| land_use_scale | String(20) | nullable — small_scale/large_scale |
| action_requested | String(100) | nullable |
| meeting_date | Date | nullable |
| agenda_section | String(255) | nullable |
| multi_project_flag | Boolean | default False |
| backup_doc_filename | String(255) | nullable |
| needs_review | Boolean | default False |
| review_notes | Text | nullable |
| created_at | DateTime(tz) | default utc_now |
| updated_at | DateTime(tz) | default utc_now, onupdate |

### commissioners
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| jurisdiction_id | Integer | FK -> jurisdictions.id, NOT NULL |
| name | String(255) | NOT NULL |
| title | String(100) | nullable |
| active | Boolean | default True |
| created_at | DateTime(tz) | default utc_now |
| updated_at | DateTime(tz) | default utc_now, onupdate |

**Unique**: (jurisdiction_id, name)

### commissioner_votes
| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| entitlement_action_id | Integer | FK -> entitlement_actions.id CASCADE, NOT NULL |
| commissioner_id | Integer | FK -> commissioners.id CASCADE, NOT NULL |
| vote | String(20) | NOT NULL — yea/nay/abstain/absent |
| made_motion | Boolean | default False |
| seconded_motion | Boolean | default False |
| created_at | DateTime(tz) | default utc_now |

## Extraction Pipeline
Scrape → Intake/Dedup → Collection Review → Convert (PDF/HTML/DOCX) → Auto-Detect → Keyword Filter → LLM Extract (Claude) → Threshold Filter → Normalize → Insert Records → Agenda-Minutes Match → Lifecycle Inference → Acreage Enrichment
