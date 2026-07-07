# Design CamelCamelCamel — Amazon Price Tracker & Alert System

Reference: https://camelcamelcamel.com/

A third-party website for users to:
1. Get products' historical prices on Amazon
2. Subscribe to email/phone alerts for price drops of a certain product

---

## Functional Requirements
- Users should be able to search and view any Amazon product's **price history** over time.
- Users should be able to **subscribe to price drop notifications** (email/phone) for a specific product.
- The system should **periodically scrape/fetch Amazon product prices** and store the history.
- The system should **detect price drops and trigger alerts** to subscribed users.

## Out of Scope
- Purchasing products (redirect to Amazon).
- Price comparison across multiple retailers (Amazon only).
- Browser extension functionality.

---

## Non-Functional Requirements (Estimation)

| Metric | Value |
|---|---|
| Total users | 100M |
| Active users | ~10M |
| Peak QPS (price history reads) | **50K QPS** |
| Regular QPS | **10K QPS** |
| Alerts per day | **20K alerts/day** |
| Products tracked | ~100M Amazon products |
| Price scrape frequency | Every 1–6 hours (configurable per product popularity) |
| Price history read latency | **< 200ms p95** |
| Alert delivery latency | **< 5 minutes** from price drop detection |
| Availability | **99.9%** |
| Consistency | Eventual consistency acceptable for price data; strong for notification subscriptions |

---

## Core Entities

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│    Product        │       │  PriceHistory     │       │   Notification    │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ product_id (PK)  │──1:N─▶│ product_id (FK)  │       │ notification_id  │
│ amazon_url       │       │ price            │       │ product_id (FK)  │
│ name             │       │ currency         │       │ user_id (FK)     │
│ metadata         │       │ recorded_at      │       │ target_price     │
│   - seo_url      │       └──────────────────┘       │ channel (email/  │
│   - image_url    │                                   │          phone)  │
│   - category     │                                   │ status (ACTIVE/  │
│   - size         │                                   │   PAUSED/FIRED)  │
│ current_price    │       ┌──────────────────┐       │ created_at       │
│ last_scraped_at  │       │     User          │       └──────────────────┘
└──────────────────┘       ├──────────────────┤
                           │ user_id (PK)     │
                           │ email            │
                           │ phone            │
                           │ created_at       │
                           └──────────────────┘
```

**Relationships**:
- **Product → PriceHistory**: 1:N (one product has many price data points over time)
- **User → Notification**: 1:N (a user can subscribe to alerts for many products)
- **Product → Notification**: 1:N (a product can have many subscribers)

---

## API Design

All APIs are REST. Auth via `Authorization: Bearer <token>` header.

### 1. Get Price History

```
GET /api/v1/price/{product_id}?startTime={startTime}&endTime={endTime}&pageSize={pageSize}&cursor={cursor}
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|---|---|---|---|
| `product_id` | String (path) | Yes | Amazon product ID (ASIN) |
| `startTime` | ISO 8601 | No | Start of time range (default: 30 days ago) |
| `endTime` | ISO 8601 | No | End of time range (default: now) |
| `pageSize` | Int | No | Number of data points (default 100, max 500) |
| `cursor` | String | No | Opaque cursor for pagination |

**Response (200)**:
```json
{
  "product": {
    "product_id": "B09V3KXJPB",
    "name": "Apple AirPods Pro (2nd Gen)",
    "amazon_url": "https://amazon.com/dp/B09V3KXJPB",
    "image_url": "https://cdn.camelcamelcamel.com/products/B09V3KXJPB.jpg",
    "current_price": 189.99,
    "currency": "USD",
    "last_scraped_at": "2026-02-17T10:00:00Z"
  },
  "price_history": [
    { "price": 249.99, "recorded_at": "2026-01-01T00:00:00Z" },
    { "price": 199.99, "recorded_at": "2026-01-15T00:00:00Z" },
    { "price": 189.99, "recorded_at": "2026-02-10T00:00:00Z" }
  ],
  "stats": {
    "highest": 249.99,
    "lowest": 169.99,
    "average": 209.99
  },
  "next_cursor": "eyJ0cyI6MTcwNzM4NTEyOTQ1Nn0=",
  "has_more": true
}
```

### 2. Subscribe to Price Drop Notification

```
POST /api/v1/notifications
```

**Request Body**:
```json
{
  "product_id": "B09V3KXJPB",
  "target_price": 179.99,
  "channel": "email",
  "email": "user@example.com",
  "phone": "+1234567890"
}
```

**Response (201)**:
```json
{
  "notification_id": "n_abc123",
  "product_id": "B09V3KXJPB",
  "target_price": 179.99,
  "channel": "email",
  "status": "ACTIVE",
  "created_at": "2026-02-17T10:00:00Z"
}
```

### 3. Get User Notifications

```
GET /api/v1/notifications?status={status}&pageSize={pageSize}&cursor={cursor}
```

**Response (200)**:
```json
{
  "notifications": [
    {
      "notification_id": "n_abc123",
      "product_id": "B09V3KXJPB",
      "product_name": "Apple AirPods Pro (2nd Gen)",
      "current_price": 189.99,
      "target_price": 179.99,
      "channel": "email",
      "status": "ACTIVE",
      "created_at": "2026-02-17T10:00:00Z"
    }
  ],
  "next_cursor": "...",
  "has_more": false
}
```

### 4. Delete / Pause Notification

```
DELETE /api/v1/notifications/{notification_id}
PATCH  /api/v1/notifications/{notification_id}   { "status": "PAUSED" }
```

### 5. Search Product (by Amazon URL or keyword)

```
GET /api/v1/products/search?q={amazon_url_or_keyword}
```

**Response (200)**:
```json
{
  "products": [
    {
      "product_id": "B09V3KXJPB",
      "name": "Apple AirPods Pro (2nd Gen)",
      "current_price": 189.99,
      "image_url": "https://cdn.camelcamelcamel.com/products/B09V3KXJPB.jpg"
    }
  ]
}
```

---

## High-Level Architecture

```
                                                    ┌──────────────┐
                                                    │   Amazon      │
                                                    │  (source)     │
                                                    └──────┬───────┘
                                                           │
                                                           ▼
                                                    ┌──────────────┐
                                                    │ Web Scraper / │
                                                    │ Price Crawler  │
                                                    │ (scheduled)    │
                                                    └──────┬───────┘
                                                           │
                                                           ▼
                                                    ┌──────────────────┐
                                                    │ Kafka Topic       │
                                                    │ (product_id,      │
                                                    │  price)           │
                                                    └───┬──────────┬──┘
                                                        │          │
                                              ┌─────────┘          └─────────┐
                                              ▼                              ▼
┌────────┐    ┌──────────┐    ┌──────────────────┐                ┌──────────────────┐
│ User   │───▶│ Gateway   │───▶│ Product Price    │                │ Notification      │
│        │    │ (LB)     │    │ History Service  │                │ Processor         │
└────────┘    └──────┬───┘    └───────┬──────────┘                │ (price drop       │
                     │                │                            │  detection)       │
                     │                │ read                       └────────┬──────────┘
                     │                ▼                                     │
                     │         ┌──────────────┐                            │ detected
                     │         │ Redis Cache   │                            │ price drop
                     │         │ (hot products)│                            ▼
                     │         └──────┬───────┘                     ┌──────────────────┐
                     │                │ miss                        │ Notification      │
                     │                ▼                             │ Service           │
                     │         ┌──────────────┐                    └────────┬──────────┘
                     │         │ NoSQL DB      │                            │
                     │         │ Cassandra     │                            │ read subscriptions
                     │         │ (product_id   │                            ▼
                     │         │  partition)   │                     ┌──────────────────┐
                     │         └──────────────┘                     │ Notification DB   │
                     │                                              │ PostgreSQL        │
                     │                                              └──────────────────┘
                     │         ┌──────────────┐                            │
                     └────────▶│ Notification  │                            │ send alert
                               │ Service       │◀───────────────────────────┘
                               │ (subscribe)   │────▶ Email / SMS Gateway
                               └──────────────┘
```

### Component Summary

| Component | Responsibility |
|---|---|
| **Web Scraper / Price Crawler** | Periodically fetches product prices from Amazon; publishes to Kafka |
| **Kafka** | Decouples scraping from storage and notification processing; topic keyed by `product_id` |
| **Product Price History Service** | Serves price history reads; reads from Redis cache → Cassandra fallback |
| **Redis Cache** | Caches hot product price data (recent history, current price) |
| **Cassandra (NoSQL DB)** | Durable store for all price history; partitioned by `product_id` |
| **Notification Processor** | Kafka consumer that detects price drops by comparing new price vs previous; triggers alerts |
| **Notification Service** | Manages subscriptions (CRUD); sends email/SMS alerts via external gateways |
| **Notification DB (PostgreSQL)** | Stores notification subscriptions, user data |
| **CDC (Change Data Capture)** | Streams price changes from Cassandra to Kafka for notification processing |
| **API Gateway** | Load balancing, auth, rate limiting |

---

## Detailed Design

### 1. Price Scraping Pipeline (Amazon → Storage)

#### Web Scraper / Price Crawler

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Scheduler     │────▶│ Scraper Pool  │────▶│ Amazon       │────▶│ Kafka        │
│ (priority     │     │ (distributed  │     │ Product Page │     │ (product_id, │
│  queue)       │     │  workers)     │     │              │     │  price)      │
└──────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                       │
                                                              ┌────────┴────────┐
                                                              ▼                  ▼
                                                       ┌──────────┐      ┌──────────────┐
                                                       │ Price     │      │ Notification  │
                                                       │ Writer    │      │ Processor     │
                                                       │ Consumer  │      │ Consumer      │
                                                       └────┬─────┘      └──────────────┘
                                                            │
                                                     ┌──────┴──────┐
                                                     ▼              ▼
                                              ┌──────────┐   ┌──────────┐
                                              │ Cassandra │   │ Redis    │
                                              │ (durable) │   │ (cache)  │
                                              └──────────┘   └──────────┘
```

**Scraping strategy**:

| Product Tier | Scrape Frequency | Criteria |
|---|---|---|
| **Hot** (many subscribers) | Every 1 hour | > 100 active notifications |
| **Warm** (some subscribers) | Every 6 hours | 1–100 active notifications |
| **Cold** (no subscribers) | Every 24 hours | 0 notifications, but tracked |
| **On-demand** | Immediate | User searches a new product |

**Scraper pseudocode**:
```
function scrapeProduct(product_id):
    // 1. Fetch Amazon product page
    page = httpClient.get("https://amazon.com/dp/{product_id}", headers=rotateUserAgent())

    // 2. Parse price from HTML (or use Amazon Product API if available)
    price = parser.extractPrice(page)
    metadata = parser.extractMetadata(page)  // name, image, category, size

    // 3. Publish to Kafka
    kafka.publish("product.price", key=product_id, value={
        product_id: product_id,
        price: price,
        currency: "USD",
        scraped_at: now(),
        metadata: metadata
    })
```

**Anti-scraping mitigations**:
- Rotate IP addresses (proxy pool)
- Rotate User-Agent headers
- Respect rate limits with backoff
- Use Amazon Product Advertising API where possible (preferred, but rate-limited)
- Distribute scraping across time windows to avoid bursts

#### Price Writer Consumer (Kafka → Cassandra + Redis)

```
function onPriceEvent(event):
    product_id = event.product_id
    price = event.price
    scraped_at = event.scraped_at

    // 1. Write to Cassandra (durable history)
    cassandra.execute("""
        INSERT INTO price_history (product_id, recorded_at, price, currency)
        VALUES (?, ?, ?, ?)
    """, [product_id, scraped_at, price, event.currency])

    // 2. Update current price in Cassandra
    cassandra.execute("""
        UPDATE products SET current_price = ?, last_scraped_at = ? WHERE product_id = ?
    """, [price, scraped_at, product_id])

    // 3. Update Redis cache
    redis.HSET("product:{product_id}", "current_price", price, "last_scraped_at", scraped_at)
    redis.ZADD("price_history:{product_id}", scraped_at_ms, json({price, scraped_at}))
    redis.ZREMRANGEBYRANK("price_history:{product_id}", 0, -(MAX_CACHE_SIZE + 1))
    redis.EXPIRE("price_history:{product_id}", 86400 * 7)  // 7-day TTL for cache
```

---

### 2. Price History Read Path

```
Client                  Product Price History Service         Redis              Cassandra
  │                              │                              │                    │
  │── GET /price/{id} ─────────▶│                              │                    │
  │   ?startTime&endTime        │                              │                    │
  │                              │── HGET product:{id} ────────▶│                    │
  │                              │◀─ current_price ────────────│                    │
  │                              │                              │                    │
  │                              │── ZREVRANGEBYSCORE ─────────▶│                    │
  │                              │   price_history:{id}        │                    │
  │                              │   startTime..endTime        │                    │
  │                              │◀─ cached history ───────────│                    │
  │                              │                              │                    │
  │                              │   (if cache miss or partial) │                    │
  │                              │── SELECT FROM price_history ─────────────────────▶│
  │                              │   WHERE product_id = ?       │                    │
  │                              │   AND recorded_at >= ?       │                    │
  │                              │   AND recorded_at <= ?       │                    │
  │                              │◀─ full history ─────────────────────────────────│
  │                              │                              │                    │
  │◀── 200 OK + history ───────│                              │                    │
```

#### Cassandra Schema

```sql
-- Product metadata
CREATE TABLE products (
    product_id      TEXT PRIMARY KEY,
    name            TEXT,
    amazon_url      TEXT,
    image_url       TEXT,
    category        TEXT,
    size            TEXT,
    current_price   DECIMAL,
    currency        TEXT,
    last_scraped_at TIMESTAMP
);

-- Price history (time-series, partitioned by product)
CREATE TABLE price_history (
    product_id  TEXT,
    recorded_at TIMESTAMP,
    price       DECIMAL,
    currency    TEXT,
    PRIMARY KEY (product_id, recorded_at)
) WITH CLUSTERING ORDER BY (recorded_at DESC);
```

**Why Cassandra?**
- **Write-optimized**: High-throughput writes from scraper (100M products × multiple scrapes/day)
- **Time-series natural fit**: Partition by `product_id`, cluster by `recorded_at DESC` — perfect for "give me price history for product X between date A and B"
- **Horizontal scaling**: Add nodes as product catalog grows
- **Read complexity**: O(1) partition lookup + O(K) scan where K = data points in time range

**Partition sizing**:
```
100M products × 4 scrapes/day avg × 365 days × 20 bytes/row ≈ 2.9 TB/year
Per-product partition: 4 × 365 = 1,460 rows/year → small, well within Cassandra limits
After 5 years: ~7,300 rows per product → still fine (no bucketing needed)
```

#### Redis Cache Structure

```
// Current product info (hash)
Key: product:{product_id}
Type: Hash
Fields: current_price, name, image_url, last_scraped_at
TTL: 24 hours (refreshed on every scrape)

// Recent price history (sorted set)
Key: price_history:{product_id}
Type: Sorted Set
Score: recorded_at (epoch ms)
Member: JSON {price, recorded_at}
Max size: 500 entries (~3 months of hourly data)
TTL: 7 days (for hot products, refreshed on access)
```

**Cache strategy**: Cache-aside with TTL. Hot products (frequently viewed) stay cached. Cold products evict naturally.

---

### 3. Notification System (Price Drop Detection & Alerting)

This is the core value proposition — alerting users when prices drop below their target.

#### Price Drop Detection Flow

```
Kafka (product.price)
        │
        ▼
┌──────────────────────┐
│ Notification          │
│ Processor             │
│ (Kafka Consumer)      │
│                       │
│ 1. Read new price     │
│ 2. Read previous      │
│    price from Redis   │
│ 3. If price dropped:  │
│    query subscribers  │
│    from Notification  │
│    DB                 │
│ 4. For each subscriber│
│    where new_price <= │
│    target_price:      │
│    send alert         │
└───────────┬──────────┘
            │
            ▼
┌──────────────────────┐     ┌──────────────────┐
│ Notification Service  │────▶│ Email Gateway     │
│                       │     │ (SendGrid/SES)   │
│                       │────▶│ SMS Gateway       │
│                       │     │ (Twilio)          │
└──────────────────────┘     └──────────────────┘
```

#### Notification Processor Pseudocode

```
function onPriceEvent(event):
    product_id = event.product_id
    new_price = event.price

    // 1. Get previous price
    previous_price = redis.HGET("product:{product_id}", "current_price")

    // 2. Check if price dropped
    if previous_price == null OR new_price >= previous_price:
        return  // no drop, skip

    // 3. Price dropped! Find subscribers whose target is met
    subscribers = notificationDB.query("""
        SELECT * FROM notifications
        WHERE product_id = ? AND status = 'ACTIVE' AND target_price >= ?
    """, [product_id, new_price])

    // 4. Send alerts
    for sub in subscribers:
        if sub.channel == "email":
            emailGateway.send(
                to: sub.email,
                subject: "Price Drop Alert: {product_name}",
                body: "The price of {product_name} dropped to ${new_price} (was ${previous_price}). Your target was ${sub.target_price}."
            )
        elif sub.channel == "phone":
            smsGateway.send(to: sub.phone, message: "...")

        // 5. Mark notification as fired (or keep active for future drops)
        notificationDB.update("""
            UPDATE notifications SET status = 'FIRED', fired_at = NOW()
            WHERE notification_id = ?
        """, [sub.notification_id])
```

#### Notification DB Schema (PostgreSQL)

```sql
CREATE TABLE users (
    user_id     UUID PRIMARY KEY,
    email       VARCHAR(255),
    phone       VARCHAR(50),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY,
    product_id      VARCHAR(64) NOT NULL,
    user_id         UUID NOT NULL REFERENCES users(user_id),
    target_price    DECIMAL NOT NULL,
    channel         VARCHAR(20) NOT NULL,  -- 'email' | 'phone'
    status          VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE | PAUSED | FIRED | DELETED
    created_at      TIMESTAMP DEFAULT NOW(),
    fired_at        TIMESTAMP,
    INDEX idx_product_active (product_id, status, target_price),
    INDEX idx_user (user_id, status)
);
```

**Why PostgreSQL for notifications?**
- Strong consistency needed (user subscribes → must be immediately queryable)
- Relational queries: "find all ACTIVE notifications for product X where target_price >= new_price"
- Moderate scale: 20K alerts/day is trivial for PostgreSQL
- ACID transactions for status updates

#### CDC Alternative (from screenshot)

The screenshot shows a **CDC (Change Data Capture)** path from Cassandra → Kafka. This is an alternative to the direct Kafka consumer approach:

```
Scraper → Cassandra (write price) → CDC → Kafka → Notification Processor
```

**Trade-off**:
| Approach | Pros | Cons |
|---|---|---|
| **Direct Kafka** (recommended) | Simpler; scraper publishes to Kafka, both writer and notification processor consume | Dual-write concern if scraper fails after Kafka but before Cassandra |
| **CDC from Cassandra** | Single source of truth (Cassandra); no dual-write | Added complexity (CDC infrastructure); higher latency for notifications |

We use **Direct Kafka** (scraper → Kafka → both consumers) as the primary approach, matching the screenshot's architecture.

---

### 4. Alert Delivery Guarantees

| Concern | Solution |
|---|---|
| **At-least-once delivery** | Kafka consumer commits offset only after alert is sent; idempotent sends via dedup key `(notification_id, price, scraped_at)` |
| **Alert deduplication** | Store `last_alerted_price` per notification; don't re-alert for same price |
| **Email/SMS failure** | Retry with exponential backoff; dead-letter queue for persistent failures |
| **Batch alerts** | If a user has 50 notifications that fire simultaneously, batch into a single email digest |
| **Rate limiting** | Max 1 alert per product per user per 24 hours (avoid spam from price fluctuations) |

---

## Database Choices Summary

| Component | Database | Why |
|---|---|---|
| **Product metadata** | Cassandra | Co-located with price history; partition by product_id |
| **Price history** | Cassandra | Time-series data; write-heavy from scraper; partition by product_id, cluster by recorded_at |
| **Users & Notifications** | PostgreSQL | Strong consistency; relational queries for subscription management |
| **Price cache** | Redis | Sub-ms reads for hot products; current price + recent history |
| **Event streaming** | Kafka | Decouple scraper from storage and notification processing |

---

## Non-Functional Requirements — Deep Dive

### Scalability

**Read path (price history)**:
```
Peak 50K QPS → Redis serves hot products (~80% cache hit rate)
  → 50K × 0.8 = 40K served from Redis (trivial for Redis Cluster)
  → 50K × 0.2 = 10K Cassandra reads (trivial for Cassandra)
```

**Write path (scraping)**:
```
100M products / 6 hours avg = ~4,600 writes/sec to Cassandra
  → Cassandra handles 10K+ writes/sec per node easily
  → 3-node cluster with RF=3 handles this with headroom
```

**Notification processing**:
```
20K alerts/day = ~0.23 alerts/sec → trivial
Burst: popular product drops → 10K notifications in minutes
  → Kafka consumer scales horizontally
  → Email gateway rate limit: batch + queue
```

### Scraper Scaling

```
100M products to scrape:
  Hot (1hr):    100K products × 24 scrapes/day = 2.4M scrapes/day
  Warm (6hr):   10M products × 4 scrapes/day  = 40M scrapes/day
  Cold (24hr):  90M products × 1 scrape/day   = 90M scrapes/day
  Total: ~132M scrapes/day = ~1,528 scrapes/sec

  At 2 seconds per scrape (with rate limiting):
  → Need ~3,000 concurrent scraper workers
  → Distributed across multiple IPs/proxies
```

### Availability (99.9%)

| Component | Strategy |
|---|---|
| **API Gateway** | Multi-AZ, auto-scaling |
| **Services** | Stateless, Kubernetes, rolling deploys |
| **Cassandra** | RF=3, multi-DC, LOCAL_QUORUM |
| **PostgreSQL** | Multi-AZ RDS, read replicas |
| **Redis** | Redis Cluster with replicas |
| **Kafka** | RF=3, ISR-based leader election |
| **Scraper** | Distributed workers; missed scrape retried next cycle |

### Consistency

| Operation | Consistency | Rationale |
|---|---|---|
| **Price write** | Eventual | Scraper writes asynchronously; brief lag acceptable |
| **Price read** | Eventual | Cache may be slightly stale; acceptable for price history |
| **Notification subscribe** | Strong | User expects immediate confirmation |
| **Alert delivery** | At-least-once | Better to send duplicate alert than miss one |

---

## Failure Modes & Mitigations

| Failure | Impact | Mitigation |
|---|---|---|
| **Amazon blocks scraper** | Price data goes stale | Rotate IPs/proxies; use Amazon API as fallback; alert ops team |
| **Kafka down** | New prices not processed | Scraper retries; prices buffered locally; Kafka multi-broker HA |
| **Cassandra down** | Price history reads fail | Redis cache serves recent data; Cassandra multi-DC failover |
| **Redis down** | Increased latency on reads | Fall back to Cassandra directly; Redis Cluster auto-failover |
| **Email gateway down** | Alerts not delivered | Retry queue with exponential backoff; dead-letter for manual review |
| **Notification Processor crash** | Price drops missed | Kafka retains events; consumer restarts from last committed offset |
| **Scraper worker crash** | Some products not scraped on time | Scheduler reassigns to other workers; next cycle catches up |

---

## Monitoring & SLOs

| SLO | Target |
|---|---|
| Price history read latency p95 | < 200ms |
| Price freshness (time since last scrape) | < 6 hours for warm products |
| Alert delivery latency (price drop → email sent) | < 5 minutes |
| Alert delivery success rate | > 99.5% |
| Scraper success rate | > 95% (Amazon may block some requests) |
| API availability | > 99.9% |

**Key metrics**:
- Scrape success/failure rate per product tier
- Kafka consumer lag (notification processor)
- Redis cache hit rate
- Alert delivery latency distribution
- Price staleness distribution across products
- Amazon API/scrape rate limit errors

---

## Extension Points (Future)

| Feature | How It Fits |
|---|---|
| **Browser extension** | Inject price history chart on Amazon product pages; calls same API |
| **Multi-retailer** | Add scraper modules for Walmart, BestBuy, etc.; same Kafka pipeline |
| **Price prediction** | ML model on price history; "likely to drop in next 2 weeks" |
| **Wishlist integration** | Import Amazon wishlist; auto-create notifications for all items |
| **Price comparison** | Cross-retailer comparison view; aggregate from multiple scraper sources |
| **Webhook notifications** | In addition to email/SMS, allow webhook callbacks for power users |
