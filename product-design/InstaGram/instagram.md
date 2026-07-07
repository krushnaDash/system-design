## Functional Requirements
- Users should be able to create posts featuring photos, videos, and a simple caption.
- Users should be able to follow other users.
- Users should be able to see a chronological feed of posts from the users they follow.

## Out of Scope
- Users should be able to comment on posts.
- Users should be able to like posts.
- Users should be able to share posts.

---

## Non-Functional Requirements (Estimation)

| Metric | Value |
|---|---|
| Daily Active Users (DAU) | 500M |
| Avg posts per user per day | 0.1 (50M new posts/day) |
| Avg follows per user | 200 |
| Avg feed reads per user per day | 10 |
| Feed read QPS | 500M × 10 / 86400 ≈ **~58K reads/sec** |
| Post write QPS | 50M / 86400 ≈ **~580 writes/sec** |
| Avg media size | 2 MB (photos), 50 MB (videos) |
| Storage per day | ~50M × 5 MB avg ≈ **250 TB/day** |
| Read:Write ratio | **~100:1** (read-heavy) |
| Feed latency target | **< 200ms p95** |
| Post creation latency | **< 500ms p95** (excluding upload) |
| Media upload | Resumable, fault-tolerant |
| Availability | **99.99%** |
| Consistency | Eventual consistency acceptable for feed; strong consistency for follow/unfollow |

---

## Core Entities

```
┌──────────────┐        ┌──────────────────┐        ┌──────────────┐
│    User       │        │     Follow        │        │    Post       │
├──────────────┤        ├──────────────────┤        ├──────────────┤
│ user_id (PK) │──1:N──▶│ follower_id (FK) │        │ post_id (PK) │
│ username     │        │ followee_id (FK) │◀──N:1──│ user_id (FK) │
│ display_name │        │ created_at       │        │ caption      │
│ avatar_url   │        │ status           │        │ media_urls[] │
│ bio          │        └──────────────────┘        │ media_type   │
│ created_at   │                                    │ created_at   │
└──────────────┘                                    │ status       │
                                                    └──────────────┘

┌──────────────────┐
│    Media          │
├──────────────────┤
│ media_id (PK)    │
│ post_id (FK)     │
│ url              │
│ type (PHOTO|VID) │
│ width, height    │
│ size_bytes       │
│ created_at       │
└──────────────────┘
```

**Relationships**:
- **User → Post**: 1:N (a user creates many posts)
- **User → Follow → User**: N:M (a user follows many users, a user has many followers)
- **Post → Media**: 1:N (a post can have multiple photos/videos — carousel)

---

## API Design

All APIs are REST. Auth via `Authorization: Bearer <token>` header. Responses use JSON.

### 1. Create Post

```
POST /api/v1/posts
```

**Request Body**:
```json
{
  "caption": "Sunset at the beach",
  "media_ids": ["m_abc123", "m_def456"]
}
```

**Response (201)**:
```json
{
  "post_id": "p_xyz789",
  "user_id": "u_123",
  "caption": "Sunset at the beach",
  "media": [
    {
      "media_id": "m_abc123",
      "url": "https://cdn.instagram.com/media/m_abc123.jpg",
      "type": "PHOTO"
    }
  ],
  "created_at": "2026-02-17T10:00:00Z"
}
```

**Flow**: Client uploads media first (gets `media_ids`), then creates the post referencing them. This decouples upload from post creation.

### 2. Upload Media (Pre-signed URL)

```
POST /api/v1/media/upload
```

**Request Body**:
```json
{
  "file_name": "sunset.jpg",
  "content_type": "image/jpeg",
  "size_bytes": 2048000
}
```

**Response (200)**:
```json
{
  "media_id": "m_abc123",
  "upload_url": "https://upload.cdn.instagram.com/presigned/m_abc123?token=...",
  "expires_at": "2026-02-17T10:15:00Z"
}
```

Client uploads directly to blob storage via the pre-signed URL. This **offloads upload traffic from API servers**.

### 3. Follow / Unfollow

```
POST /api/v1/users/{user_id}/follow
DELETE /api/v1/users/{user_id}/follow
```

**Response (200)**:
```json
{
  "follower_id": "u_123",
  "followee_id": "u_456",
  "status": "FOLLOWING",
  "created_at": "2026-02-17T10:00:00Z"
}
```

### 4. Get Feed

```
GET /api/v1/feed?cursor={cursor}&limit={limit}
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|---|---|---|---|
| `cursor` | String | No | Opaque cursor for pagination. Omit for latest. |
| `limit` | Int | No | Number of posts (default 20, max 50) |

**Response (200)**:
```json
{
  "posts": [
    {
      "post_id": "p_xyz789",
      "user_id": "u_456",
      "username": "jane_doe",
      "avatar_url": "https://cdn.instagram.com/avatars/u_456.jpg",
      "caption": "Sunset at the beach",
      "media": [
        {
          "media_id": "m_abc123",
          "url": "https://cdn.instagram.com/media/m_abc123.jpg",
          "type": "PHOTO",
          "width": 1080,
          "height": 1350
        }
      ],
      "created_at": "2026-02-17T10:00:00Z"
    }
  ],
  "next_cursor": "eyJ0cyI6MTcwNzM4NTEyOTQ1Nn0=",
  "has_more": true
}
```

**Cursor encoding** (base64 JSON, opaque to client):
```json
{ "ts": 1707385129456, "pid": "p_xyz789" }
```
- `ts` — `created_at` of last returned post (for WHERE clause)
- `pid` — `post_id` tie-breaker for same-timestamp posts

### 5. Get User Profile

```
GET /api/v1/users/{user_id}
```

**Response (200)**:
```json
{
  "user_id": "u_456",
  "username": "jane_doe",
  "display_name": "Jane Doe",
  "avatar_url": "https://cdn.instagram.com/avatars/u_456.jpg",
  "bio": "Photographer",
  "post_count": 342,
  "follower_count": 12500,
  "following_count": 180
}
```

### 6. Get User Posts

```
GET /api/v1/users/{user_id}/posts?cursor={cursor}&limit={limit}
```

Same pagination pattern as feed.

---

## High-Level Architecture

```
                                    ┌─────────────┐
                                    │     CDN      │
                                    │ (CloudFront) │
                                    └──────┬──────┘
                                           │ media
┌────────┐     ┌──────────────┐    ┌───────┴──────┐     ┌──────────────┐
│ Client  │───▶│ API Gateway   │───▶│ Post Service  │────▶│ Blob Storage  │
│(iOS/And)│    │ (LB + Auth)  │    │              │     │ (S3)         │
└────────┘    └──────┬───────┘    └──────┬───────┘     └──────────────┘
                      │                   │
                      │                   │ write event
                      │                   ▼
                      │            ┌──────────────┐
                      │            │    Kafka      │
                      │            │ (post-events) │
                      │            └──────┬───────┘
                      │                   │
                      │          ┌────────┴────────┐
                      │          │                  │
                      │          ▼                  ▼
                      │   ┌──────────────┐  ┌──────────────┐
                      │   │ Fan-out       │  │ Post Store    │
                      │   │ Service       │  │ (write-behind)│
                      │   └──────┬───────┘  └──────────────┘
                      │          │
                      │          ▼
                      │   ┌──────────────┐
                      ├──▶│ Feed Service  │◀── reads
                      │   └──────┬───────┘
                      │          │
                      │   ┌──────┴───────┐
                      │   │ Feed Cache    │
                      │   │ (Redis)       │
                      │   └──────────────┘
                      │
                      │   ┌──────────────┐     ┌──────────────┐
                      ├──▶│ User Service  │────▶│ User DB       │
                      │   └──────────────┘     │ (PostgreSQL)  │
                      │                        └──────────────┘
                      │   ┌──────────────┐     ┌──────────────┐
                      └──▶│ Graph Service │────▶│ Follow DB     │
                          │ (follow/      │     │ (PostgreSQL/  │
                          │  unfollow)    │     │  Cassandra)   │
                          └──────────────┘     └──────────────┘
```

---

## Detailed Design — Achieving Functional Requirements

### FR1: Users Should Be Able to Create Posts

#### Write Path

```
Client                 API Gateway        Post Service         S3            Kafka         Posts DB
  │                        │                   │                │               │              │
  │── POST /media/upload ─▶│──────────────────▶│                │               │              │
  │◀── presigned URL ──────│◀─────────────────│                │               │              │
  │                        │                   │                │               │              │
  │── PUT (upload to S3) ──────────────────────────────────────▶│               │              │
  │◀── 200 OK ────────────────────────────────────────────────│               │              │
  │                        │                   │                │               │              │
  │── POST /posts ────────▶│──────────────────▶│                │               │              │
  │                        │                   │── validate ───▶│ (check exists)│              │
  │                        │                   │── publish ─────────────────────▶│              │
  │                        │                   │── write ──────────────────────────────────────▶│
  │◀── 201 Created ────────│◀─────────────────│                │               │              │
```

**Key decisions**:

1. **Pre-signed URL upload**: Client uploads media directly to S3 via pre-signed URL. API servers never handle raw media bytes → reduces API server load and enables resumable uploads.

2. **Post creation is synchronous write**: Post is written to Posts DB (PostgreSQL or DynamoDB) and a `post.created` event is published to Kafka. The API returns 201 immediately.

3. **Kafka event triggers fan-out**: The `post.created` event is consumed asynchronously by the Fan-out Service to populate follower feeds.

#### Posts DB Schema

**Option A: PostgreSQL** (simpler, good for moderate scale)
```sql
CREATE TABLE posts (
    post_id     VARCHAR(64) PRIMARY KEY,    -- Snowflake ID (sortable)
    user_id     VARCHAR(64) NOT NULL,
    caption     TEXT,
    media_type  VARCHAR(20) NOT NULL,       -- PHOTO, VIDEO, CAROUSEL
    status      VARCHAR(20) DEFAULT 'ACTIVE',
    created_at  TIMESTAMP NOT NULL,
    INDEX idx_user_posts (user_id, created_at DESC)
);

CREATE TABLE media (
    media_id    VARCHAR(64) PRIMARY KEY,
    post_id     VARCHAR(64) REFERENCES posts(post_id),
    url         TEXT NOT NULL,
    type        VARCHAR(20) NOT NULL,
    width       INT,
    height      INT,
    size_bytes  BIGINT,
    created_at  TIMESTAMP NOT NULL
);
```

**Option B: DynamoDB** (better for Instagram scale)
```
Table: posts
  Partition Key: user_id
  Sort Key: created_at#post_id
  Attributes: caption, media_type, status, media[]

GSI: post_id-index
  Partition Key: post_id  (for single-post lookup)
```

**Trade-off**: PostgreSQL is simpler for joins and transactions; DynamoDB scales horizontally with no ops overhead. At 500M DAU, DynamoDB or sharded PostgreSQL is needed.

---

### FR2: Users Should Be Able to Follow Other Users

#### Follow/Unfollow Flow

```
Client          API Gateway       Graph Service        Follow DB         Kafka
  │                  │                  │                   │               │
  │── POST /follow ─▶│─────────────────▶│                   │               │
  │                  │                  │── INSERT ─────────▶│               │
  │                  │                  │── publish ─────────────────────────▶│
  │◀── 200 OK ──────│◀────────────────│                   │   (follow.created)
```

#### Follow DB Schema

The follow relationship is a directed graph: `follower → followee`.

**Option A: PostgreSQL**
```sql
CREATE TABLE follows (
    follower_id  VARCHAR(64) NOT NULL,
    followee_id  VARCHAR(64) NOT NULL,
    created_at   TIMESTAMP DEFAULT NOW(),
    status       VARCHAR(20) DEFAULT 'ACTIVE',
    PRIMARY KEY (follower_id, followee_id),
    INDEX idx_followee (followee_id, follower_id)  -- for "who follows me?"
);
```

Two indexes serve two access patterns:
- **PK (follower_id, followee_id)** → "who do I follow?" + "do I follow user X?"
- **Secondary (followee_id, follower_id)** → "who follows me?" (needed for fan-out)

**Option B: Cassandra** (for extreme scale)
```
-- "Who do I follow?"
Table: user_following
  Partition Key: follower_id
  Clustering Key: created_at DESC, followee_id
  Columns: status

-- "Who follows me?" (needed for fan-out)
Table: user_followers
  Partition Key: followee_id
  Clustering Key: created_at DESC, follower_id
  Columns: status
```

**Trade-off**: Two tables (denormalized) in Cassandra for O(1) partition lookups on both access patterns. PostgreSQL uses indexes but may struggle with hot partitions (celebrity users with 100M+ followers).

#### Follower/Following Counts

Maintained as **counters in Redis** (or a separate counters table), updated asynchronously via Kafka `follow.created` / `follow.deleted` events. Not computed on the fly (too expensive at scale).

```
Redis:
  user:{user_id}:follower_count  → INT
  user:{user_id}:following_count → INT
```

---

### FR3: Users Should Be Able to See a Chronological Feed

This is the **hardest problem** in the design. Two fundamental approaches:

#### Approach 1: Fan-out on Write (Push Model) — Recommended for Most Users

When a user creates a post, **push the post_id into every follower's feed cache**.

```
Post Service ──▶ Kafka (post.created) ──▶ Fan-out Service
                                              │
                                              │ for each follower of post author:
                                              │   LPUSH feed:{follower_id} post_id
                                              │   LTRIM feed:{follower_id} 0 799
                                              ▼
                                         Redis (Feed Cache)
                                         ┌─────────────────────────┐
                                         │ feed:u_123 → [p9, p8, p7, p6, ...] │
                                         │ feed:u_456 → [p9, p5, p4, p3, ...] │
                                         └─────────────────────────┘
```

**Fan-out Service pseudocode**:
```
function onPostCreated(event):
    post_id = event.post_id
    author_id = event.user_id
    created_at = event.created_at

    // Get all followers of the author
    followers = graphService.getFollowers(author_id)

    for follower_id in followers:
        // Push post_id into follower's feed (sorted by time)
        redis.ZADD("feed:{follower_id}", created_at, post_id)
        // Trim to keep only latest 800 posts
        redis.ZREMRANGEBYRANK("feed:{follower_id}", 0, -(MAX_FEED_SIZE + 1))
```

**Feed read** (fast — just read from Redis):
```
function getFeed(user_id, cursor, limit=20):
    if cursor == null:
        post_ids = redis.ZREVRANGE("feed:{user_id}", 0, limit - 1)
    else:
        post_ids = redis.ZREVRANGEBYSCORE("feed:{user_id}", cursor.ts - 1, "-inf", LIMIT, 0, limit)

    // Hydrate post_ids with full post data (batch lookup)
    posts = postService.batchGet(post_ids)

    // Enrich with user info (batch lookup, cached)
    enriched = enrichWithUserInfo(posts)

    return { posts: enriched, next_cursor: buildCursor(posts.last) }
```

**Pros**: Feed reads are O(1) from Redis — sub-ms latency. Perfect for the 100:1 read-heavy ratio.

**Cons**: Fan-out is expensive for celebrity users (100M followers = 100M Redis writes per post).

#### Approach 2: Fan-out on Read (Pull Model) — For Celebrity Users

For users with >500K followers ("celebrities"), **don't fan out on write**. Instead, merge their posts at read time.

```
function getFeed(user_id, cursor, limit=20):
    // 1. Get pre-computed feed from Redis (posts from non-celebrity followees)
    cached_posts = redis.ZREVRANGEBYSCORE("feed:{user_id}", ...)

    // 2. Get celebrity followees
    celebrity_followees = graphService.getCelebrityFollowees(user_id)

    // 3. Fetch recent posts from each celebrity (cached in Redis per-user timeline)
    celebrity_posts = []
    for celeb_id in celebrity_followees:
        recent = redis.ZREVRANGEBYSCORE("user_posts:{celeb_id}", ...)
        celebrity_posts.addAll(recent)

    // 4. Merge and sort by created_at DESC
    merged = merge_sorted(cached_posts, celebrity_posts)
    return merged[:limit]
```

#### Hybrid Approach (Recommended)

| User Type | Followers | Fan-out Strategy |
|---|---|---|
| **Normal user** | < 500K | Fan-out on write (push to all follower feeds) |
| **Celebrity** | ≥ 500K | Fan-out on read (merge at read time) |

**Threshold** (500K) is configurable. This is what Instagram/Twitter actually use.

#### Feed Cache Structure (Redis)

```
// Per-user feed (populated by fan-out on write)
Key: feed:{user_id}
Type: Sorted Set
Score: created_at (epoch ms)
Member: post_id
Max size: 800 entries (ZREMRANGEBYRANK to trim)

// Per-user timeline (for celebrity pull model)
Key: user_posts:{user_id}
Type: Sorted Set
Score: created_at (epoch ms)
Member: post_id
Max size: 100 entries
```

#### Feed Generation — End-to-End Flow

```
User opens app
      │
      ▼
GET /api/v1/feed?limit=20
      │
      ▼
Feed Service
      │
      ├── 1. ZREVRANGE feed:{user_id} 0 19          ← Redis (pre-computed, sub-ms)
      │
      ├── 2. Get celebrity followees                  ← Graph Service (cached)
      │
      ├── 3. ZREVRANGE user_posts:{celeb_id} 0 4     ← Redis (per celebrity, sub-ms)
      │       (for each celebrity followee)
      │
      ├── 4. Merge + sort by created_at DESC
      │
      ├── 5. Take top 20 post_ids
      │
      ├── 6. Batch GET post details                   ← Post Service (cached in Redis)
      │
      ├── 7. Batch GET user info                      ← User Service (cached in Redis)
      │
      └── 8. Return enriched feed
```

**Latency breakdown**:
| Step | Latency |
|---|---|
| Redis ZREVRANGE (feed) | ~1 ms |
| Redis ZREVRANGE (celebrity posts, 5 celebs) | ~2 ms |
| Merge + sort | ~1 ms |
| Batch GET posts (Redis cache hit) | ~3 ms |
| Batch GET users (Redis cache hit) | ~2 ms |
| **Total** | **~10 ms** (well under 200ms p95) |

---

## Database Choices Summary

| Component | Database | Why |
|---|---|---|
| **Users** | PostgreSQL | Relational data, strong consistency for profile updates, moderate scale |
| **Posts** | DynamoDB (or sharded Postgres) | High write throughput, partition by user_id, horizontal scaling |
| **Follows** | Cassandra (or sharded Postgres) | Massive N:M relationship, two access patterns, write-heavy on follow/unfollow |
| **Feed Cache** | Redis Cluster | Sub-ms reads, sorted sets for chronological feed, TTL for inactive users |
| **Media** | S3 + CloudFront CDN | Blob storage for photos/videos, CDN for global low-latency delivery |
| **Counters** | Redis | Follower/following/post counts, atomic increments |
| **Events** | Kafka | Decouple write path from fan-out, event retention for replay |

---

## Non-Functional Requirements — Deep Dive

### Scalability

**Read path (feed)**:
```
58K reads/sec → Redis Cluster handles ~1M ops/sec per node
  → 6-node Redis Cluster handles this with headroom
  → Horizontal scaling: add nodes as DAU grows
```

**Write path (post creation)**:
```
580 posts/sec → trivial for any DB
Fan-out: 580 posts/sec × 200 avg followers = 116K Redis writes/sec
  → Well within Redis Cluster capacity
Celebrity fan-out avoided by pull model
```

**Fan-out for celebrity posts** (worst case):
```
Celebrity with 100M followers posts once:
  Push model: 100M Redis writes → takes ~100 seconds at 1M ops/sec → TOO SLOW
  Pull model: 0 writes on post. Merge at read time for each reader → O(C) where C = celebrity followees (~5-10)
```

### Availability (99.99%)

| Component | Strategy |
|---|---|
| **API Gateway** | Multi-AZ, auto-scaling, health checks |
| **Services** | Stateless, horizontally scaled, Kubernetes with rolling deploys |
| **PostgreSQL** | Multi-AZ RDS, read replicas, automated failover |
| **DynamoDB** | Managed, multi-AZ by default, on-demand scaling |
| **Cassandra** | Multi-DC replication, RF=3, LOCAL_QUORUM reads/writes |
| **Redis** | Redis Cluster with replicas, automatic failover |
| **S3** | 99.999999999% durability, cross-region replication |
| **Kafka** | Multi-broker, RF=3, ISR-based leader election |

### Consistency

| Operation | Consistency | Rationale |
|---|---|---|
| **Post creation** | Strong (write-read-your-own) | User should see their own post immediately |
| **Follow/Unfollow** | Strong | User expects immediate effect |
| **Feed** | Eventual (seconds) | Acceptable lag for new posts appearing in follower feeds |
| **Counters** | Eventual (seconds) | Follower/post counts can lag briefly |
| **Media upload** | Eventual (CDN propagation) | CDN caches propagate in seconds |

### Media Storage & Delivery

```
Upload: Client → Pre-signed URL → S3 (original)
                                     │
                                     ▼
                              Media Processing Worker
                              (triggered by S3 event)
                                     │
                              ┌──────┴──────┐
                              │ Generate     │
                              │ thumbnails   │
                              │ + transcode  │
                              │ video        │
                              └──────┬──────┘
                                     │
                                     ▼
                              S3 (multiple resolutions)
                                     │
                                     ▼
                              CloudFront CDN → Client
```

**Resolutions generated**:
- Thumbnail: 150×150
- Feed: 640×640
- Full: 1080×1350
- Video: 720p, 1080p (adaptive bitrate)

### Rate Limiting

| Endpoint | Limit | Window |
|---|---|---|
| POST /posts | 10 | per hour |
| POST /media/upload | 20 | per hour |
| POST /follow | 100 | per day |
| GET /feed | 300 | per minute |

Implemented via Redis sliding window counter: `rate:{user_id}:{endpoint}:{window}`

### Monitoring & SLOs

| SLO | Target |
|---|---|
| Feed read latency p95 | < 200ms |
| Feed read latency p99 | < 500ms |
| Post creation latency p95 | < 500ms |
| Feed freshness (time from post to appearing in follower feed) | < 5 seconds |
| Media upload success rate | > 99.9% |
| API availability | > 99.99% |

**Key metrics to monitor**:
- Kafka consumer lag (fan-out delay)
- Redis memory usage and eviction rate
- Feed cache hit rate
- Fan-out latency per post (p50, p95, p99)
- CDN cache hit ratio

---

## Failure Modes & Mitigations

| Failure | Impact | Mitigation |
|---|---|---|
| **Redis feed cache down** | Feed reads fail | Fall back to on-demand pull from Posts DB; Redis Cluster auto-failover |
| **Kafka down** | Fan-out stops; new posts don't appear in feeds | Posts still written to DB; fan-out replays from Kafka on recovery |
| **Fan-out Service crash** | Feed staleness increases | Kafka retains events; consumer restarts from last committed offset |
| **S3 down** | Media upload fails | Retry with exponential backoff; multi-region S3 replication |
| **Celebrity posts storm** | Spike in pull-model reads | Celebrity post timelines cached in Redis; CDN caches API responses |
| **Thundering herd (viral post)** | Spike in post detail lookups | Post data cached in Redis with TTL; request coalescing |

---

## Extension Points (Future)

| Feature | How It Fits |
|---|---|
| **Likes/Comments** | Separate service + Kafka events; counters in Redis; append to post detail |
| **Stories** | Separate ephemeral store with 24h TTL; different feed pipeline |
| **Explore/Discover** | ML ranking service; content-based + collaborative filtering |
| **Notifications** | Kafka consumer for follow/like/comment events → push notification service |
| **Direct Messages** | Separate real-time messaging system (WebSocket-based) |
| **Ranked Feed** | Replace chronological sort with ML-ranked scoring; keep same fan-out infra |
