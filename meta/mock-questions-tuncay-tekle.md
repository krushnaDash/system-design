# Mock Questions — Product Architecture Interview (Tuncay Tekle Profile)

Interviewer background: PhD in Efficient Datalog Queries (complexity/logic), Meta since Dec 2023, 13 years industry (LogicBlox declarative DB, Columbus Consulting retail data solutions for Nike/PepsiCo/Ralph Lauren), teaches data modeling. Values: reliable, fast, maintainable code.

---

## Section 1: Data Model & Schema Design (His PhD + Teaching Focus)

### Q1. "Walk me through your data model. What are the core entities and how do they relate?"
**What he's probing**: Can you think entity-first? Do you understand cardinality, access patterns, and normalization trade-offs?

**How to answer well**:
- Start with entities and relationships (not services or infra).
- State cardinality explicitly (1:N, M:N).
- Call out access patterns that drive schema decisions.
- Example from your URS experience: "OrderId is the primary entity; each order has 1:N invoices; each invoice has 1:N payment events. We chose a single actor per order because..."

**Follow-up he'll likely ask**: "Why not model it the other way? What would change if you used per-invoice entities instead?"

### Q2. "How do you handle schema evolution when upstream contracts change?"
**What he's probing**: Real-world data messiness — his retail consulting background means he's seen this constantly.

**How to answer well**:
- Reference your URS experience: schema version headers, backward-compatible fields, order-level keying to mask upstream variability.
- Mention the alternate_payment_id pattern as a concrete example of designing for key instability.
- Discuss forward/backward compatibility strategies.

### Q3. "What indexes do you need? What's the read complexity for your primary query?"
**What he's probing**: PhD-level — he wants Big-O, not hand-waving.

**How to answer well**:
- Be specific: "Primary read is by (live_video_id, bucket) with clustering on created_at DESC — that's O(1) partition lookup + O(K) scan where K = page size."
- For secondary access patterns, explain why you chose (or avoided) secondary indexes.
- Mention prepared statements, partition-aware routing.

---

## Section 2: Complexity & Performance (His PhD Thesis Area)

### Q4. "What's the time complexity of your write path? Your read path? Where's the bottleneck?"
**What he's probing**: Can you reason about system complexity end-to-end, not just individual components?

**How to answer well**:
- Break down per-component: "Write: O(1) Kafka produce + O(1) Cassandra write per partition. Read: O(B) where B = buckets scanned for pagination, typically 1–2."
- Identify the bottleneck: "Fan-out is O(N) where N = viewers. We mitigate with tiered relay architecture reducing per-node work to O(N/P) where P = edge pods."
- Use concrete numbers from your designs (e.g., 1K comments/sec, 100M viewers).

### Q5. "You said this handles 20K req/s. Walk me through the capacity math."
**What he's probing**: Can you do back-of-envelope calculations precisely?

**How to answer well**:
- Reference your URS POC: "1M requests across 2K entities on RDS db.m5d.2xlarge + 5× m5.xlarge EKS = ~20,283 req/s, avg 484ms."
- Show you understand what limits throughput: CPU, I/O, network, connection pools.
- Discuss what happens at 2× or 10× scale — where does it break first?

### Q6. "How does your design scale with 10× more data? 100×?"
**What he's probing**: Do you understand asymptotic behavior of your system, not just current numbers?

**How to answer well**:
- Identify what scales linearly (stateless services, Kafka partitions) vs what doesn't (hot partitions, single-node bottlenecks).
- Discuss partitioning strategies: bucketed keys in Cassandra, shard-aligned Kafka consumers.
- Mention what you'd change at 100× (e.g., switch from scatter-gather to precomputed views).

---

## Section 3: Reliability & Failure Handling (His "Reliable" Value)

### Q7. "What happens when your database goes down? Walk me through the failure scenario."
**What he's probing**: Do you think about failure modes proactively?

**How to answer well**:
- Be specific: "Kafka retains events; on DB recovery, persistence consumer replays from last committed offset. Redis serves reads during the gap. We accept eventual consistency — comments may be delayed but not lost."
- Reference your URS experience: multi-AZ failover, auto-restarts, recovery runbooks.
- Mention monitoring: how do you detect the failure? What alerts fire?

### Q8. "How do you ensure exactly-once processing in your event pipeline?"
**What he's probing**: Deep understanding of distributed systems guarantees — not just buzzwords.

**How to answer well**:
- Distinguish at-least-once + idempotent consumers (your URS approach) from true exactly-once.
- Explain dedupe keys, idempotent writes (Cassandra upserts are naturally idempotent).
- Discuss Kafka consumer offsets, commit strategies, and what happens on consumer restart.

### Q9. "Your system has eventual consistency. What's the worst case? How do you bound it?"
**What he's probing**: Precise understanding of consistency windows, not vague "it's eventually consistent."

**How to answer well**:
- Quantify: "Redis ↔ Cassandra lag is bounded by Kafka consumer lag, typically <100ms. Projection lag for dashboards is bounded at ~1 hour by design."
- Explain what happens if the bound is violated — alerting, backfill procedures.
- Reference your URS projection lag thresholds and backfill procedures.

---

## Section 4: API Design & Maintainability (His "Maintainable" Value)

### Q10. "Design the API for this feature. How would you version it?"
**What he's probing**: Clean, RESTful design; forward-thinking about evolution.

**How to answer well**:
- Start with resources and verbs, not implementation.
- Discuss cursor-based pagination (not offset) — explain why.
- Version strategy: URL path (/v1/) vs header-based; backward compatibility guarantees.
- Reference your product-architecture.md notes on API evolution and GraphQL federation.

### Q11. "A new product requirement comes in that changes the data model. How do you handle the migration?"
**What he's probing**: Real-world maintainability — his 13 years of consulting means he's seen migrations go wrong.

**How to answer well**:
- Dual-run / shadow mode (your URS approach).
- Schema evolution with backward-compatible fields.
- Feature flags per upstream / per client.
- Rollback strategy — what if the migration fails halfway?

### Q12. "How do you decouple your services? What contracts exist between them?"
**What he's probing**: Separation of concerns, clean boundaries — his LogicBlox background is all about declarative, well-defined interfaces.

**How to answer well**:
- Event-driven decoupling via Kafka (your URS normalizer pattern).
- Clear ownership: upstreams own source events, URS owns reconciliation state.
- Schema contracts with version headers.
- Reference your domain boundaries section.

---

## Section 5: Trade-off Discussions (His Consulting + Academic Background)

### Q13. "You chose X over Y. Convince me Y was the wrong choice."
**What he's probing**: Can you argue both sides? Do you understand the trade-off space?

**Prepare for these specific trade-offs from your experience**:
- Per-order actor vs per-invoice actor
- R2DBC/Postgres vs Cassandra
- Java vs Scala for Akka
- Spring vs Akka HTTP
- WebSocket vs long-polling vs SSE
- Cassandra vs DynamoDB for comments

### Q14. "What would you change about this design if cost was the primary constraint? If latency was?"
**What he's probing**: Can you re-optimize for different objectives?

**How to answer well**:
- Cost-optimized: fewer replicas, larger batch windows, cold storage earlier, spot instances.
- Latency-optimized: more caching layers, precomputed views, edge deployment, read replicas.
- Show you understand the Pareto frontier — you can't optimize both simultaneously.

### Q15. "What's the most important metric to monitor for this system? Why?"
**What he's probing**: Operational maturity — do you think about observability as a first-class concern?

**How to answer well**:
- Pick ONE metric and defend it (e.g., "end-to-end comment delivery latency p99 — because it captures the full pipeline health").
- Then layer: Kafka consumer lag, fan-out lag, error rates, connection counts.
- Reference SLOs and alerting thresholds.

---

## Section 6: Deep Technical Probes (His Datalog/Logic Background)

### Q16. "How does your Kafka partitioning strategy interact with your database partitioning? Are they aligned?"
**What he's probing**: Cross-layer consistency — his Datalog work is about understanding how rules compose.

**How to answer well**:
- Your URS design explicitly aligns Kafka partitions with actor shard allocation — explain why (minimize cross-node chatter).
- For live comments: Kafka partitioned by videoId, Cassandra partitioned by (videoId, bucket) — explain the mismatch and how scatter-gather handles it.

### Q17. "Walk me through what happens to a single event from ingestion to query-ability. Every hop."
**What he's probing**: End-to-end understanding — no black boxes.

**How to answer well**:
- Trace the full path: Client → Gateway → Service → Moderation → Kafka → (Fan-out + Persistence + Redis) → Client query.
- At each hop: what's the latency? What can fail? What's the consistency guarantee?
- This is where your URS normalizer → Kafka → actor → projection → dashboard story shines.

### Q18. "You mentioned idempotent consumers. How exactly do you implement deduplication?"
**What he's probing**: Implementation depth — not just architecture diagrams.

**How to answer well**:
- Dedupe key = (eventType, orderId, paymentId, timestamp) or similar composite.
- Storage: dedupe table with TTL, or Cassandra's natural upsert behavior.
- Edge cases: what about redelivery after consumer restart? Kafka offset commit timing.

---

## Section 7: Meta-Specific Product Questions

### Q19. "Design [Facebook feature X] — start with the data model."
**Likely prompts** (based on Meta's known question bank):
- Design Facebook News Feed ranking
- Design Facebook Marketplace search
- Design Instagram Stories
- Design Facebook Live Comments (you have this prepared)
- Design a notification system at Meta scale

**His twist**: He'll likely start from data model, then ask about query complexity, then scale.

### Q20. "How would you build this at Meta scale (3B+ users)? What changes from your initial design?"
**What he's probing**: Can you think at Meta's scale, not just your current employer's?

**How to answer well**:
- Multi-region by default (not an afterthought).
- TAO-like graph store for social data.
- Billions of rows — partition everything.
- Feature flags, gradual rollout, shadow traffic.

---

## Quick Reference: His Likely Follow-Up Patterns

| Your Statement | His Likely Follow-Up |
|---|---|
| "We use Cassandra" | "What's the partition key? What's the read complexity?" |
| "It's eventually consistent" | "What's the worst-case staleness? How do you bound it?" |
| "We cache in Redis" | "What's the invalidation strategy? What happens on cache miss?" |
| "We use Kafka" | "How many partitions? How do consumers scale? What about ordering?" |
| "It scales horizontally" | "Show me the math. Where does it stop scaling linearly?" |
| "We handle failures with retries" | "How do you prevent duplicate processing? What's the retry budget?" |
| "We chose X over Y" | "Argue for Y. When would Y be better?" |

---

## Preparation Checklist

- [ ] Know Big-O for every read/write path in your designs
- [ ] Have back-of-envelope numbers ready (throughput, storage, latency)
- [ ] Be able to trace a single event end-to-end through every component
- [ ] Prepare both sides of every trade-off decision
- [ ] Know your data model cold — entities, relationships, keys, indexes
- [ ] Have failure scenarios rehearsed with specific recovery steps
- [ ] Quantify consistency windows (not just "eventual")
- [ ] Prepare 2–3 concrete examples from URS for each theme
