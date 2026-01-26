# UR State machine Design   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid disruption See details.

UR State machine Design

Created by Krushna Chandra Dash on Sep 10, 2025

Problem Statement

The existing state machine is configured to handle store orders, utilizing a straightforward actor model where the order ID and payment ID serve as key identifiers. Currently, all
upstream systems that send events to the state machine possess both keys, ensuring that messages are correctly routed to the designated cluster sharding actor. However, in order to
process .com orders, we need to incorporate additional key identifiers. This introduces two main challenges: firstly, there is a need to modify the schema to include these new keys for
actor creation; and secondly, not all upstream systems will possess all the necessary keys.

Upstream with their avaible Keys

UPP

PK1 OrderId

Fulﬁllment

CTH

PK2 PaymentRequestId

PK1 OrderId

PK3 PaymentHandle

PK2 PaymentId

PK4 GlobalTransactionId

Plutus

PK1 OrderId

PK2 PaymentHandle

PK3 InvoiceId

OMS Accounting

PK1 OrderId

PK2 InvoiceId

Accounting

BUA

PK1 OrderId

PK2 PaymentId

FDF

PK1 OrderId

PK2 InvoiceId

PK3 PaymentHandle

UnﬁedSettlement

All

PK1 OrderId

PK2 InvoiceId

PK3 PaymentHandle

PK4 SettleMatchKey

Suggested Solutions

Problem

Name

Detils

Pros

Cons

Recommanded

C

Differnt
keys old
events vs
new
events
structure

Use Akka
schema
evaluation 

Akka supports Event/Schema Evolution
capabilities
https://doc.akka.io/docs/akka/current/persistence-
schema-evolution.html, this can be used to
support different keys combination with old and
new events

Do a one
time
migration

One time migration can be done of all old
messages/events and snapshot from old
structure to new one

Develop
version-2
of state
machine 

Develop a revised version of the state machine in
Java incorporating a new set of keys. This
updated state machine will be capable of
processing traffic from both store and .com
platforms, whereas the existing state machine will
be limited to handling store traffic only.

The old state machine will be phased out once
we achieve sufficient confidence in the new
system's performance and all outstanding store
orders have been reconciled or complete

No migration
activities
needed 

Integrating and maintaining complex logic to
handle both versions of events will significantly
increase the complexity of the state machine
Increase the manitantbilty and monitoring cost

No

No

Migrating substantial amounts of data from the
old structure to the new one could be susceptible
to errors and must be executed with absolute
accuracy.
Additionally, it may become necessary to sift
through and migrate a significant volume of data
that may not be needed

Developing a new state machine in java will
required some extra effort
We need maintenet two version of statemachine
for a short period of time.

Yes

No additional
logic to
process
different
version of
events

Cleaner
approach 
We will have
another
system to
compare the
result during
the  prod
rampup
 Our long-term
objective
includes
migrating the
state machine
to Java, aiming
to complete
this before the
current system
becomes
overly complex
This transition
may also
address some

Problem

Name

Detils

Pros

Cons

Recommanded

C

not all
upstream
systems
will
possess
all the
necessary
keys

Use a
parent and
child
acotor

Create
only one
actor at
order level

Implement an order-level actor responsible for
determining the appropriate timing to instantiate
a child actor at the invoice level. This decision
should be made once the order-level actor has
received all required keys. Subsequently, after
that it will forward messages to the child actor for
processing.

Create only one actor at order level and have
data structure to maintent the state at invoice
level.

unforeseen
issues, such
as lagging and
other
discrepancies.
Furthermore,
the prototype
of the new
state
machine's
code will be
reviewed by
Lightbend,
offering an
opportunity to
identify and
rectify potential
problems early
on.

One actor per
invoice will
allow little bit
easy
implementation
of state
transition at
invoice level

Little complex
to implement
state transition
at invoice level
The acotr life
will increase
since it
represent all
the invoices

No

Yes

An additional order-level actor will be introduced,
tasked with implementing complex logic to
manage the child actor.
This setup introduces numerous potential failure
points, particularly in scenarios where the parent
and child actors reside on different nodes.
Such an approach is not recommended by
Lightbend consultants.

POC
completed(https://gecgithub01.walmart.com/FRE-
STFC/ur-statemanager and result looks very
promising.
The number of acotr will be very less
Since we have an acotr at order level, it can give
the full picture at order level
We can easily pull out order level as well as
invoice level status
This approach recommended by Lightbend
consultants
Able to handle any future requirements, since we
can communicate with the State machine with
just using order id

Suggested approach

We can develop a new state machine in java with single actor at order level. This approach not only aligns with our long-term objectives but also, according to our evaluation with the
tech leads, will not affect our project timeline.

The POC code is completed and committed in this repo :https://gecgithub01.walmart.com/FRE-STFC/ur-statemanager

HighLevel class digram

POC source code : https://gecgithub01.walmart.com/FRE-STFC/ur-statemanager

URState

-uRSalesOrder: URSalesOrder

+ addInovice(Invoice invoice): URState

+ addAccounting(String invoiceId, Accounting accounting): URState

+ addTender(String invoiceId, Tender tender): URState

+ addSettlement(String invoiceId, Settlement settlement): URState

1

InvoiceState

UrKey

- InitialState: InvoiceState

- orderId: String

- IncompleteState: InvoiceState

-InvoiceId:String

- ReconciledState: InvoiceState

- paymentHandle: String

- ******

*

1

URSalesOrder

Invoice

- orderId: String

- state: InvoiceState

- invoices: Map<String,Invoice>

1..*

- inoviceId: String

+ .....

- amount: String

- tenders: Set<Tender>

- accountings: Set<Accounting>

- settlements: Set<Settlement>

+ copy(state:InvoiceState):Invoice

Tender

- paymentHandle: String

-amount:String

- paymentType: String

Accounting

- PostingDate: String

-amount:String

- paymentHandle: String

- receivableName: String

Settlement

- status: String

-amount:String

- clientMatcherId: String

1..n

State Transition Diagram Invoice -Recon

BUA

CTH

OMS

PLUTUS

Account Event
order_id
payment_id

Store order
order_id
payment_id

OrderShipment
Message
order_id
invoice_id

order capture
message with
order_id, invoice_id,
paymentHandle/
clientRequestId

FDF

Accounting Event
Order_id
invoice_id
paymentHandle

Orphan

order_id,
paymentId

Auth Event
orderId
paymentId

UPP
Store Auth
message

any Event from BUA/CTH

InitializedState

order_id,invoice_id
paymentHandle

fulﬁllment

Invoiced
Accounted
Captured

order_id,invoice_id
paymentHandle

Different State

InvoicedAndAccounted
InvoicedAndCaptured
CapturedAndAccounted
InvoicedAndAccountedAndCaptured

.com UPP
(payPal, Chase payment
tech)

Settlement Event :  with

status requested, uploaded and

State on Settlement

ReadyForSettlement -> Requested
SettlementInitiated -> Uploaded
Settled/SettlementAccepted  ->Deposited

Settlement Event
with status requested, uploaded

US

OrderId
PaymentHandle
InvoiceId
GTN
SettleMatchKey

Settlement Event
with status deposited

ReadyForSettle

Yes

is Duel
message

No

Settlement Event

Settled

ReadyForReconciliation

deposited

GlobalTransactionID
SettleMatchKey
OrderId
PaymentHandle
InvoiceId

All Records
Matched

No

Yes

NoActionEvent

MismatchState

Reconciled

AdjustmentEvent

PaymentDisputeEvent

MismatchAccepted

ReadyForSettlement

Disputed

MoM of 29th March call

1. State Machine Version 2 Adoption: Unanimously, we've agreed to proceed with State Machine Version 2, selecting Java as our development language of choice.
2. Ongoing Development with AKKA: Given the current phase of development with certain features in PEKKO, we will continue utilizing AKKA. A planned migration from AKKA

to PEKKO is on the horizon, subject to further review and planning.

3. Priority Tasks: Rectifying the issues with the current State Machine projection is our foremost priority. Parallelly, the development efforts for State Machine Version 2 will persist.
4. Technical Solution for Projection Issue: To address the current projection issue, we've decided on the integration of the R2DBC connector. This connector will also be

beneficial for the development of the new State Machine.

5. Assigned Responsibilities:

Chris is tasked with resolving the existing issues related to the State Machine projection.
Luis, Daniel, Krushna and other designated team members will embark on developing the new State Machine, focusing on incorporating new features and adding
 business logic.

6. Approval of New State Machine Design I am pleased to report that the new State Machine design, featuring a single actor at the order level and maintaining state at the

invoice level through a sophisticated state data structure, has been officially approved by Lightbend.

POC task in progress

1. Implement of R2DBC connector for recording event journal data to a SQL database, such as PostgreSQL with Data partitioning (https://doc.akka.io/docs/akka-persistence-

r2dbc/current/data-partition.html) [Done]

2. Implement the R2DBC connector for writing projection data to a SQL database, such as PostgreSQL  ( https://doc.akka.io/docs/akka-persistence-r2dbc/current/data-

partition.html)[Done]

3. External shard allocation to match up Kafka Partition consumption with shard locations (https://doc.akka.io/docs/alpakka-kafka/current/cluster-sharding.html)[Done]

Akka-persistence with R2DBC

Akka-persistence offers several strategies for data management, with the prevalent approach being the utilization of a Cassandra database for event journaling and snapshots.
Cassandra, a NoSQL database, excels under write-heavy loads, making it an ideal candidate for state machines managing vast volumes of events. Presently, our state machine
employs Cassandra for its persistence layer. However, I propose shifting towards a SQL database, specifically PostgreSQL, integrated via an R2DBC connector. The rationale behind
this suggestion encompasses several factors:

1. Cost Efficiency: Cassandra's operational costs are significantly higher compared to SQL databases like PostgreSQL. This cost disparity makes PostgreSQL a more economical

choice for persistence.

2. Distribution and Sharding Capabilities: Akka inherently possesses mechanisms for data distribution and sharding. Leveraging Akka's built-in functionalities to distribute data

across multiple, independent storage systems can be more efficient than relying on a distributed data storage solution like Cassandra. This approach can simplify the
architecture without compromising on scalability or data availability.

These points advocate for the adoption of a SQL database for persistence, highlighting the potential for cost savings and architectural simplification without sacrificing performance or
scalability.

How SQL data base will able to take the load

Utilizing a single, non-distributed database can potentially create a bottleneck for applications demanding high throughput. To mitigate this risk and efficiently distribute the load, key
components such as the event journal, snapshot store, and durable state can be divided across multiple tables and backend databases.

Partitioning plays a crucial role in this process. Data is partitioned into slices, which Akka then distributes across several databases and tables. For instance, consider a configuration
with number-of-partitions set to 4 and number-of-databases to 2. In this scenario, both the event journal and snapshot data would be distributed across four tables within
two separate physical databases.

This approach not only alleviates the pressure on a single database but also leverages Akka's capabilities for efficient data management and distribution. By doing so, it ensures
scalability and high performance even under substantial load, aligning with the throughput requirements of demanding applications.

Slice

Database

Table

0-255

DB1

event_journal_0

256-511

DB1

event_journal_1

512-767

DB2

event_journal_2

768-1023

DB2

event_journal_3

cluster Sharding entities

Entity-1001
slice 166

Entity-6000
slice 717

Entity-8000
slice 527

Entity-1002
slice 167

Entity-7000
slice 622

Entity-5000
slice 812

event_journal_0
slice 0-255

event_journal_1
slice 256-511

event_journal_2
slice 512-767

event_journal_3
slice 768-1023

Connection-factory-0-1

Connection-factory-0-1

The advantages of using R2DBC PostgreSQL over Cassandra for persistence and projection.

The R2DBC project (https://r2dbc.io) aims to provide fully reactive connectivity to relational databases. R2DBC is based on the Reactive Streams initiative (Lightbend is a founding
contributor),  and Reactive Streams is itself is the underlying SPI of Akka Streams. Therefore there is strong synergy between databases that provide an r2dbc interface and other
components of the Akka ecosystem, especially Akka Streams and Alpakka connectors. R2DBC is meant to be a more modern replacement for JDBC. 

Over the last couple of years, Lightbend has been investing a lot in r2dbc-based technology and have several new features in Akka that rely on r2dbc functionality. 

The r2dbc connector enables simpler storage for event and snapshot journals of Akka Persistence. The advantage of using single instance relational database instances over
multi-node distributed databases lies in the simplicity of deployment and operation. For example, a single node postgres instance is easier to maintain (is generally more
resilient) than a distributed Cassandra deployment.
The r2dbc connector allows for Akka Persistence Data Partitioning over several rdb instances  https://doc.akka.io/docs/akka-persistence-r2dbc/current/data-partition.html .  In
this way, Akka Persistence r2dbc provides for similar scale-out capacity as might be offered by distributed databases.
R2dbc enables Akka Projection gRPC https://doc.akka.io/docs/akka-projection/current/grpc.html, which can be thought of as a brokerless message queue (think Kafka but
without having to deploy and maintain any additional resources).   
Akka Projection gRPC in turn powers features in Akka Distributed Cluster https://doc.akka.io/docs/akka-distributed-cluster/current/index.html, such as replicated event sourcing
(active-active or hot standby). These can be key components for implementing active-active or hot standby across datacenters or availability zones.

Recommended strategy for managing failover in PostgreSQL databases, particularly in scenarios involving data partitioning

In some sense, the resilience of single node postgres instances can be higher — just based on their inherent simplicity — over a distributed database solution. However it is true that a
single instance represents a single point of failure. If an instance fails, then no entity partitioned to that db instance can do replay or writes until the db comes up again, but if an entity
is already started it could still accept non-writing commands. Therefore it is important to ensure the database is deployed with some kind of automatic recovery (like k8s auto restarts or
installed as an auto-restarting service, etc). In addition it will be more important to have a plan for recovery (multi az failover for example) than with a distributed database which is less
likely to have a total meltdown since that is somewhat built in.

POC load test result

We did some recent tests on a simple Akka PoC that implemented a microservice for inventory management. 
Test Infra:

Database: db.m5d.2xlarge (8vCPU / 32 GB Ram), AWS RDS (Postgres)
EKS: 5 x m5.xlarge (4vCPU / 16 GB Ram)

With this deployment, we use ghz (and later gatling) to run tests. In the following case, we ran 1 million requests across 2000 entities. Here’s a sample output from one run:

Summary:
  Count:  1000000
  Total:  49.30 s
  Slowest:  2.85 s
  Fastest:  2.67 ms
  Average:  484.22 ms
  Requests/sec: 20283.47

Some moresult from Akka

https://www.linkedin.com/pulse/benchmarking-database-sharding-akka-lightbend-inc--78cvc/

Page viewed 8 times

No labels
```
