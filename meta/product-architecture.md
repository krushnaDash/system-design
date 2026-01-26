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

