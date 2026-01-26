# Processing Auth message without Order_id   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid
disruption See details.

Processing Auth message without Order_id

Created by Krushna Chandra Dash on Sep 10, 2025

Problem Statement

Some systems are directly calling Epay without sending the `order_id` when initiating an Epay authentication request. As a
result, Epay is unable to include the `order_id` in the authentication message it publishes. In the URS system, processing
these authentication messages without an `order_id` is challenging because the "order_id" is mandatory. Therefore, we
need a solution to handle these transactions effectively.

Option1

Requesting all such upstream systems to include the "order_id" in their requests. However, this is not a simple task, as we
don't have a comprehensive list of these upstream systems, and each of them has its own set of priorities.

Option2

Enrich the authentication messages by including the `order_id` from the corresponding CTH message, and then pass
them to the state machine.

Enriching the Authentication Messages

The ETL batch job that processes authentication messages from Epay can enrich them by scanning the CTH order event
storage in Cosmos and then sending the enriched messages as events to the state machine.

Fulﬁlment System
[Software System]
OMS Accounting, Plutus,
CTH

Fulﬁllment
OrderEvent

EventStorageDatabase

[Cosmos Database Table]

Store a copy of each events with TTL

EventSourcedDatabase

[Postgres SQL Database Table]

A persistent store saving event history

Projection Database

[Postgres SQL Database Table]

Accounting System
[Software System]
BUA

Accounting
Event

Auth System
[Software System]
UPP

Auth
Events

Settlement System
[Software System]
US

settlement
Events

Auth System
[Software System]
EPAY

Auth
JSON

Accounting System
[Software System]
FDF

Accounting
Event

Normalizer

[Container: WCNP, Docker]

Validates, normalizes and enriches

incoming order and event messages

State Manager

[Container: Akka, WCNP, Docker]

Manages end to end lifecycle of a

funding request using pre-conﬁgured 

business rules throughout

Reconciliation and dispute process 

FundingExceptions
[Postgres SQL Database Table]
Stores all payment exceptions and
actions from epact associates

UR-ETL

[Container: WCNP Cron, Docker]

Validates, normalizes and enriches

incoming order and event messages

scan

EventStorageDatabase

[Cosmos Database Table]

Store a copy of each events with TTL

No labels
```
