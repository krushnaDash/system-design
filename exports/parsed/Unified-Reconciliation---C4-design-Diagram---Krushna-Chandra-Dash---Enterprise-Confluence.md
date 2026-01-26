# Unified Reconciliation   C4 design Diagram   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid disruption See details.

Unified Reconciliation - C4-design Diagram

Created by Krushna Chandra Dash on Sep 10, 2025

Container Digram

[Container Diagram] - Uniﬁed Reconciliation

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

UR-ETL

[Container: WCNP Cron, Docker]

Validates, normalizes and enriches

incoming order and event messages

FundingExceptions
[Postgres SQL Database Table]
Stores all payment exceptions and
actions from epact associates

PaymentExceptions UI

[Container: ReactJS, WCNP, Docker]

Frontend for Exceptions Dashboard

for Business users to take action

PaymentExceptionsProcessor

[Container: WCNP, Docker]

Backend for frontend to process

actions on exceptions

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

Criteria for Event Storage Database

Requirement

Scalability

Notes

TPS 

Number of Events per day

Data Retention

QPS/IOPS

Auto Scale 

Strong consistency/Eventual
Consistency

Availability

Multi Region

Active/Passive or Active/Active

Secondary Indexes

Do we need to query the data using attributes in the event data?

TTL

Data can be automatically DELETEd records from transaction tables based on choosen policies. This will help
us in deleting the data that is needed for transaction processing

GTP Managed Service

easy to maintain and no maintenance required by application team

Document Storage

JSON data can be storage as it is

Criteria for  State  Database/ Event source (Framewok managed with Data partitioning )

Required

20K

150M +50M =200M

30Days

20K

Yes

Eventual Consistency

Active/Active

Yes

Yes

Yes

Yes

Requirement

Scalability

Notes

TPS 

Number of Events per day/month

Data Retention

QPS/IOPS

Auto Scale

Strong consistency/Eventual
Consistency

Availability

Multi Region

Active/Passive or Active/Active

Secondary Indexes

Do we need to query the data using attributes in the event data?

TTL

Data can be automatically DELETEd records from transaction tables based on choosen policies. This will help
us in deleting the data that is needed for transaction processing

GTP Managed Service

easy to maintain and no maintenance required by application team

Document Storage

Criteria for  Projection  Database (Frame work managed)

Requirement

Scalability

Notes

TPS 

Number of Events per day/month

Data Retention

QPS/IOPS

Auto Scale

Strong consistency/Eventual
Consistency

Availability

Multi Region

Active/Passive or Active/Active

Secondary Indexes

Do we need to query the data using attributes in the event data?

TTL

Data can be automatically DELETEd records from transaction tables based on choosen policies. This will help us
in deleting the data that is needed for transaction processing

GTP Managed Service

easy to maintain and no maintenance required by application team

Document Storage

Required

20K

200M

90 days

20K

Yes

Any

Any

No

Yes

Yes

No

Required

5K

100M

180days

5k

No

Strong consistency

Active/Passive

Yes

No

Yes

No

Projection ER model

No labels
```
