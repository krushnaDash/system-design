# Order Aggregator - Requirements

## Overview
**Flow**: Customer → B2C OMS → **Aggregator** → B2B OMS → Vendors (Apple, Samsung, LG, Google)  
Aggregates orders by **time** (configurable windows) and **quantity** (thresholds per vendor/item). Max latency: 30s.

## Functional Requirements
- Ingest orders via API/Kafka, validate, ensure idempotency
- Aggregate by time windows OR quantity thresholds (whichever triggers first)
- Route aggregated orders to B2B OMS with vendor mapping
- Track B2C-to-B2B order lineage, handle cancellations
- Retry logic for failures, exactly-once processing

## Non-Functional Requirements
- **Performance**: 10K orders/min, <30s latency, <200ms API response (p95)
- **Scalability**: Horizontal scaling, 100+ vendors, auto-scale
- **Reliability**: 99.9% uptime, zero data loss, exactly-once guarantee
- **Security**: Encryption (transit/rest), audit logs

## HLD Components
- **Order Receiver**: API Gateway + Kafka Consumer → validate orders
- **Aggregation Engine**: Redis buffer, time/qty triggers → Kafka Streams/Flink
- **Vendor Router**: Map to vendors → send to B2B OMS via Kafka/API
- **State Manager**: PostgreSQL/MongoDB for order mappings
- **Config Service**: Redis/etcd for rules (time windows, thresholds)

## LLD
**Data**: Order{orderId, customerId, itemId, sku, qty, vendorId, timestamp}, AggregatedOrder{aggOrderId, vendorId, items[], sourceOrderIds[]}  
**Algorithm**: Buffer orders → Group by vendor+SKU → Trigger on time/qty → Send to B2B OMS  
**APIs**: POST /orders, GET /orders/{id}/status, POST /aggregate/trigger  
**Events**: OrderReceived, AggregationTriggered, AggregationCompleted, OrderSentToB2B  
**Tech**: Java/Go, Kafka, PostgreSQL, Redis, Kafka Streams, Prometheus
