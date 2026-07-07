Questions:
Design a Facebook live comments system, which can support 100M concurrent users for a live video.

Functional Requirements:
-user can post a comments
-user view the latest 20 comments
-user can delete the comments
-User can scroll back to view older comments


Non-Functional Requirements:
- Support 100M concurrent users for a live video.
- posting around 1000 comments per second
- max latency of 1 second

---

## High-Level Architecture

```
┌──────────┐       ┌────────────────┐       ┌───────────────────┐
│  Client   │──WS──▶  WebSocket     │──────▶│  Comment Service   │
│ (App/Web) │◀──WS──│  Gateway      │       │  (Write Path)      │
└──────────┘       │  (Edge PoPs)   │       └────────┬──────────┘
                   └────────────────┘                │
                                        ┌────────────┤
                                        ▼            ▼
                               ┌──────────────┐  ┌──────────────┐
                               │  Moderation   │  │  Kafka       │
                               │  Service      │  │  (Partitioned│
                               │  (Spam/Abuse) │  │  by videoId) │
                               └──────────────┘  └──────┬───────┘
                                                        │
                                        ┌───────────────┼───────────────┐
                                        ▼               ▼               ▼
                               ┌──────────────┐ ┌──────────────┐ ┌───────────┐
                               │  Fan-out      │ │  Persistence │ │ Analytics │
                               │  Service      │ │  Service     │ │ Service   │
                               │  (Push to WS) │ │  (DB writes) │ └───────────┘
                               └──────────────┘ └──────────────┘
```

**Flow**:
1. Client posts a comment via **WebSocket** (HTTP POST as fallback).
2. **Gateway** authenticates, rate-limits, and forwards to **Comment Service**.
3. Comment Service runs **Moderation** (sync fast-path < 50 ms).
4. Approved comment is published to **Kafka** topic partitioned by `liveVideoId`.
5. **Fan-out Service** consumes Kafka and pushes to all connected WebSocket subscribers (see detailed fan-out explanation below).
6. **Persistence Service** consumes the same topic and writes to the database.
7. Client joining mid-stream fetches recent comments via REST (served from cache).

---

## API Design

### WebSocket (Primary — Real-Time Channel)

**Connect**: `wss://live.fb.com/ws?live_video_id={id}&token={auth_token}`

**Client → Server**
```json
// Post comment
{
  "type": "POST_COMMENT",
  "data": {
    "liveVideoId": "lv_xyz",
    "text": "Great stream!",
    "clientMsgId": "cm_001"
  }
}
```

**Server → Client**
```json
// New comment broadcast
{
  "type": "NEW_COMMENT",
  "data": {
    "commentId": "c_abc123",
    "liveVideoId": "lv_xyz",
    "userId": "u_456",
    "userName": "Jane Doe",
    "userAvatar": "https://...",
    "text": "Great stream!",
    "createdAt": "2026-02-07T10:00:01.234Z"
  }
}
```

### REST API (Fallback + History)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/live/{liveVideoId}/comments` | Post a comment (HTTP fallback) |
| `GET` | `/api/v1/live/{liveVideoId}/comments?cursor={ts}&limit=20` | Fetch recent / older comments (cursor-based pagination) |
| `DELETE` | `/api/v1/comments/{commentId}` | Delete comment (author/mod) |

#### POST /api/v1/live/{liveVideoId}/comments

Request:
```json
{ "text": "Hello!" }
```

Response (201):
```json
{
  "commentId": "c_abc123",
  "liveVideoId": "lv_xyz",
  "userId": "u_456",
  "text": "Hello!",
  "createdAt": "2026-02-07T10:00:01.234Z",
  "status": "VISIBLE"
}
```

#### GET /api/v1/live/{liveVideoId}/comments?cursor=&limit=20

Response (200):
```json
{
  "comments": [ ... ],
  "nextCursor": "2026-02-07T09:59:50.000Z",
  "hasMore": true
}
```

---

## Data Models

### Comment

| Field | Type | Notes |
|---|---|---|
| `commentId` | String (Snowflake ID) | Globally unique, time-sortable |
| `liveVideoId` | String | Partition key |
| `userId` | String | Author |
| `text` | String (max 500 chars) | Comment body |
| `createdAt` | Timestamp (ms) | Sort key; cursor for pagination |
| `status` | Enum: VISIBLE, DELETED, FLAGGED | Moderation state |

### LiveVideo (Reference)

| Field | Type | Notes |
|---|---|---|
| `liveVideoId` | String | Primary key |
| `streamerId` | String | Owner |
| `status` | Enum: LIVE, ENDED | |
| `startedAt` | Timestamp | |
| `endedAt` | Timestamp (nullable) | |

---

## Database Choices and Trade-offs

### Option A: Cassandra (Recommended for write path)

| Aspect | Detail |
|---|---|
| **Partition Key** | `liveVideoId` (with bucket suffix for hot streams) |
| **Clustering Key** | `createdAt DESC, commentId` |
| **Consistency** | `LOCAL_QUORUM` writes, `LOCAL_ONE` reads |

```
CREATE TABLE live_comments (
    live_video_id  TEXT,
    bucket         INT,          -- time bucket for hot-partition mitigation
    created_at     TIMESTAMP,
    comment_id     TEXT,
    user_id        TEXT,
    text           TEXT,
    status         TEXT,
    PRIMARY KEY ((live_video_id, bucket), created_at, comment_id)
) WITH CLUSTERING ORDER BY (created_at DESC, comment_id DESC);
```

| Pros | Cons |
|---|---|
| Write-optimized; linear horizontal scaling | No ad-hoc secondary queries |
| Multi-DC replication built in | Hot partition risk for celebrity streams |
| Predictable low-latency at scale | Operational complexity (compaction tuning) |
| Natural fit for time-series append | Read-before-write patterns are expensive |

**Hot-partition mitigation**: Bucket suffix on partition key (e.g., per-minute buckets). Client scatter-gathers across buckets. For a 100M-viewer stream, use ~60 buckets/hour.

### Option B: DynamoDB

| Aspect | Detail |
|---|---|
| **PK** | `liveVideoId#bucket` |
| **SK** | `createdAt#commentId` |

| Pros | Cons |
|---|---|
| Fully managed, auto-scaling | Cost at extreme scale (100M viewers) |
| Single-digit ms latency | 400KB item limit |
| DAX in-memory cache layer | Hot-partition throttling without sharding |
| No ops burden | Vendor lock-in |

### Option C: Redis (Sorted Sets) — Hot cache only

| Pros | Cons |
|---|---|
| Sub-ms reads for recent 20 comments | Volatile; not durable |
| Perfect for "latest N" window | Memory-bound; expensive at scale |
| Sorted sets naturally ordered by timestamp | Need a durable backing store |

### Recommended Combination

| Data | Primary Store | Cache | Rationale |
|---|---|---|---|
| Comments | **Cassandra** | **Redis** (recent 20 per stream as sorted set) | Durable, write-heavy; cache serves most reads |
| User/Video metadata | **PostgreSQL** | Redis / Memcached | Relational, low volume, strong consistency |
| Moderation signals | Feature Store | Redis | Real-time ML scoring |

---

## Infrastructure Components

### 1. Kafka (Message Broker)

- **Topic**: `live-comments`, partitioned by hash of `liveVideoId`.
- **Consumers**: fan-out service (per-region groups), persistence service, analytics.
- Decouples write path from read/push path.
- Retains events for replay (catch-up, reprocessing).

#### Partition Count

All comments for a single live stream hash to **one partition** (same `liveVideoId` → same partition). A single Kafka partition handles ~10K–100K msgs/sec, so 1,000 comments/sec per hot stream is fine.

The total partition count is driven by **global throughput across all concurrent streams**:
```
Example: 100K total comments/sec globally ÷ 10K msgs/sec per partition = ~10–50 partitions
```
Set **~50–100 partitions** to allow headroom and parallelism for consumers.

#### Consumer Groups — One Per Region (Critical Design Point)

In a Kafka consumer group, each partition is assigned to exactly **one** consumer in that group. If all regional relays shared one group, only one relay would get each message — the others would see nothing.

**Solution**: each region runs a **separate consumer group** so every region independently reads all partitions:

```
Consumer Group: "fanout-us-east"    → US-East relay instances consume ALL partitions
Consumer Group: "fanout-eu-west"    → EU-West relay instances consume ALL partitions
Consumer Group: "fanout-ap-south"   → AP-South relay instances consume ALL partitions
Consumer Group: "persistence"       → Persistence service (single global group)
Consumer Group: "analytics"         → Analytics pipeline (single global group)
```

Each regional consumer group gets a **full copy** of every message. Within a group, partitions are split across relay instances for parallelism (e.g., 3 relay pods in US-East each handle ~17 partitions out of 50).

```
                     Kafka Topic: live-comments (50 partitions)
                     ┌─────────────────────────────────────────┐
                     │  P0  P1  P2  ... P16 │ P17 ... P33 │ P34 ... P49 │
                     └──┬────────────────────┴──────┬───────┴──────┬─────┘
                        │                           │              │
          ┌─────────────┼───────────────────────────┼──────────────┼──────────┐
          │             │   group: fanout-us-east    │              │          │
          │     Relay-US-1 (P0–P16)    Relay-US-2 (P17–P33)   Relay-US-3     │
          └───────────────────────────────────────────────────────────────────┘
          ┌───────────────────────────────────────────────────────────────────┐
          │             │   group: fanout-eu-west    │              │          │
          │     Relay-EU-1 (P0–P16)    Relay-EU-2 (P17–P33)   Relay-EU-3     │
          └───────────────────────────────────────────────────────────────────┘
          ... (same for every region)
```

This means: a comment posted on `liveVideoId=X` lands on partition P7. **Every regional group** has a relay instance assigned to P7 that reads the message. All regions get it.

### 2. Fan-out Service (Comment Delivery) — Deep Dive

The core problem: when a single comment is posted, it must be delivered to **up to 100M open WebSocket connections** within < 1 second. No single machine can hold 100M connections. The fan-out service solves this with a **three-tier push architecture**.

#### 2a. Subscription Registry

When a client opens a WebSocket to watch a live stream, the **edge gateway** registers that connection locally:

```
// Each edge gateway pod maintains an in-memory map
subscriptions: Map<liveVideoId, Set<WebSocketConnection>>

// On client connect:
subscriptions.getOrCreate(liveVideoId).add(conn)

// On client disconnect:
subscriptions.get(liveVideoId).remove(conn)
```

Each edge pod only knows about its own connections (100K–500K per pod). There is **no global registry** of all 100M connections — that would be a bottleneck. Instead, we use a pub/sub broadcast so every edge pod that has subscribers for a stream receives the message.

#### 2b. Three-Tier Fan-out Architecture

```
                        ┌─────────────────────────────────────┐
                        │           Kafka Partition            │
                        │     (topic: live-comments,           │
                        │      key: liveVideoId)               │
                        └──────────────┬──────────────────────┘
                                       │
                          1 msg per comment
                                       │
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                        ▼
     ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
     │  Regional Relay  │    │  Regional Relay  │    │  Regional Relay  │
     │  (US-East)       │    │  (EU-West)       │    │  (AP-South)      │
     └────────┬────────┘    └────────┬────────┘    └────────┬────────┘
              │                      │                      │
     Fans out to edge pods    Fans out to edge pods   Fans out to edge pods
     in US-East region        in EU-West region       in AP-South region
              │                      │                      │
     ┌────┬───┴───┬────┐    ┌────┬──┴───┬────┐     ┌───┬───┴──┬────┐
     ▼    ▼       ▼    ▼    ▼    ▼      ▼    ▼     ▼   ▼      ▼    ▼
    Edge Edge   Edge  Edge  Edge Edge  Edge Edge  Edge Edge  Edge  Edge
    Pod  Pod    Pod   Pod   Pod  Pod   Pod  Pod   Pod  Pod   Pod   Pod
    (50K (50K   ...   ...   ...  ...   ...  ...   ... ...    ...   ...
    conn) conn)
     │     │
     ▼     ▼
   Clients (WebSocket push)
```

**Tier 1 — Kafka → Regional Relays** (small fan-out: ~5–10 regions)
- Each region has its own **Kafka consumer group** (e.g., `fanout-us-east`). See §1 above.
- Within a region, 2–3 relay pods split the 50 partitions between them for parallelism.
- Every region independently reads **all** messages. So a comment on partition P7 is read by the US-East relay assigned to P7, the EU-West relay assigned to P7, etc.
- Only ~5–10 consumer groups total — Kafka handles this trivially.

**Tier 2 — Regional Relay → Edge Pods** (medium fan-out: ~100–200 pods per region)

The relay's job: **route each Kafka message to only the edge pods that care about that `liveVideoId`**.

- The relay maintains an in-memory registry: `Map<liveVideoId, Set<gRPC stream to edge pod>>`.
- Edge pods register interest via **persistent gRPC bidirectional streams** (or Redis Pub/Sub).
- When a comment arrives from Kafka, the relay:
  1. Extracts `liveVideoId` from the message.
  2. Looks up the set of edge pod streams registered for that `liveVideoId`.
  3. Pushes the comment to **only those edge pods** (not all 200 in the region — only the ones with active viewers for that stream).
- This is a **server-to-server push** — very efficient, low overhead.

```
// Relay pseudocode
onKafkaMessage(comment):
    videoId = comment.liveVideoId
    edgePods = registry.get(videoId)     // e.g., 30 edge pods have viewers for this stream
    for pod in edgePods:
        pod.grpcStream.send(comment)     // server-to-server, ~0.1ms each
```

**Why the relay exists (and why edge pods don't consume Kafka directly)**:
- 1,000 edge pods can't each be a Kafka consumer — Kafka consumer groups max out at ~partition count consumers. With 50 partitions, only 50 consumers per group are useful.
- The relay is the **multiplexer**: it translates from Kafka's partition-based routing to `liveVideoId`-based routing to specific edge pods.
- Without the relay, you'd need every edge pod to see every message and filter locally — wasteful at scale.

**Tier 3 — Edge Pod → Clients** (large fan-out: ~100K–500K per pod)
- Each edge pod iterates its local `subscriptions[liveVideoId]` set and writes the comment JSON to each WebSocket.
- This is a tight loop: serializing the message once, then calling `ws.send(bytes)` for each connection.
- At ~100K connections per pod, this takes ~50–200 ms with async I/O (epoll/kqueue), well within the 1s budget.

#### 2c. How Edge Pods Register with Regional Relays

**The Problem You Identified**: A region has 3 relay pods splitting 50 partitions:
```
Relay-US-1 → P0–P16   (handles videoIds that hash to these partitions)
Relay-US-2 → P17–P33
Relay-US-3 → P34–P49
```
An edge pod has viewers for `videoId=X` which hashes to P7. If it only connects to Relay-US-2, it will never get those comments — Relay-US-1 owns P7.

**Three approaches to solve this** (from simplest to most decoupled):

---

**Option A: Edge pod connects to ALL relay pods in its region (Recommended — simplest)**

With only 2–3 relay pods per region, this is trivial. Each edge pod opens a persistent gRPC stream to **every** relay pod and sends SUBSCRIBE(liveVideoId) to **all** of them:

```
// Edge pod startup: connect to all relay pods in this region
relayConnections = [grpc.connect(relay1), grpc.connect(relay2), grpc.connect(relay3)]

// When first viewer for videoId=X connects to this edge pod:
for relay in relayConnections:
    relay.send(SUBSCRIBE(videoId=X, edgePodId=self))

// Only the relay that owns the partition for videoId=X will actually
// have messages to send. The other 2 relays simply hold an idle
// subscription — zero cost.
```

```
Edge Pod (has viewers for videoId=X, which hashes to P7)
    │
    ├── gRPC stream → Relay-US-1 (owns P0–P16, including P7)
    │                  ✅ Has messages for videoId=X → pushes them
    │
    ├── gRPC stream → Relay-US-2 (owns P17–P33)
    │                  ⏸️ No messages for videoId=X → idle stream
    │
    └── gRPC stream → Relay-US-3 (owns P34–P49)
                       ⏸️ No messages for videoId=X → idle stream
```

**Why this works well**:
- Only 2–3 gRPC connections per edge pod — negligible overhead.
- No need for partition-aware routing logic on the edge pod.
- **Rebalance-safe**: if Kafka rebalances and P7 moves from Relay-US-1 to Relay-US-3, the subscription is already registered on Relay-US-3. Messages flow seamlessly without any re-registration.

**How gRPC works here — bypassing the load balancer**:

The edge pod must connect to **each specific relay pod**, not a random one behind an LB. A standard L4/L7 load balancer would route all connections to one random relay, breaking the "connect to all" strategy.

```
❌ WRONG: Edge pod → LB → random relay pod (sticky to one)
✅ RIGHT: Edge pod → direct gRPC to each relay pod IP
```

**Solution: Headless service + client-side discovery**

In Kubernetes, deploy the relay pods behind a **headless service** (`clusterIP: None`). This makes DNS return **all pod IPs** instead of a single virtual IP:

```yaml
# Kubernetes: headless service for relay pods
apiVersion: v1
kind: Service
metadata:
  name: relay-us-east
spec:
  clusterIP: None          # ← headless: DNS returns all pod IPs
  selector:
    app: relay
    region: us-east
  ports:
    - port: 9090
      name: grpc
```

```
# DNS lookup returns individual pod IPs, not a single VIP
$ nslookup relay-us-east.ns.svc.cluster.local
  → 10.0.1.11   (Relay-US-1)
  → 10.0.1.12   (Relay-US-2)
  → 10.0.1.13   (Relay-US-3)
```

```
// Edge pod startup: resolve all relay pod IPs via headless DNS
relayIPs = dns.resolve("relay-us-east.ns.svc.cluster.local")
// Returns: [10.0.1.11, 10.0.1.12, 10.0.1.13]

// Open a persistent gRPC bidirectional stream to EACH pod directly
for ip in relayIPs:
    stream = grpc.connect(ip + ":9090")
    relayStreams.add(stream)

// Subscribe for a videoId on ALL streams
onNewViewer(videoId):
    for stream in relayStreams:
        stream.send(SUBSCRIBE(videoId))
```

**What about the relay pods (Kafka consumers) — are they behind an LB too?**

No. Relay pods are **Kafka consumers**, not HTTP servers. They don't sit behind an LB at all:
- Kafka assigns partitions to consumers directly via the consumer group protocol.
- Relay pods pull from Kafka — no inbound LB needed.
- The only inbound connections are gRPC streams from edge pods (which connect directly via headless service).

```
                    ┌─────────────────────────┐
                    │        Kafka             │
                    │  (assigns partitions     │
                    │   to relay consumers     │
                    │   via group protocol)    │
                    └─────┬──────┬──────┬──────┘
                          │      │      │        ← Relay pods PULL from Kafka (no LB)
                          ▼      ▼      ▼
                    Relay-1  Relay-2  Relay-3
                    (P0–16)  (P17–33) (P34–49)
                       ▲        ▲        ▲
                       │        │        │       ← Edge pods connect DIRECTLY
                       │        │        │          via headless DNS (no LB)
                    Edge Pod ───┘────────┘
                    (3 gRPC streams, one to each relay)
```

**Handling relay pod restarts / scaling**:
- Edge pods periodically re-resolve the headless DNS (e.g., every 30s) or use gRPC's built-in **DNS resolver with watch** to detect new/removed relay pods.
- On new relay pod: edge pod opens a gRPC stream and re-sends all active SUBSCRIBEs.
- On relay pod death: gRPC stream breaks → edge pod detects, removes it. Kafka rebalances partitions to surviving relays. Edge pod's existing streams to those relays already have subscriptions → no data loss.

**Relay-side logic stays the same**:
```
// Relay pod pseudocode
subscriptions: Map<liveVideoId, Set<edgePodStream>>

onSubscribe(videoId, edgePodStream):
    subscriptions.getOrCreate(videoId).add(edgePodStream)

onKafkaMessage(comment):
    videoId = comment.liveVideoId
    for stream in subscriptions.get(videoId):
        stream.send(comment)
    // If no edge pods subscribed for this videoId → skip (no-op)
```

---

**Option B: Partition-aware routing (more efficient, more complex)**

Edge pod computes `partition = hash(videoId) % 50`, looks up which relay owns that partition (via service discovery / ZooKeeper / config), and connects only to that relay.

```
// Edge pod knows the partition map (fetched from coordination service)
partitionMap: Map<partitionId, relayPodAddress>

onNewViewer(videoId):
    partition = hash(videoId) % 50
    targetRelay = partitionMap.get(partition)
    targetRelay.send(SUBSCRIBE(videoId, edgePodId=self))
```

| Pros | Cons |
|---|---|
| Fewer connections (only connect to the relevant relay) | Must track partition assignments in real time |
| Slightly less overhead | On Kafka rebalance, edge pods must detect the change and re-subscribe to the new relay owner |
| | Adds a coordination service dependency (ZooKeeper / etcd) |

Not worth the complexity when you only have 2–3 relays per region.

---

**Option C: Redis Pub/Sub as intermediary (fully decoupled)**

Remove direct relay → edge pod connections entirely. Each relay publishes to a **Redis Pub/Sub channel** per `liveVideoId`:

```
// Relay pod: on Kafka message
onKafkaMessage(comment):
    redis.publish("live:{comment.liveVideoId}:region:us-east", comment)

// Edge pod: on first viewer for videoId
onNewViewer(videoId):
    redis.subscribe("live:{videoId}:region:us-east")
```

| Pros | Cons |
|---|---|
| Edge pods don't know relay pods exist | Redis becomes a hot-path dependency |
| Zero re-registration on Kafka rebalance | Single Redis node bottleneck for very hot streams (~1M msgs/sec limit per node) |
| Simple subscribe/unsubscribe | Extra network hop (relay → Redis → edge pod) adds ~1–2ms latency |

Good for moderate scale. For 100M viewers, Option A is simpler and avoids the Redis bottleneck.

---

**Trade-off Summary**:

| | Option A: Connect to ALL relays | Option B: Partition-aware routing | Option C: Redis Pub/Sub intermediary |
|---|---|---|---|
| **Connections per edge pod** | 2–3 (all relays) | 1 (only the right relay) | 0 (Redis handles it) |
| **Rebalance handling** | Automatic — already subscribed everywhere | Must detect + re-subscribe to new relay owner | Automatic — relay publishes, edge reads |
| **Extra dependencies** | None | ZooKeeper / etcd for partition map | Redis in hot path |
| **Latency overhead** | None (direct gRPC) | None (direct gRPC) | +1–2 ms (extra Redis hop) |
| **Complexity** | Low | High (partition tracking, re-subscribe logic) | Medium (Redis ops) |
| **Bottleneck risk** | None | None | Redis node for hot streams |
| **Best for** | Small relay count (2–5) | Large relay count (10+) | Moderate scale, simplicity preferred |

**Recommendation**: **Option A** for this design. 2–3 gRPC connections per edge pod is trivial, it's rebalance-safe, and there's no coordination service or Redis in the hot path.

#### 2d. Why Not Simpler Alternatives?

| Approach | Why it doesn't work at 100M scale |
|---|---|
| **Every edge pod consumes from Kafka directly** | 1,000 pods × thousands of streams = millions of Kafka consumers; Kafka consumer groups don't scale to that |
| **Single fan-out service pushes to all 100M clients** | No single machine can hold 100M connections; network bandwidth is ~100 Gbps just for one comment |
| **Redis Pub/Sub alone (all pods subscribe)** | Works at moderate scale (~10K pods), but a single Redis node becomes a bottleneck for 100M messages. Regional scoping helps but still needs the tiered approach for extreme scale |
| **HTTP long-polling instead of WebSocket** | 100M polling clients × every second = 100M HTTP requests/sec; far more overhead than persistent WS connections |

#### 2e. Fan-out Math for One Comment

```
1 comment arrives in Kafka
  → Kafka delivers to ~5 regional relays         (5 messages)
  → Each relay pushes to ~200 edge pods           (1,000 messages total)
  → Each edge pod pushes to ~100K local clients   (100M WebSocket writes total)

Total server-to-server messages:  ~1,005 (trivial)
Total server-to-client messages:  ~100M  (distributed across 1,000 pods)
Per-pod work:                     ~100K ws.send() calls — takes ~100ms with async I/O
```

At 1,000 comments/sec, each edge pod does ~100K × 1,000 = **100M ws.send() calls/sec**. This is too much for a single pod. In practice, for very hot streams the client does **comment sampling** — the edge pod only pushes a subset (e.g., every 10th comment, or the ML-ranked "top" comments) to reduce per-pod fan-out by 10–100×.

#### 2f. Comment Sampling for Extreme Volume

When comment rate × viewer count exceeds a pod's capacity:
- Edge pod switches to **sampled mode**: pushes 1-in-N comments, or only ML-ranked "top" comments.
- Client UI shows "1,000 comments/sec" counter but renders only the sampled subset.
- The full comment stream is still persisted to Cassandra — viewers can scroll back to see all.

### 3. WebSocket Gateway (Edge PoPs)

- Deployed at edge locations close to users.
- Handles: connection lifecycle, auth, heartbeat, reconnection, rate-limiting.
- Rate limits: e.g., 1 comment/sec per user; burst allowance.
- Sticky sessions via consistent hashing on connection ID.

### 4. Comment Service (Write Path)

- Stateless; horizontally scaled behind load balancer.
- Validates input → calls moderation (sync) → publishes to Kafka.
- Returns ACK after Kafka produce confirmation.

### 5. Moderation Service

- **Sync** (< 50 ms): rule-based filters (banned words, spam patterns, user trust score).
- **Async**: deep ML model (toxicity); may hide retroactively.
- **Circuit breaker**: if down, allow-with-flag (don't block posting).

### 6. Redis Cluster (Cache)

- **Recent comments**: Sorted set per `liveVideoId` (score = timestamp), capped at 20 entries — serves the "latest 20" requirement directly.
- **Rate limiting**: Token bucket per user.
- TTL aligned with live window; auto-expire after stream ends + buffer.

---

## Read Path — History Comments and Pagination (Deep Dive)

When a user joins a live stream mid-way, or scrolls back to view older comments, the system must serve historical comments efficiently. This section covers the full read path from API to Cassandra query.

### Read Path Flow

```
Client                    Comment Read Service              Redis                Cassandra
  │                              │                            │                      │
  │── GET /comments?limit=20 ──▶│                            │                      │
  │   (no cursor = latest 20)   │                            │                      │
  │                              │── ZREVRANGE(videoId,0,19) ▶│                      │
  │                              │◀─ 20 comments ────────────│                      │
  │◀── 200 OK + comments ───────│                            │                      │
  │                              │                            │                      │
  │── GET /comments?cursor=X ──▶│  (scrolling back)          │                      │
  │   (cursor = older page)     │                            │                      │
  │                              │── ZREVRANGEBYSCORE? ──────▶│                      │
  │                              │◀─ MISS (outside cache) ───│                      │
  │                              │                            │                      │
  │                              │── scatter-gather query ──────────────────────────▶│
  │                              │◀─ merged + sorted results ──────────────────────│
  │◀── 200 OK + comments ───────│                            │                      │
```

**Two-tier read strategy**:
1. **Latest 20 (most common)** → served from **Redis sorted set** (sub-ms).
2. **Scrolling back (older pages)** → falls back to **Cassandra** (single-digit ms).

### API Details

#### GET /api/v1/live/{liveVideoId}/comments?cursor={cursor}&limit=20

**Request parameters**:

| Parameter | Type | Required | Description |
|---|---|---|---|
| `liveVideoId` | String (path) | Yes | The live stream to fetch comments for |
| `cursor` | String (query) | No | Opaque cursor for pagination. Omit for latest comments. |
| `limit` | Int (query) | No | Number of comments to return (default 20, max 50) |
| `direction` | Enum (query) | No | `older` (default) or `newer` — scroll direction |

**Response (200)**:
```json
{
  "comments": [
    {
      "commentId": "c_abc123",
      "liveVideoId": "lv_xyz",
      "userId": "u_456",
      "userName": "Jane Doe",
      "userAvatar": "https://cdn.fb.com/avatars/u_456.jpg",
      "text": "Great stream!",
      "createdAt": "2026-02-08T10:05:30.123Z",
      "status": "VISIBLE"
    },
    {
      "commentId": "c_abc122",
      "liveVideoId": "lv_xyz",
      "userId": "u_789",
      "userName": "John Smith",
      "userAvatar": "https://cdn.fb.com/avatars/u_789.jpg",
      "text": "Hello everyone!",
      "createdAt": "2026-02-08T10:05:29.456Z",
      "status": "VISIBLE"
    }
  ],
  "nextCursor": "eyJ0cyI6MTcwNzM4NTEyOTQ1NiwiY2lkIjoiY19hYmMxMjAiLCJiIjo1fQ==",
  "hasMore": true
}
```

**Cursor encoding** (base64-encoded JSON — opaque to client):
```json
{
  "ts": 1707385129456,
  "cid": "c_abc120",
  "b": 5
}
```
- `ts` — `createdAt` timestamp of the last returned comment (for Cassandra WHERE clause).
- `cid` — `commentId` of the last returned comment (tie-breaker for same-timestamp comments).
- `b` — current bucket number (so we know which bucket to continue querying).

### Redis — Serving the Latest 20

The persistence service writes every new comment into a Redis sorted set alongside Cassandra:

```
// On new comment (persistence service):
ZADD live:{liveVideoId}:comments {createdAt_ms} {commentJson}
ZREMRANGEBYRANK live:{liveVideoId}:comments 0 -{maxCacheSize+1}
// Keeps only the latest N comments (e.g., N=100 for scroll headroom)
```

**Read latest 20 (no cursor)**:
```
// Comment Read Service:
ZREVRANGE live:{liveVideoId}:comments 0 19
// Returns: 20 most recent comments, sorted newest-first, sub-ms
```

**Read with cursor (still in cache window)**:
```
// If cursor.ts is within the cached window:
ZREVRANGEBYSCORE live:{liveVideoId}:comments {cursor.ts - 1} -inf LIMIT 0 20
// Returns: next 20 comments older than cursor
```

If the cursor falls **outside** the Redis cache window (user scrolled far back), fall through to Cassandra.

### Cassandra — Serving Older Pages (Scatter-Gather)

Recall the schema uses **bucketed partition keys**:
```
PRIMARY KEY ((live_video_id, bucket), created_at, comment_id)
CLUSTERING ORDER BY (created_at DESC, comment_id DESC)
```

**The bucket problem**: Comments are spread across buckets (e.g., bucket 0 = minute 0, bucket 1 = minute 1, ...). A single query can't span buckets. We need **scatter-gather**.

#### Query Strategy

```
// Comment Read Service pseudocode:

function getComments(videoId, cursor, limit=20):

    // 1. Try Redis first (latest window)
    if cursor == null:
        results = redis.ZREVRANGE("live:{videoId}:comments", 0, limit-1)
        if results.size == limit:
            return results + buildCursor(results.last)

    // 2. Redis miss or cursor outside cache → Cassandra scatter-gather
    currentBucket = cursor != null ? cursor.bucket : getCurrentBucket(videoId)
    collected = []

    while collected.size < limit AND currentBucket >= 0:
        // Query one bucket at a time, starting from cursor position
        if cursor != null AND cursor.bucket == currentBucket:
            rows = cassandra.execute("""
                SELECT * FROM live_comments
                WHERE live_video_id = ? AND bucket = ?
                  AND (created_at, comment_id) < (?, ?)
                ORDER BY created_at DESC, comment_id DESC
                LIMIT ?
            """, [videoId, currentBucket, cursor.ts, cursor.cid, limit - collected.size])
        else:
            rows = cassandra.execute("""
                SELECT * FROM live_comments
                WHERE live_video_id = ? AND bucket = ?
                ORDER BY created_at DESC, comment_id DESC
                LIMIT ?
            """, [videoId, currentBucket, limit - collected.size])

        collected.addAll(rows)
        currentBucket -= 1    // move to previous (older) bucket

    nextCursor = buildCursor(collected.last, currentBucket)
    return { comments: collected, nextCursor, hasMore: currentBucket >= 0 }
```

#### Example: User Scrolls Back

Stream started at 10:00 AM. Buckets are per-minute. User joins at 10:30 and scrolls back.

```
Request 1: GET /comments?limit=20           (no cursor)
  → Redis returns latest 20 comments        (10:29:55 – 10:30:00)
  → cursor = { ts: 10:29:55, b: 29 }

Request 2: GET /comments?cursor=...&limit=20  (scroll back)
  → Redis MISS (10:29:55 is outside cached window of last 100)
  → Cassandra: query bucket=29 WHERE created_at < 10:29:55 → gets 8 rows
  → Need 12 more → query bucket=28 LIMIT 12 → gets 12 rows
  → Return 20 comments (10:28:40 – 10:29:54)
  → cursor = { ts: 10:28:40, b: 28 }

Request 3: GET /comments?cursor=...&limit=20  (scroll back more)
  → Cassandra: query bucket=28 WHERE created_at < 10:28:40 → gets 15 rows
  → Need 5 more → query bucket=27 LIMIT 5 → gets 5 rows
  → Return 20 comments
```

#### Optimizing the Scatter-Gather

| Optimization | Detail |
|---|---|
| **Query buckets sequentially, not in parallel** | Start from cursor bucket, move backward. Most requests satisfied in 1–2 buckets. No need to scatter across all buckets. |
| **Bucket size tuning** | 1-minute buckets for hot streams (1K comments/sec = ~60K per bucket = good partition size). 5-minute buckets for normal streams. |
| **Fetch limit + 1** | Fetch `limit + 1` rows. If you get `limit + 1`, there's more data → set `hasMore = true`. Return only `limit` rows. |
| **Filter DELETED in app layer** | Query includes DELETED comments (Cassandra can't efficiently filter). App layer filters them out and fetches more if needed. |
| **Prepared statements** | Pre-compile CQL queries — avoids query parsing overhead on every request. |

### Consistency: Redis vs Cassandra

There's a brief window where Redis and Cassandra may be out of sync (Kafka consumer lag):

```
Kafka → Persistence Service → writes to Cassandra (2–5 ms)
Kafka → Persistence Service → writes to Redis (1–2 ms)
```

Both writes happen from the same consumer. Redis is typically updated first (faster). In rare cases:
- A comment appears in Redis but not yet in Cassandra → user scrolls back, doesn't see it in older pages → acceptable (it appears when they scroll forward again).
- A comment appears in Cassandra but not Redis → user doesn't see it in latest 20 → it appears on next refresh or scroll.

**This is fine for a live comments system** — eventual consistency within milliseconds is acceptable.

### Read Path Capacity

```
100M viewers joining a stream, each fetching latest 20:
  → Thundering herd mitigation: staggered connection + comments served from Redis
  → Redis handles ~1M ops/sec per node → 100M requests spread over ~30s ramp = ~3M/sec
  → 3-node Redis Cluster handles this easily

Scroll-back traffic (much lower — ~1% of users scroll):
  → ~1M scroll requests → Cassandra handles easily with LOCAL_ONE reads
```

---

## Scaling for 100M Concurrent Users

| Challenge | Mitigation |
|---|---|
| 100M WebSocket connections | Distribute across edge PoPs; ~200–1K gateway pods; each handles 100K–500K connections |
| Hot Kafka partition (1 stream) | Single partition handles 1K msgs/sec easily; fan-out is the bottleneck, solved by tiered relay |
| Hot DB partition | Bucketed partition keys in Cassandra (time-bucket suffix) |
| Thundering herd on stream start | Rate-limit connection ramp; staggered reconnects with jitter |
| Late joiners need recent 20 | Serve from Redis sorted set; fallback to Cassandra |
| Cross-region latency | Multi-DC Cassandra; regional Kafka clusters with MirrorMaker; edge PoPs |

### Connection Math

```
100M connections × ~2 KB state each = ~200 GB total RAM
Spread across 1,000 edge pods = ~200 MB per pod (trivial)
Each pod handles ~100K connections
```

### Write Path Math

```
1,000 comments/sec → Kafka → single partition handles easily
Each comment → fan-out to 100M viewers
Tiered: 1 Kafka msg → ~1,000 relay msgs → ~100K edge pushes each
Total network: ~1,000 × 100K = 100M pushes/sec (distributed)
```

---

## Failure Modes and Graceful Degradation

| Failure | Behavior |
|---|---|
| Kafka down | Buffer in gateway (bounded queue); drop oldest if full; alert |
| Redis down | Serve from Cassandra (higher latency for reads) |
| Moderation down | Allow-with-flag; async review catches up |
| DB write failure | Kafka retains events; replay on recovery |
| WebSocket disconnect | Client auto-reconnects with exponential backoff + jitter; fetches missed comments via REST GET |
| Edge pod crash | LB reroutes; clients reconnect to another pod; fetch missed window from cache |

---

## Sequence Diagram — Post Comment

```
Client          Gateway         CommentSvc      Moderation      Kafka       FanOut       Cassandra    Redis
  │                │                │               │             │           │             │           │
  │──POST_COMMENT──▶                │               │             │           │             │           │
  │                │──validate/auth─▶               │             │           │             │           │
  │                │                │──check(sync)──▶             │           │             │           │
  │                │                │◀──APPROVED─────│             │           │             │           │
  │                │                │──publish──────────────────▶  │           │             │           │
  │                │◀───ACK─────────│               │             │           │             │           │
  │◀───ACK─────────│                │               │             │           │             │           │
  │                │                │               │             │──consume──▶             │           │
  │                │                │               │             │           │──broadcast──▶ (viewers)  │
  │                │                │               │             │──consume───────────────▶│           │
  │                │                │               │             │──consume────────────────────────────▶│
  │                │                │               │             │           │             │  (ZADD)   │
```

---

## Extension Points

- **Pinned comments**: Streamer pins; separate field + client-side rendering priority.
- **Slow mode**: Server-enforced per-user cooldown (configurable by streamer).
- **Top comments**: ML-ranked subset pushed instead of firehose for extreme volume.
- **Replay comments**: After stream ends, comments replayed in sync with VOD timeline.
- **Reactions**: Add reaction counters via Redis HINCRBY + periodic flush to durable store.
