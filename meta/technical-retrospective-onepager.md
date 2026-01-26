# Technical Retrospective (One-Pager)

Project: Unified Reconciliation and Settlement (URS)
Role: Architect and Developer — design, POC, cross-functional alignment
Date: 2025–2026

## Problem & Goals
- Fragmented systems (stores vs e-commerce) created duplicated costs, slow onboarding of new tenders, and inconsistent reconciliation.
- Out-of-balance visibility gap: e-commerce (~30% sales) had ~$150M OOB vs stores ~$50M; .com lacked order/payment-level traceability.
- Goal: unify settlement and reconciliation into a single, event-driven platform that:
  - Reconciles at order/invoice level for all channels.
  - Onboards new processors via configuration (reduce months→days).
  - Provides end-to-end traceability, 7-year audit trails, and SOX compliance.

## Scope
- Build a Unified Reconciliation System (URS) that ingests events from CTH/OMS/UPP/BUA/FDF/PLUTUS and reconciles per order/payment.
- Extend from store-only to .com where upstreams provide partial keys.
- Stabilize projections and reduce ops cost/complexity.

## Architecture (HLD)
- State machine v2: single actor per order; invoice-level state within the order actor.
- Persistence: Akka Persistence R2DBC (PostgreSQL) with data partitioning; projections via Akka Projection to SQL.
- Messaging/Keys: primary OrderId with invoice-level details; handles partial key scenarios.
- Scale/Placement: external shard allocation aligned with Kafka partitions.
- Future: AKKA → PEKKO after feature parity.

## Key Decisions & Trade-offs
- Per-order actor vs per-invoice actors
  - Chosen for simpler routing, fewer entities, holistic order view; endorsed by Lightbend.
- R2DBC/Postgres vs Cassandra
  - Lower ops burden and cost; partitioned tables preserve scale-out; clear failover runbooks.
- Deterministic keying under ambiguity
  - Order-level primary key masks upstream key variability while preserving invoice detail.

## Performance & Reliability
- POC Infra: RDS Postgres db.m5d.2xlarge; EKS 5× m5.xlarge.
- Load: 1,000,000 requests across 2,000 entities.
- Results: ~20,283 req/s; avg 484 ms; fastest 2.67 ms; slowest 2.85 s.
- Reliability: partitioned journals/snapshots across DBs; projection stability improved; failover guidance (auto-restarts, multi-AZ, replay/recovery).

## Cross-Functional & Execution
- Partners: Treasury, Accounting, Payments, plus upstream teams (CTH/OMS/UPP/BUA/FDF/PLUTUS).
- External review: Lightbend approved design; MoM captured owners (projection fixes vs SM v2 features).
- Artifacts: C4, state diagrams, communication design; repository and design docs.

## Domain Boundaries & Integration Challenges
- Event contracts and versioning
  - Agreed with .com teams on minimal required keys per event (OrderId as primary; InvoiceId/PaymentHandle optional with evolution path), schema version headers, and backward-compatible fields.
- System responsibilities (who does what)
  - Upstreams (CTH/OMS/UPP/BUA/FDF/PLUTUS) own source-of-truth events; URS owns reconciliation state, projections, and exception workflows; settlement system owns batch submission and funding status.
- Data flow and idempotency
  - Kafka topics per domain; idempotent consumers with dedupe keys; external shard allocation aligns partitions with actors to minimize cross-node chatter.
- SLAs and failure handling
  - Defined ingestion/replay SLAs, projection lag thresholds, and backfill procedures; runbooks for dead-letter, retries, and schema rollbacks.
- Rollout and governance
  - Dual-run window with shadow reconciliation; feature flags per upstream; change reviews via MoM with RACI; monitoring dashboards shared across teams.

## Risks & Mitigations
- Single-node DB failure → auto-restarts, multi-AZ failover, recovery runbooks.
- Schema/key evolution across upstreams → schema evolution support; order-level keying.
- Migration risk from legacy events → one-time migration plan; dual-run window during ramp.

## What Could Have Been Better
- Earlier E2E functional testing across domains
  - Formalize cross-domain E2E scenarios (store & .com) as part of definition of ready; fail fast on contract gaps.
- Common, always-on pre-prod environment
  - A single stable, data-seeded environment shared by CTH/OMS/UPP/BUA/FDF/PLUTUS/URS to validate flows end-to-end continuously.
- BDD and domain-owned test coverage
  - Encourage each domain to maintain BDD specs and near-100% coverage of domain behaviors; publish shared test catalogs for reuse.
- Earlier discovery of domain edge cases
  - Example: PLUTUS behavior when invoice is generated without successful auth → no captured events emitted. Add domain-specific contract tests to surface such behaviors upfront.

## Business Impact
- Unified view of settlement/reconciliation across channels; out-of-balance visibility at order/payment level.
- Faster onboarding of payment processors (config-driven) and improved auditability.
- Reduced ops cost/complexity vs Cassandra; clearer SLOs and observability.

## Next Steps
- Tighten success metrics (recon accuracy, time-to-reconcile) across store vs .com.
- Automate projection backfills; expand DR/region drills.
- Complete AKKA→PEKKO migration and re-benchmark.

## Artifacts (internal)
- PDFs/MDs: exports/pdf/*UR-*.pdf, exports/parsed/*UR-*.md
  - UR State machine Design; Flat Design; Communication Design; C4 diagram; Current Plan; Redesign.
- POC repository: https://github.com/krushnaDash/spring-akka
- MoM: decisions and owners in UR State machine Design doc.
