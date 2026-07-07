# Design & Architecture

This interview focuses on system design and architecture—distributed systems and APIs—with emphasis on building/implementing a structure or product. Be thorough and drive the conversation with clarifying questions, trade-offs, and measurable outcomes.

Topics to be familiar with include:
* Concurrency (threads, deadlock, starvation, consistency, coherence)
* Abstraction (understanding how OS, filesystem, and database works)
* Real-world performance (relative performance RAM, disk, network, SSD)
* Availability and Reliability (durability, understanding how things can fail)
* Data storage (RAM vs. durable storage, compression, byte sizes)
* CAP Theorem
* Byte math

At this level, be proactive in:
* Communication and steering the conversation
* Demonstrating familiarity with complex systems
* Explaining trade-offs and resource management
* Identifying key metrics you would monitor

---

## Problem Statement
Example prompts and scope from the original guidance:
* Design Uber. Design a simple version of Instagram. Design Facebook News Feed API. Design Ticketmaster. Design a Top 10 Listens tool.
* Emphasis on API design and how technical choices impact user experience. Assume standard infra components (e.g., LB, managed DB) can be sourced; focus on end-to-end product architecture and UX impact.

## Clarifying Questions and Assumptions
For “Design a simple Instagram” (illustrative):
* Clients: mobile apps (iOS/Android) and possibly web. Auth via bearer token in headers.
* Functional: upload photos, manage friends/follows, search users, generate news feed, notifications.
* Non-functional: upload resiliency (resume), latency targets for feed (<200ms p95 read), upload throughput, storage durability, cost.
* Constraints: large media objects, network variability; need pagination and backfills.

## High-Level Architecture
Clients → API Gateway → Services (Auth, Upload, Users/Graph, Posts/Feed, Notification) → Storage (Blob store, Metadata DB, Indexes) → Async (Queues/Workers) → Observability (logs/metrics/traces).
Key flows:
* Upload: client requests pre-signed URL with TTL → multipart HTTP upload to blob storage → callback/worker validates/compliance checks → metadata persisted.
* Social Graph: follow/unfollow; search with pagination; friendship status and states (requested/accepted/rejected).
* Feed: cursor-based pagination; enrich posts with counts and top comments; notifications via long polling or server-sent events.

## Detailed Design
APIs:
* POST /uploads: returns pre-signed URL (TTL) and upload ID; supports parallel/multipart uploads and resumability.
* POST /posts: finalize after upload; includes media ID, caption, visibility.
* POST /follow, DELETE /follow, GET /users/search?cursor=… with status.
* GET /feed?cursor=… returns posts + counts + top comments; uses cursor pagination for efficient scrolling.

Data model highlights: Users, Relationships (directed for follow), Posts (media refs), Reactions/Comments (counters + sampled top comments), Notifications.

Storage & infra: Blob store for media; relational DB for metadata and graph (or specialized graph/index service if required at scale); cache hot paths (feed, profile, counts); queues for async processing (compliance, thumbnails, fanout/backfill).

Consistency & UX: eventual consistency acceptable for counts; strong consistency where user actions need immediate reflection; idempotent endpoints for retries.

## Scalability and Reliability
Partition users/posts by user ID; replicate metadata; CDN for media; multiregion read replicas; DR runbooks; idempotent upload finalization; backpressure on ingestion pipelines; rate-limits on write-heavy endpoints.

## Performance Considerations
Latency budgets per path (feed <200ms p95); presigned uploads to offload API; indexes on (user_id, created_at) and graph edges; cursor pagination; cache warm strategies; cost controls on storage/egress.

## Observability and Operations
SLOs for feed/read and upload success; metrics on upload retries, feed latency, error rates; structured logs with correlation IDs; distributed tracing across gateway/services/workers; oncall playbooks for media spikes.

## Trade-offs and Alternatives
* Notifications: long polling vs. SSE vs. WebSockets — start with SSE for simplicity; upgrade to WebSockets for interactive features.
* Feed: precomputed fanout vs. on-demand aggregation — begin on-demand; precompute for high-fanout users.
* DB: relational vs. NoSQL — relational for transactional integrity and joins early; move heavy reads to denormalized stores as scale grows.

## What Went Well
<!-- TODO: Strong areas of the design/communication. -->

## Improvements
<!-- TODO: Gaps, missed edge cases, areas to deepen. -->

## Follow-ups
<!-- TODO: Reading, proofs-of-concept, or artifacts to produce. -->

## Product Design example

The Product Design interview typically focuses on the more holistic parts of building a software solution and less on the back end components required.
* focus on good API
* Extend the API as product evlove (vesrionin)
* Check the graph QL fedration layer
* Inverted Indexes
* Polling vs Websocket with multiple back-end server, vs server send evetns 

---

## Interviewer-Specific Prep: Tuncay Tekle (Product Architecture)

**Profile**: PhD in Efficient Datalog Queries (complexity guarantees), Meta since Dec 2023, 13 yrs industry (LogicBlox declarative DB, Columbus Consulting retail data for Nike/PepsiCo/Ralph Lauren), teaches data modeling. Values: reliable, fast, maintainable.

### His Focus Areas — Prioritize These in Your Design Walkthrough

**1. Lead with Data Model (not services)**
- He'll expect you to start with entities, relationships, cardinality, and access patterns.
- State partition keys, clustering keys, and indexes explicitly.
- From URS: "OrderId is the primary entity; 1:N invoices; 1:N payment events per invoice. Single actor per order because..."

**2. Know Complexity at Every Layer**
- Have Big-O ready for every read/write path.
- Example: "Cassandra write = O(1) per partition. Read = O(B) where B = buckets scanned, typically 1–2. Fan-out = O(N/P) per edge pod."
- He will ask: "What's the complexity of that?" — don't hand-wave.

**3. Quantify Consistency Windows**
- Never say just "eventually consistent." Say: "Redis ↔ Cassandra lag bounded by Kafka consumer lag, typically <100ms. Projection lag bounded at ~1 hour."
- From URS: projection lag thresholds, backfill procedures, dual-run shadow reconciliation.

**4. Trace a Single Event End-to-End**
- Be ready to walk through every hop: Client → Gateway → Service → Kafka → (Fan-out + Persistence + Cache) → Client query.
- At each hop: latency, failure mode, consistency guarantee.
- From URS: event → normalizer → Kafka → actor → journal → projection → dashboard.

**5. Argue Both Sides of Trade-offs**
- He'll ask "Why not Y?" for every decision. Prepare:
  - Per-order vs per-invoice actors
  - R2DBC/Postgres vs Cassandra
  - Java vs Scala for Akka
  - WebSocket vs SSE vs long-polling
  - Cassandra vs DynamoDB

**6. Back-of-Envelope with Precision**
- From URS POC: 1M requests, 2K entities, ~20,283 req/s, avg 484ms, RDS db.m5d.2xlarge + 5× m5.xlarge EKS.
- Know what limits throughput: CPU, I/O, network, connection pools.
- Be ready for "What happens at 10× scale?"

**7. Failure Scenarios with Specific Recovery**
- For every component: what fails, how you detect it, how you recover.
- From URS: multi-AZ failover, auto-restarts, Kafka replay on DB recovery, dead-letter queues, schema rollback runbooks.

### Quick Cheat Sheet: His Follow-Up Patterns

| You Say | He'll Ask |
|---|---|
| "We use Cassandra" | "Partition key? Read complexity?" |
| "Eventually consistent" | "Worst-case staleness? How bounded?" |
| "Cache in Redis" | "Invalidation strategy? Cache miss path?" |
| "Use Kafka" | "How many partitions? Consumer scaling? Ordering?" |
| "Scales horizontally" | "Show me the math. Where does it stop?" |
| "Retries on failure" | "Dedup strategy? Retry budget?" |
| "Chose X over Y" | "Argue for Y. When would Y win?" |

### URS Talking Points Mapped to His Focus

| His Focus | Your URS Example |
|---|---|
| Data model first | Order → Invoice → Payment events; single actor per order; unified JSON event structure |
| Complexity | 20K req/s POC; O(1) actor lookup via shard-aligned Kafka partitions |
| Schema evolution | Version headers, backward-compatible fields, alternate_payment_id fallback key |
| Failure handling | Multi-AZ, Kafka replay, dead-letter, projection backfill, dual-run shadow mode |
| Trade-offs | Per-order vs per-invoice actors; R2DBC vs Cassandra; Java vs Scala |
| Maintainability | Normalizer decouples upstream variability; config-driven processor onboarding |
| Consistency | Projection lag bounded ~1hr; event journal strongly consistent; projections eventually consistent |

See full mock question set: `meta/mock-questions-tuncay-tekle.md`