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
- Per-invoice actor vs per-tender actors
  - Chosen for simpler routing, fewer entities, holistic order view; endorsed by Lightbend.
- R2DBC/Postgres vs Cassandra
  - Lower ops burden and cost; partitioned tables preserve scale-out; clear failover runbooks.
- Deterministic keying under ambiguity
  - Order-level primary key masks upstream key variability while preserving invoice detail.
- Using java as language of development instead of Scala
- Using Spring for API and web interface development, instead of Akka HTTP
- development of Unified normalizer who process the events from multiple sources and then transform them into a unified events to 
- single kafka topic like below Unified JSON strcture

``` JSON
order_id:
invoice_id
EventType : Invoice | Auth | Accounting |Tender | Settlement

InvoiceEvent 
amount:
type:
date:
BusinessUnit

AuthEvent 
PayemntId:
amount:
provider:
cardType:
function: { AUTHORIZATION | REVERSAL | REFUND | REFUND_REVERSAL}

AccountingEvent 
amount:
paymentId:
glAccountNumber:
postingDate:
BusinessUnit:

TenderEvent 
amount:
paymentId:
provider:
cardType:
WriteOff: True, False, Conditional

SettlementEvent 
amount:
paymentId:
provider:
cardType:

```
event_journal : The primary table used for event sourcing
event_snapshot : The primary table used for state snapshotting

``` JSON
event_journal_0
{
 slice:Int
 persistence_id:varchar ## actor id (order_id+Invoice_id)
 SequenceNumber:Long ## event sequence number
 event_payload : Byte ## event payload (JSON)
 .....   
}
snapshot_0
{
 slice:Int
 persistence_id:varchar ## actor id (order_id+Invoice_id)
 SequenceNumber:Long ## event sequence number
 snapshot BYTEA ## snapshot payload (JSON)
 .....   
}
```
persistence_id -> Hashing to find Silce and then DB to store the event
R2DBC

- Projection using akka projection, for Dashboard and othere analytical usecases, eventully consistency (may stale by 1 hours)


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

## Bottlenecks and How you solve them
How the PLUTUS the .com systme which assign Tender to invoice behave in certain edge case.

When failed settlements are retried from PLUTUS, if the authorization successes upon reattempt, PLUTUS will proceed
with capture. However, if the authorization fails after all retries, there will be no capture message. To distinguish this case,the URS system must process the authorization messages to determine if the final retry of the authorization was
unsuccessful.
In URS the decsion was taken to process all the capture events from PLUTUS to find the tender.

But this auth message can be used as tender, we need create tender events from auth message in certain
case when we will know there will not be any further capture message, as all retry of auth is falied.

The normaliser will have the logic to create tender events from auth message in certain case when we will know there will not be any further capture message, as all retry of auth is falied.

Mapping

Capture message with "isFinalRetry: false" → Tender event with "writeOff": "False"
Capture message with "isFinalRetry: True" → Tender event with "writeOff": "Conditional"
Auth message with "isFinalRetry: false" → No message to sent
Auth message with "isFinalRetry: true" and pgPmtTxnStatus is not "SUCCESS" → Tender event with "writeOff": "True"




## Speaking about a Majro Bug and How you solve them
- UPP development onboarding is not 100%, which means we still need to support multiple walmart payment Platform like EPAY, CPAY, PGPayments.
- Some clients(RX easy Pay, Walmart Pharmacy, ..) calling to EPAY for AUTH are not including the order_id and payment_id in the auth call, or the order_id and payment_id was not consistent.
- Due to which some AUTH events publish from EPAY was missing the order_id and Payment_id, or they will not match
- Subsequent system like CTH has the logic to generate order_id and payment_id if they are not present in the event.
- This come as blocker, with this bug we will not able to reconcile the AUTH events with the order and payment.

- Qucik solution was to : Ask all the clients to include the order_id and payment_id in the auth call. Which is not possible for company like walmart as the payment platfrom Epay itself deos not know who all clinets are 

- Right solution : Always generate a alternate_payment_id by combing key business fields like
siteNumber, TerminalId, TenderType, authorizerId,authorizedAmount, referenceNumber, approvalNumber, pansurrogate.value

- When the normaliser procss the AUTH and Invoice events it will generate the alternate_payment_id and enrich it.

- Similarly the Unified settlement system will use the same logic to generate the alternate_payment_id and enrich it.
- An ETL jobs will be run from the Projection DB for all the mismatch order_id and payment_id from Auth and Tender events.

Now with this we will 3 cases in State machine

Case 1 : Happy path where the order_id and payment_id all match, no issues and puzzle solved
Case2 : Order_id matched, but payment_id not, in that case it is within the same entity in the sate macine the reconcilation can be done by using the alternate_pyment_id
case3: Order_id not matched, then we have merge the Tender and accounting with Auth and Settlement, uing the alternate_payment_id
```
case 1 : 
order_id: 123
Tender: P101
Auth: P101
Settlement: P101
Accounting: P101

Case 2: Order_id matched, but payment_id not
order_id: 123
Tender: P100
Auth: P102
Settlement: P102
Accounting: P102

As the order_id matched this will be under one actor entity and the reconcilation can be done by using the alternate_payment_id

Case 3:Both order_id and payment_id not matched and there will be multiple actor entities for the same order

order_id: 1004
Tender: P100
Accounting: P100


order_id: A1004
Auth: AP1001
Settlement: AP1001

Here both actor entities are under different order_id, they need to be merged by the ETL jobs and resend the 
auth and settlement events with correct order_id and payment_id, using the alternate_payment_id.
```

## What Could Have Been Better
- Earlier E2E functional testing across domains
  - Formalize cross-domain E2E scenarios (store & .com) as part of definition of ready; fail fast on contract gaps.
- Common, always-on pre-prod environment
  - A single stable, data-seeded environment shared by CTH/OMS/UPP/BUA/FDF/PLUTUS/URS to validate flows end-to-end continuously.
- BDD and domain-owned test coverage
  - Encourage each domain to maintain BDD specs and near-100% coverage of domain behaviors; publish shared test catalogs for reuse.
- Earlier discovery of domain edge cases
  - Example: PLUTUS behavior when invoice is generated without successful auth → no captured events emitted. Add domain-specific contract tests to surface such behaviors upfront.

## What Should I Do Differently

- **Validate upstream data contracts earlier with concrete test data**
  - I relied on API specs and meetings to understand upstream behavior (CTH/OMS/UPP/PLUTUS). In hindsight, I should have processed the real production payloads from day one and built contract validation tests before writing any actor logic. The EPAY missing order_id/payment_id bug (§Major Bug) would have surfaced weeks earlier if I had run real auth events through the normalizer during design phase, not after integration.

- **Build the alternate_payment_id reconciliation path from the start, not as a fix**
  - The alternate key logic (siteNumber + TerminalId + TenderType + ...) was designed reactively after discovering the EPAY inconsistency. I should have anticipated that upstream key quality would vary across platforms (EPAY, CPAY, PGPayments) and designed the normalizer with a primary + fallback key strategy from the architecture phase. This would have avoided the ETL merge job for Case 3 being a late addition.

- **Prototype the projection stability earlier with realistic load**
  - Projection lag and stability issues were discovered during load testing. I should have set up a continuous projection stress test (even at 10% scale) from the first sprint, rather than treating projections as a secondary concern after the state machine was working. Projections are a critical read path — they deserved first-class attention in the POC.

- **Push harder for a shared pre-prod environment from the architecture review**
  - I flagged environment gaps in cross-functional meetings but didn't escalate strongly enough. As the architect, I should have made a shared, always-on pre-prod environment a hard prerequisite with leadership, not a nice-to-have. The lack of it delayed end-to-end validation by weeks.

- **Document edge-case decision trees for the normalizer upfront**
  - The PLUTUS retry/capture/auth logic (§Bottlenecks) was complex and discovered incrementally. I should have created a formal decision matrix (auth success/fail × isFinalRetry × capture present/absent → event type) during the design phase and reviewed it with the PLUTUS team before coding. This would have prevented ambiguity in the normalizer logic.


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
