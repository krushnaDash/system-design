# UR Statemanager redesign   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid disruption See details.

UR Statemanager redesign

Created by Krushna Chandra Dash on Sep 10, 2025

Decision / Meeting Log
Problem
Why redesign is necessary
Scope of work for redesign
Redesign High level architecture for statemanager (splitting into two services)
Brainstorming on design
State data model
Reconciliation Options  

Option 1 Reconciliation using Akka State Manager with BQ Projection
Option 2: Akka State Manager with Projection in Postgres SQL and BQ for Reconciled records
Option 3: No State Manager - Kafka Connect to BQ - Batch Job for recon check 
Option 4: No State Manager - Postgres for Entity level records - Batch for Recon - BQ for Recon Summary
Option 5: No State Manager - GCS - Spark for recon - BQ:
Option 6: State Manager and Projection simplified 

Application Flow
Additional Information

Decision / Meeting Log

Contributors / Attendes

Statemanager Redesign Proposals

Meeting Recording / Date

@ Ting Wu   @ Nachiappan Ramasamy
@ Chad Willwerth   @ Lalith Rallabhandi  

Decision to include invoice_reconcile information part of
payment summary

Invoice Recon information will be included in payment
summary part of redesign and format is attached csv.
We’ll include invoice_amount, invoice_id and
invoice_reconciled columns. When sum of amount from
all the transactions for a paymentId reconcile part of
same invoice_id match with the invoice_amount, we’ll
mark invoice reconciled.

@ Ting Wu   @ Nachiappan Ramasamy
@ Chad Willwerth   @ Lalith Rallabhandi  

Validations and mismatches:
Two types of mismatches were discussed:

1. Accounting is present but settlement missing or

tender missing or auth missing

2. Maual Recon (due to data or technical issue we

didn’t reconcile)

15 May 2025

https://walmart.zoom.us/rec/share/E4zEVpNosSypninOMb2xj9
3761SUZjilxMGVWeuKCaU.K2szoFuG86tIOKeh

Passcode: szzz80*&

15 May 2025

https://walmart.zoom.us/rec/share/E4zEVpNosSypninOMb2xj9
3761SUZjilxMGVWeuKCaU.K2szoFuG86tIOKeh

Passcode: szzz80*&

@ Praveen Duttuluri
@ Karunanithi Sivasubramanian   @ Joshua Orozco
@ Chad Willwerth   @ Arpit Agrawal  

Based on discussion today, Praveen suggested to use
Cassandra to support the volume of data we forecast
part of 85% goal.

29 Apr 2025

Some Pros / Cons discussed:

Cassandra is NoSQL db, we’ll benefit from partition /
sharding features when we want to scale up

We’ll loose consistency but since we are using akka, we
are assuming akka will make sure we don’t drop any
events from persisting into event journal.

There aren’t any updates, event journal is append only,
so we’ll not face issues with consistency.

Cassandra has TTL feature, we can use that over DB
triggers we have in place today to mark event journal
records to be delated for a configured timeframe.

Earlier decision to use Posgres was mainly cost driven,
which is outlined
https://confluence.walmart.com/pages/viewpage.action?
pageId=2000965364#URStatemachineDesign-Akka-
persistencewithR2DBC – with delete functionality, we
are assuming cost will remain manageable.

We have Cassandra in place with EPC statemanager in
production today, and there weren’t any major concerns
by engineers.

There aren’t any major concerns, we’ll evaluate
Cassandra with redesign project sprint starting May 1st
and make final decision based on performance testing
outcome before moving forward to prod parallel
deployment.

  @ Daniel Devadoss   @ Luis Bernaola Ibarra
@ Rupal Haribhakti   @ VISHAL VAITLA
@ Naman Purwar  

Option 4 for now, if we find a unique key to join all
entities revisit redesign

20 Feb 2025

 
 
 
 
Contributors / Attendes

Statemanager Redesign Proposals

Meeting Recording / Date

Decision:
https://confluence.walmart.com/pages/viewpage.action?
pageId=2627166767#URStatemanagerredesign-
RedesignStateformatoptions

  @ Daniel Devadoss   @ Luis Bernaola Ibarra
@ Rupal Haribhakti   @ VISHAL VAITLA
@ Naman Purwar  

Option 1 (statemanager keep map of paymentId to
payment summary, projection as new service sending
data to BQ)

03 Apr 2025

New Design decision:
https://confluence.walmart.com/pages/viewpage.action?
pageId=2627166767#URStatemanagerredesign-
ReconciliationOptions:

State Structure

UR Data Model

07 Apr 2025

Problem

Currently, state-manager stores state object as MultiMap (custom) data structure and persist in event journal.  In normal scenario FSM creates 4 maps per entity and each entity is
duplicated across all 4 maps. When we have more than one tender / invoice per order, we will duplicate each individual entity 4 times.

The reconciliation happens in projection. Akka team recommended to keep projection code light to achieve maximum performance. Currently graph is unable to find correlated entities
uniquely, which makes some transactions not reconciling correctly. Our recon percentage is ranging from 90-97 on daily basis, we are aiming for 99% reconciliation.

In future, when we start having 100% ecommerce traffic, we can face challenges in terms of memory footprint high because of duplication of entities in State and graph logic consumes
memory too.

This redesign tries to simplify the code so that it is more maintainable and performant with higher traffic in future. 

Refer to Current Statemanager design and UR State Manager Performance Benchmarking for further details

For more details refer to pros / cons section of Option0.

Why redesign is necessary

To simplify in memory footprint and handle 25-30 million transactions per day (100+ million messages per day) in future, we want to reduce time for individual recons, please refer to
pros / cons sections below for Option0, which is current design can explain why. 

Statemanager, kafka lag. From Nov, till today (Apr 2025) - scaled up to 15 pods still xmatters with a huge kafka lag is seen.

Scope of work for redesign

1.  Redesign Statemanager
a. New State Format
b. Move Recon Logic from projection to statemanager
c. Projection as a separate service (To be defined)

i. Help us scale projection independently and write into consolidated table for easy mismatch and alert queries

 
 
Redesign High level architecture for statemanager (splitting into two services)

Kafka Topic

Consume

Akka Stream

Event Handler
Update Actor State

Is Reconciled

Yes

Create Recon event
with 5 Entity
payload

Postgres Event
Journal

Read

UR Projection
Service

No

Write

Alert Action

No

Is Alert

Yes

Alert Action

Brainstorming on design

State data model

Identifiers from Upstream:

BQ Event Table

Read

ETL / Batch Job

Write

BQ Entity Level
Table

Recon Reporting

Auth

Invoice

Plutus /tender

Settlement

Accounting

(OMS)

OrderId

OrderId

OrderId

OrderId

OrderId

PaymentHandle

InvoiceId

InvoiceId

InvoiceId

InvoiceId

PaymentId is InvoiceId

PaymentHandle

PaymentHandle

PaymentHandle

ClientMatcher

ClientMatcher

ClientMatcher (Not available yet, WIP)

Current Entity relationships:

For Store, we'll use PaymentId field (which is combination of IDs: Store Number, register number, tender type (CREDIT / DEBIT / etc.),  authorization id, transaction timestamp,
reference number, approval number, p2pe token value)

For ECOMM, we'll use: InvoiceId + PaymentHandle 

Some examples of reconciliation:

When we receive Accounting : 

order_id, invoice_id, payment_handle --> find tender and settlement, if we have duplicates, we use client matcher to find matching settlement from tender.

When we receive Tender or Settlement:  : 

order_id, invoice_id, payment_handle --> find Accounting and use client matcher to find settlement or tender

We’ll use invoiceId to find the invoice

Notes from discussion with Praveen:

Finalized Option 4

Event Journal - what data elements will be stored
Average size of a event journal record per order_id
Test flexibility, reprocess specific entity in case we fix a bug

Earlier discussion Notes:

Part of implementation, we'll not have to persist state to event journal, instead we'll do state transition in EventHandler
Reference: state transition code in epc-statemanager which handles 20 million transactions today and doing state transition in memory
Alternatively, we can leverage projection to read from state changes directly via akka persistence

Option2: State Object having

map of invoiceid to sets of invoices

Option3: State Object having
map of Transaction Key to individual transaction consist of invoice, auth,
accounting, tender, settlement entities

Op

Lo

map of paymentId to set of accounting, tender and auth

Trasaction key (unique per transaction) -

map of clientmatcherid to set of tenders and settlements

Credit: Angello

Option1 GTN + invoiceID (ecomm)
Option2 PaymentHandle + Invoice (ecomm)

paymentid for store

Credit: Daniel

Note: Akka Cluster Sharding (distributed key value store) stores Stat

Option1: 
keep current
logic and Graph
asis

UR State Machine
Flat Design

Actor State

Order ID

Transaction Map
HashMap<String,ReconEntity>

Invoice Map
HashMap<String,InvoiceReconEntity>

Transaction
 Key

Txn Key 1

Txn Key 2

Recon Entity

Recon Entity 1

+ auth: AuthEntity

+ accounting: AccountingEntity

+ tender: TenderEntity

+ settlement: SettlementEntity

Recon Entity 2

+ auth: AuthEntity

+ accounting: AccountingEntity

+ tender: TenderEntity

+ settlement: SettlementEntity

ClientMatcher TransactionKey Map
HashMap<String,String>

Client Matcher
 ID

Txn Key

c-mat-cher-id

Txn Key 2

Invoice ID

Invoice 1

Invoice Recon Entity 1

+ txnList: Set<String>

+ invoice: InvoiceEntity

Invoice 2

Invoice Recon Entity 2

+ txnList: Set<String>

+ invoice: InvoiceEntity

OrphanSettlement Map
HashMap<String,SettlementEntity>

Client Matcher
 ID

SettlementEntity

c-mat-cher-id

Settlement Entity

Note:
Transaction Key ( Unique Identiﬁer for a transaction) 

Store = 5 attributes -alternate payment (TBD)
Ecom = Client Matcher ID or  (Invoice +GTN) (TBD)

 Transaction key will be set in Normaliser based on data type
and source

Note: We don't need statemanager to store Order level reconciled flag.

Pros

Pros

Pros

  Perf
benchmark
supports 7-10k
TPS

  No extra
development
effort

  State object will be smaller compare to current format

 Light state object with minimal data required to reconcile

  EventHandler will process incoming data and projection

 No duplication of entity

will do the recon

  Reconciliation individual entity level and invoice level

(same as today)

 Faster access to data of a particular transaction ( O(1) complexity )

 Reconciliation at all levels ( Transaction, Invoice and Order)

Cons

Pro

10-

Option2: State Object having

map of invoiceid to sets of invoices

Option3: State Object having
map of Transaction Key to individual transaction consist of invoice, auth,
accounting, tender, settlement entities

map of paymentId to set of accounting, tender and auth

Trasaction key (unique per transaction) -

map of clientmatcherid to set of tenders and settlements

Credit: Angello

Option1 GTN + invoiceID (ecomm)
Option2 PaymentHandle + Invoice (ecomm)

paymentid for store

Credit: Daniel

 Quick to implement, no logic change (just rewrite using
different data structure), we'll not have to do performance
benchmark again

 require change in normalizer to insert transaction key as it is not part of majority of

entities today

 GTN can not uniquely identify settlements ** this is rectified by using

 Reconciliation at all levels (Transaction, Invoice)

payment_handle + invoiceId as combination as of Feb 17th 

Cons

 tender and settlement duplicated on paymentIdmap and

clientmatcher map

 PaymentHandle changes when capture failed (failed transaction) ** we'll have to use

clientMatcher to payment_handle lookup map to handle this edge case (only found 6
failed transaction in prod db)

Option1: 
keep current
logic and Graph
asis

Cons

 State Object is

larger, graph
processing
happens in
memory 

 Graph logic
harder to maintain
and debug

 Kafka lag is
frequently seen
(threads are in
TIMED_WAITING,
WAITING state
because of
resource
contention in
stream processing
an projection side

 When we have
Multiple tender for
same invoice,
currently
reconciliation isn't
marking entities
correctly

 We are
missing 3-10%
transactions in
ecomm, even
when all entities
are present

No effort

Effort: 1 week (some work is already done) (Iteration 1 only)

Effort: 

Notes: 
Invoice ID + Payment Handle = Ecomm 

Store number, set of columns  = Store, reference, Order_id and Payment_id 

Notes on Implementation

class FlattenEntities(
        AccountingEntity accountingEntity,
        TenderEntity tenderEntity,
        AuthEntity authorization, SettlementEntity settlement
) {
}

class State{
        Map<String, FlattenEntities> transactionkeyToEntitiesMap;
        Map<String, InvoiceEntity> invoiceEntityMap;
        Map<String, String> clientMatcherToPaymentHandleMap; 

}

Reconciliation Options  

Reconciliation of entities can be achieved thorough various options.

Op

Lo

Co

sim

No

St

Se
Se

Se
Se

Ma

}

Lo

Ac
an
lo
Sa
In
Ex

198
05T

If
lo

     
Option 1 Reconciliation using Akka State Manager with BQ Projection

Kafka Topic

Consume

Akka Stream

Event Handler
Update Actor State

Is Reconciled

Yes

Create Recon event
with 5 Entity
payload

Postgres Event
Journal

Read

UR Projection
Service

No

Write

Alert Action

No

Is Alert

Yes

Alert Action

BQ Event Table

Read

ETL / Batch Job

Write

BQ Entity Level
Table

Recon Reporting

Pros:

Cons:

Questions:
1) What will be the partition in BQ?
2) Are we going to keep old version in all entity level table?
3) How we will purge old data?
4) Does joining 5 entity tables efficient for Recon Report? 
5) How we will move data from BQ event table to Entity level table?

6) How event journal will handle 200 million records per day?

Option 2: Akka State Manager with Projection in Postgres SQL and BQ for Reconciled records

Kafka Topic

Consume

Akka Stream

Event
Handler(Updates
Actor State)

Postgres Event Journal

Read

No Action

No

Is Alert

No

is Reconciled

Projection Handler

Yes

Alert Action

Yes

Write

Generate Reconciled Payload
and insert to Reconciled Table
and Delete Entries from Entity
level table

Write

Delete

cleans up reconciled
records and maintains
only pending recon
which is expect to be
less

Postgres Entity Level
Table

Big Query

Postgres Reconciled Table

ETL

Recon Reporting

Pros:

Cons:

Question:
1) Can Postgres handle 200 million rows per day in entity level table?

Option 3: No State Manager - Kafka Connect to BQ - Batch Job for recon check 

Kafka Topic

Consume

Kafka Connect

Write

BQ Entity level
Table

JOB - Run Recon
Query
Every TBD Hours 

Write

Temp table with
reconciled record

(Consolidated Recon
Record )

Insert

Move recon
data to BQ
Recon Table

Join

Recon Report

Join

Pros:

Cons:

Questions:
1) How duplicate settlement and near real time events will be handled?
2) How purging of old reconciled data will be handled?

Option 4: No State Manager - Postgres for Entity level records - Batch for Recon - BQ for Recon Summary

Clean up activity

Deletes Reconciled 
data in 5 entity level table

Clean Up Reconciled
Data

UR Normaliser

Write

Join

Postgres
Entity level table

Recon Report

Join

Read

Job: Run recon Query
every hour/TBD

Write

Postgres
Recon table

Read

ETL Job to move
reconciled data

Write

Move
Reconciled data
to BQ

Pros:

Cons:

Questions:
1) How Postgres can handle 200 million records per day?
2) How duplicate settlement and near realtime event will be handled?

Option 5: No State Manager - GCS - Spark for recon - BQ:

Perform recon directly in BQ via Spark

Option 6: State Manager and Projection simplified 

BigQuery

kafka connect

reconciled events

event journal - entities

Normalizer

recon
kafka topic

statemanager

State 
Snapshots

We can move away from akka, why? 

Spring provides a mature ecosystem with built-in dependency injection.
Spring provides robust integrated transaction management
Reduces configuration complexity for typical enterprise applications.
Extensive community support and wide adoption in the enterprise space
Spring is opensource vs akka is licensed
akka framework is very complex,

hence there is steep learning curve
it hides complexity in proprietary code,
hard to debug

Current code uses springboot and akka together, which defeats the purpose of getting advantage of spring's dependency framework as akka classes can not be managed by
spring
We want to build recon business rules configurable in future, which will be difficult to handle within akka

Pros

Cons

No data duplication - event and reconciled data persisted directly to BigQuery 
Simplified architecture, no projection as a separate service
statemanager perform recon only 
Currently, event journal, projection tables are huge periodic maintenance activities are required - we'll not have to maintain it. 

we need to persist state and perform cleanup but we can solve it by using a nosql / document database

Application Flow

Input Entity
(Any Entity)

No

Is Actor/State Exist

Yes

Create State Object
with Txn key and create
new Recon Entity
object with input entity
and update invoice map

Get State Object

Get Recon Entity
From Transaction
Map using Txn Key

Update State

No Action / Alert

No

Check If Txn
Reconciled

Yes

Update Recon
Status for that Txn
in State

Checks whether txn
contains all required
entities

No Action / Alert

No

Check If
Respective Invoice 
Reconciled

Yes

Update Recon
Status for that
Invoice in Invoice
map in state

Checks whether all txn in
invoice is reconciled

No

Check if Order 
Reconciled

Yes

Checks whether all invoice
in order is reconciled

No Action / Alert

Mark the Order state
as reconciled

Additional Information

Design walkthrough with team

https://walmart.zoom.us/rec/share/fA2GeNcQXeQxGwx8_1iLkkjgozo0suOhczgB2Zi8Z_qHfwDUYpNQmFtdAYlK-VRk.nJNJ9mNHz_ewizQI

Passcode: !gku8*r!

Pros Compared to current State Manager design

1. Light state object with minimal data required to reconcile and  straight forward transaction level details using Transaction Key
2. No duplication of any entity
3. Faster access to data of a particular transaction ( O(1) complexity )
4. Reconciliation at all levels ( Transaction, Invoice and Order)

Potential issues with this design and Teams Review Points:

1. How to handle SAMS transactions which might miss some entities?

Analysis for moving logic from Projection handler to Event handler

Lightbend team suggested to move the recon logic from projection handler to event handler. team will analyze this and come up with details for make this change

Development Effort Analysis and Status Tracker

Team should come up with effort analysis and timeline for implementing this redesign
Updated Implementation Plan section

No labels
```
