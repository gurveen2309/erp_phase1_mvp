# ERP Phase 1 Implementation Workflow

## Purpose of this document

This document records what was implemented in the Phase 1 ERP MVP, why specific technical decisions were taken, how the import flow works, and what operational workflow is expected going forward.

It is intended as a working reference for future development, debugging, onboarding, and requirements review.

## Business objective

The target was to build a laptop-first, owner-operated ERP foundation that can replace spreadsheet-led operations without over-engineering the first release.

The immediate business needs were:

- maintain party masters
- enter and review challans / production rows
- maintain invoices, payments, and opening balances
- compute party ledgers and outstanding balances
- import recurring Excel data instead of relying on one-time scripts
- run locally with Docker and PostgreSQL

The implementation intentionally focused on an operational core, not a full ERP.

## Scope implemented

The project was implemented as a Django monolith with these modules:

- `masters`
- `production`
- `finance`
- `reporting`
- `migration_app`

The delivered Phase 1 scope includes:

- party master management
- challan / production record storage
- invoice storage
- payment storage
- opening balances
- computed party ledger
- outstanding summary
- production summary
- recurring Excel import framework
- workbook-specific importer for the production dashboard format
- Docker + PostgreSQL local deployment

The following items were intentionally deferred:

- automated tests
- inventory
- GST workflows
- multi-user roles and permissions
- settlement allocation logic between invoices and payments
- audit trail framework
- cloud deployment hardening

## Core architectural decisions

### 1. Django monolith instead of microservices

Decision:
- use a single Django codebase with separate apps for domain boundaries

Why:
- the system is single-business and single-operator in Phase 1
- the cost of service separation would exceed the actual business value at this stage
- Django admin provides immediate CRUD capability for the owner
- reporting and imports can be built faster in one codebase with shared models and transactions

Tradeoff:
- the codebase stays simple and fast to iterate on
- if later complexity grows, internal service boundaries already exist through app separation and query/service functions

### 2. PostgreSQL as system of record

Decision:
- use PostgreSQL for persistent operations, with Docker Compose as the standard runtime

Why:
- data integrity constraints matter for finance records
- the import workflow benefits from transactional behavior
- PostgreSQL gives better long-term stability than relying on local spreadsheet state
- the user explicitly wanted Docker and PostgreSQL only

Tradeoff:
- local setup is slightly heavier than SQLite
- the resulting environment is much closer to a durable business system

### 3. Admin-first UI with a few custom read-heavy views

Decision:
- rely on Django admin for create/edit flows
- build custom views only where read/reporting flow matters

Why:
- manual entry speed was more important than frontend polish in Phase 1
- admin gives reliable CRUD screens quickly
- reporting pages need a clearer operator workflow than raw admin tables

Implemented custom views:

- party ledger
- outstanding summary
- production dashboard
- import preview / confirmation
- import history

### 4. Running balance is computed, not stored

Decision:
- do not persist editable running balances

Why:
- storing running totals creates reconciliation drift
- balances should always be derivable from business events
- ledger correctness is easier to reason about when the source of truth is event-based

Implemented rule:

- opening balances affect ledger
- invoices are debits
- payments are credits
- challans do not affect finance balances in Phase 1

## Domain model decisions

### Party

`Party` stores the business identity used across finance and production.

Why:
- party identity is the anchor for every workflow
- imports and reports both depend on stable party names

Additional implementation choice:
- imported records track `source_batch` and `source_row_number` for traceability

### Challan

`Challan` is used as the persisted production record in Phase 1.

Why:
- the source workbook’s `Daily Production Matrix` is operational data
- this data belongs in the production module, even though it is not yet linked to billing rules

Important decision:
- `Daily Production Matrix` rows were imported into `Challan` records, even though the source workbook is not literally named as challans
- this keeps production reporting inside the ERP model instead of leaving it as an isolated spreadsheet view

### OpeningBalance, Invoice, Payment

These models represent the canonical financial event layer.

Why:
- the ledger report in the workbook is operationally a sequence of finance events
- the ERP should persist those normalized finance events, not just store the workbook as text

## Import framework decisions

### 1. Imports are repeatable operational workflows, not one-time scripts

Decision:
- build a recurring import module inside the app

Why:
- the business is still spreadsheet-driven and will continue receiving Excel updates
- one-off conversion scripts are fragile and hard to repeat safely
- preview / confirm / history is operationally safer than direct inserts

Implemented import flow:

1. upload file
2. parse and normalize rows
3. generate preview
4. show validation issues and duplicate warnings
5. confirm import
6. persist as a `MigrationBatch`
7. keep row-level errors in `MigrationRowError`

### 2. Workbook-specific importer instead of forcing generic flat-file mapping

Decision:
- create a dedicated import type for the production dashboard workbook format

Why:
- `production_dashboard (4).xlsx` is a multi-sheet business workbook, not a flat import template
- the generic import flow expects one import type per upload
- the workbook actually contains multiple domains:
  - finance events in `Ledger Report`
  - production records in `Daily Production Matrix`

Implemented import type:

- `production_dashboard_workbook`

This importer expands one workbook into multiple normalized record types:

- `Party`
- `OpeningBalance`
- `Invoice`
- `Payment`
- `Challan`

### 3. Composite import batch

Decision:
- import the workbook as one composite batch, not as multiple manual upload steps

Why:
- a fresh database would otherwise fail because finance rows depend on parties being loaded first
- a multi-step operator workflow would be error-prone
- a single batch keeps provenance consistent

Implemented behavior:

- parties are derived and upserted first
- finance rows are parsed from `Ledger Report`
- production rows are parsed from `Daily Production Matrix`
- all of them are committed under one `MigrationBatch`

## Workbook parsing rules

## Source workbook used

- `production_dashboard (4).xlsx`

Relevant sheets:

- `Ledger Report`
- `Daily Production Matrix`

Ignored sheets:

- `Analysis Dashboard`
- `Pivot Table 4`

Reason:
- those are derived / reporting views, not source-of-truth business events

### Ledger Report parsing

The ledger sheet is treated as a finance event source.

Rules implemented:

- `OPENING BALANCE` rows become `OpeningBalance`
- rows with debit amount become `Invoice`
- rows with credit amount become `Payment`
- original `Particulars` text is preserved in `remarks`

Examples:

- `TO BILL NO. ...` -> invoice
- `BILL NO. ...` -> invoice
- `BY NEFT` / `BY TRF` / `BY RTGS` -> payment
- `CREDIT` / `BY R/D` -> payment with adjustment mode

Important constraint decision:
- classification is based on debit / credit side, not only on text prefixes

Why:
- source particulars are inconsistent in later rows
- debit / credit columns are a more reliable source of financial direction than textual wording

### Daily Production Matrix parsing

The production sheet is treated as operational production input and imported into `Challan`.

Field mapping used:

- `Date` -> `challan_date`
- `Party Name` -> party alias mapping -> canonical `Party`
- `Kg(s)` -> `weight_kg`
- `Material` -> `job_description`
- `Production Output (₹)` -> `amount`

Additional columns such as shift, rate, workers, working hours, and remarks are currently folded into `remarks`.

Why:
- those fields are useful operational context
- the current schema does not yet justify a dedicated production-cost model
- preserving them in remarks keeps the source detail without expanding scope prematurely

## Party name normalization decisions

The workbook uses two different naming styles:

- long canonical names in `Ledger Report`
- short aliases in `Daily Production Matrix`

Decision:
- create a workbook-specific alias map

Examples:

- `Fitwell` -> `FITWELL FASTNERS & FITTING INDUSTRIES`
- `Precision` -> `PRECISION AUTO FASTNERS`
- `Premco` -> `PREMCO INDIA EXIM PVT. LTD.`
- `KV` -> `K.V.ENTERPRISES`

Why:
- finance and production must land on the same `Party` record
- relying on literal string matching would split the same business entity across multiple rows

Additional decision:
- production-only names not present in the ledger are still created as parties if present in the workbook

Why:
- the ERP should not discard operational parties just because finance rows do not yet exist for them

## Constraint and deduplication decisions

### 1. Keep database uniqueness constraints

Decision:
- preserve unique constraints on:
  - party + invoice number
  - party + payment reference
  - party + challan number

Why:
- those constraints are valuable and should not be weakened to accommodate dirty imports
- importer logic should adapt to source inconsistencies instead of diluting data integrity

### 2. Handle dirty workbook identifiers in importer logic

The source workbook reuses some identifiers that are not globally unique for a party.

Examples found during implementation:

- repeated invoice number for the same party on different dates
- generic payment references such as `TRF`

Decision:
- keep original source text in `remarks`
- only store meaningful payment references when they contain real identifying content
- if a source invoice number or payment reference is repeated for the same party, append the date suffix in the stored identifier for uniqueness

Why:
- this preserves the source audit trail
- the import succeeds without disabling constraints
- the normalized DB record remains unique and queryable

### 3. Duplicate detection behavior

Decision:
- preview duplicate warnings compare against the existing database
- composite workbook preview avoids requiring the related `Party` to already exist before finance rows are previewed

Why:
- the workbook import must work in an empty database
- duplicate detection should still warn if the same workbook is re-imported later

## Operational workflow implemented

### Standard local runtime

The project is intended to run through Docker Compose with:

- `web`
- `postgres`

Why:
- the database and app should start as a repeatable local stack
- the user wanted PostgreSQL and Docker only

### DBeaver support

Decision:
- expose PostgreSQL on a host port

Why:
- local DB inspection is useful during import verification and future debugging

Result:
- DBeaver can connect to the Dockerized database through `localhost`

### Import operator workflow

Recommended workflow for future workbook imports:

1. open `/imports/`
2. choose `Production Dashboard Workbook`
3. upload the latest workbook
4. review preview summary
5. inspect record breakdown and warnings
6. confirm import
7. review `/imports/history/`

## What was actually imported

The workbook importer was not only implemented, it was also used successfully against the running PostgreSQL database.

Imported totals after the successful batch:

- `21` parties
- `7` opening balances
- `367` invoices
- `88` payments
- `86` challans
- `1` persisted migration batch

The successful workbook preview produced:

- `569` valid rows
- `0` validation errors

## Validation approach taken during implementation

The implementation was validated incrementally instead of assuming the original plan would fit the workbook as-is.

Practical validation steps used:

- inspect workbook sheet structure
- inspect actual row patterns in `Ledger Report`
- identify alias mismatch between finance and production sheets
- dry-run preview against the workbook
- commit against real PostgreSQL constraints
- fix real collisions surfaced by the database
- re-run import until the batch completed cleanly
- verify post-import counts and sample ledger output

Why this mattered:

- the workbook contained real-world inconsistencies that were not visible from the initial plan alone
- the database constraints surfaced the exact normalization rules that the importer needed

## Known limitations and next logical improvements

### Current limitations

- no automated tests yet
- production rows are stored in `Challan` with extra source fields packed into `remarks`
- challans are not linked to invoices
- no invoice-payment settlement allocation
- no explicit cost analytics model from the production sheet
- workbook importer is specific to the known production dashboard format

### Recommended next improvements

1. add automated tests for workbook import parsing and idempotency
2. add a richer production model if labor / energy / utilization need first-class reporting
3. add invoice-payment allocation once reconciliation becomes necessary
4. add export and admin actions for import diagnostics
5. add a management command wrapper for scheduled or semi-automated imports

## Summary of why the implementation looks the way it does

The codebase was shaped by a practical rule:

- normalize finance data enough to make the ERP reliable
- preserve source context enough to make the import explainable
- do not enlarge scope where remarks and structured preview are sufficient

This is why the current implementation uses:

- a modular Django monolith
- PostgreSQL with Docker
- admin-first CRUD
- computed ledgers instead of stored balances
- a recurring import module instead of one-off scripts
- a workbook-specific importer instead of pretending the source is a generic flat file
- importer-side normalization rather than weakening database constraints

That combination was the smallest implementation that could safely absorb the real workbook structure and turn it into usable ERP data.
