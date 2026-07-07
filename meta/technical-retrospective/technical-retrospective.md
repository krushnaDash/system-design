# Technical Retrospective

You’ll be asked to speak about a project you were heavily involved in from a technical perspective, focusing on breadth and depth. This assesses your comfort engaging with technical details and the scope at which you’ve operated. This is a conversation, not a formal presentation.

Guidance:
* Do not make a slide deck
* Open source code, architectural diagrams, and/or a one-page summary can be helpful
* Be ready to cover high-level architecture decisions and low-level implementation details
* Discuss decisions made, bottlenecks and how you solved them, and what you would do differently
* Speaking about a major bug/SEV and the solution can be very helpful
* Some candidates prepare two projects and ask which the interviewer prefers
* While emphasis is on technology, success metrics can be helpful
* Be prepared to discuss what you would do differently

---

## Project Overview
Unified Reconciliation (UR) — State Machine v2 and Platform Evolution
- Scope: Extend store-only reconciliation to .com flows; unify keys and state handling across multiple upstreams; stabilize projections and improve operability.
- Role: Proposed and led design for single-actor-per-order with invoice-level state; drove POC, performance testing, and Lightbend design review; coordinated cross-team adoption plan.
- Constraints: Mixed identifier availability across upstreams (OrderId, InvoiceId, PaymentHandle, etc.), holiday code-freeze deadlines, reliability/cost targets.

## Problem and Requirements
Goals
- Support .com use cases where upstreams provide partial keys; ensure deterministic routing and correctness of state transitions.
- Improve projection reliability and reduce operational overhead.
- Maintain performance at high throughput with a clear scale path.

Non-functional
- Availability: predictable failover and recovery procedures.
- Performance: sustain tens of thousands of req/s at scale; keep average latencies sub-second.
- Operability: simplified persistence and projection stack; clear observability.

## Architecture and Components
UR State Machine v2
- Single actor at order level; invoice-level state maintained within order actor (reduces actor cardinality; preserves order context).
- Persistence: Akka Persistence R2DBC (PostgreSQL) with data partitioning; projections via Akka Projection to SQL.
- Messaging: integrates BUA, CTH, OMS, PLUTUS, UPP, FDF; consistent keying strategy (OrderId as primary), with invoice-level detail in state.
- Future: AKKA→PEKKO migration after feature parity.

## Implementation Details
Key decisions and trade-offs
- Order-level actor with invoice state vs per-invoice actors: chosen to simplify routing and provide holistic order view; fewer entities; endorsed by Lightbend.
- R2DBC Postgres vs Cassandra: reduced ops cost and complexity; partitioned tables across multiple DBs preserve scale-out; documented failover considerations.
- External shard allocation to align Kafka partition consumption with shard locations (improves locality and throughput).

## Reliability and Performance
Performance test (POC)
- Infra: AWS RDS Postgres db.m5d.2xlarge (8 vCPU/32 GB), EKS 5× m5.xlarge (4 vCPU/16 GB each).
- Load: 1,000,000 requests across 2,000 entities.
- Results: ~20,283 requests/sec; avg 484.22 ms; fastest 2.67 ms; slowest 2.85 s.

Reliability
- Partitioned persistence (Akka R2DBC) across tables/DBs reduces hotspots; guidance documented for failover and auto-restart.
- Projections via Akka Projection to SQL improved stability vs prior pipeline.

## Observability and Operations
Metrics and runbooks
- Track command throughput, entity activation, replay durations, projection lag, DB partition health.
- Structured logs with correlation IDs; tracing across ingest → actor → projection.
- Runbooks for DB failover, partition rebalancing, and projection backfill.

## Risks, Incidents, and SEVs
Identified risks and mitigations
- Single-node DB failure: mitigate with automatic restarts, multi-AZ failover, and clear recovery steps.
- Schema/key evolution between upstreams: design supports schema evolution; order-level actor masks variability.
- Migration risk from legacy events: one-time migration plan documented; dual-run/window considered during ramp-up.

## Outcomes and Impact
Program outcomes
- Design approved by Lightbend; MoM recorded with owners (projections fix vs SM v2 features).
- Stabilized projections path; reduced operational burden compared to Cassandra while preserving scale via partitioning.
- Clear migration path and readiness to onboard .com flows with partial keys.

## What Went Well
Strengths
- Clear articulation of trade-offs and rationale; external validation (Lightbend) and empirical load tests.
- Holistic design spanning domain model, persistence, and operations; strong documentation and diagrams.

## Improvements
Next improvements
- Tighten success metrics for reconciliation accuracy and time-to-reconcile across store vs .com flows.
- Expand multi-region DR drills; automate projection backfills.
- Complete AKKA→PEKKO migration and compare perf/operability deltas.

## What Could Have Been Better
- Earlier E2E functional testing across domains
  - Formalize cross-domain E2E scenarios (store & .com) as part of definition of ready; fail fast on contract gaps.
- Common, always-on pre-prod environment
  - A single stable, data-seeded environment shared by CTH/OMS/UPP/BUA/FDF/PLUTUS/URS to validate flows end-to-end continuously.
- BDD and domain-owned test coverage
  - Encourage each domain to maintain BDD specs and near-100% coverage of domain behaviors; publish shared test catalogs for reuse.
- Earlier discovery of domain edge cases
  - Example: PLUTUS behavior when invoice is generated without successful auth → no captured events emitted. Add domain-specific contract tests to surface such behaviors upfront.

## Follow-ups
Artifacts and references
- PDFs/MDs: exports/pdf/*UR-*.pdf, exports/parsed/*UR-*.md (e.g., UR State machine Design, Flat Design, Communication Design, C4 diagram, Current Plan, Redesign).
- POC repository: https://github.com/krushnaDash/spring-akka
- Minutes of Meeting: decisions and owners (see UR State machine Design document).


