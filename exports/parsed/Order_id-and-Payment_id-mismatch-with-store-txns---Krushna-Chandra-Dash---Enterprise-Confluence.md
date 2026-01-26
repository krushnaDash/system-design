# Order_id and Payment_id mismatch with store txns   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid disruption See details.

Order_id and Payment_id mismatch with store txns

Created by Krushna Chandra Dash on Sep 10, 2025

Problem Statement

Some clients are making requests directly to Epay without including the order_id or payment_id when initiating an Epay authentication request. As a result, Epay is unable to include
these IDs in the authentication messages it publishes. While some clients do send the order_id and payment_id, there is no consistency, meaning the same order_id or payment_id
is not maintained across systems. In the URS system, processing these authentication messages without an order_id or payment_id is challenging because the order_id is
mandatory. Additionally, for reconciliation purposes, these IDs must match across systems. Therefore, we need a solution to handle these transactions more effectively.

Some clients example are

IVR -> CPAY
CPR -> CPAY
SAMS express return -> CPAY
Walmart pay -> CPAY
Elvis SAMS new return flow
walmart pharmacy
RX Easy Pay is using legacy DLL to connect via ePay directly. This is a potentially impacting one. 

Payment_id mismatch issues

UPP always operates with a unique payment_id via smart proxy, requiring each call to UPP to include a distinct payment_id. This means that the same authorization and its reversal
will have different payment_id's. However, an exception is made for SAF transactions, where the same payment_id can be used for each retry. In contrast, the Epay system does not
have such rules, allowing a single payment_id to be used for multiple requests. As a result, in Epay, the same payment_id can be seen for both authorization and authorization
reversal. Example transcation can be seen in below attached file.

UPP → Differnet payment_id for authroziation and reversal

Epay→ Same payment_id for authroziation and reversal

sale_Reversal.xlsx

Option1: Requesting the upstream to add a flag

In option 1, each upstream system (CTH and UPP/Epay) will add a flag when the order_id and payment_id are missing and they generate one. This flag will allow these transactions
to be filtered out from URS and routed to the legacy system for reconciliation and settlement.

Processing  order_id and payment_id mismatch Txns in URS

URS system generating the alternate Id to process theses txn with a flag.

Due to the lack of consistency in order_id and payment_id, the URS system will generate an alternate_payment_id from key business fields while normalizing the transaction. This
alternate_payment_id will be used for reconciliation and to enrich the messages.

Logic for alternate payment Id

For Auth/CTH message we can use below key fields to generate the alternate_payment_id

siteNumber
terminalId
tenderType
authorizerId
timeStamp ??? 
authorizedAmount
referenceNumber
approvalNumber
pansurrogate.value

When the normaliser process the CTH/auth messages it will generate an alternate_payment_id for each tender and auth messages based on the above keys fileds and save them to
cosmos. The SM still can reconsile the transcation by using the alternate_payment_id.

An example of alternate_payment_id  may looks like : 
siteNumber_terminalId_tenderType_authorizerId_timeStamp_authorizedAmount_referenceNumber_approvalNumber_pansurrogate.value, → apply Base 64 encoding ???

alternate_payment_id : 550_44_CREDIT_FDNorthHost_2024-08-29T13:14:33-05:00_3.51_424220000012_312187_77DF9EAF27FF765F312A9C23AF639364763375278616 →
NTUwX0NSRURJVF9GRE5vcnRoSG9zdF8yMDI0LTA4LTI5VDEzOjE0OjMzLTA1OjAwXzMuNTFfNDI0MjIwMDAwMDEyXzMxMjE4N183N0RGOUVBRjI3RkY3NjVGMzEyQTlDMjN

Handelling Mismatch for Order_id

An ETL job can be executed from the Projection DB to identify all unmatched authorizations and Settlement caused by a mismatch in the "order_id". The correct "order_id" can be
determined by searching for the corresponding tender using the "alternate_payment_id". Once a match is found, the ETL process can generate the necessary events to send to SM for
updating the authorization data.

Container Digram

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

Auth System
[Software System]
EPAY

Auth
JSON

scan

look for orphan Auth

Accounting System
[Software System]
FDF

Accounting
Event

EventStorageDatabase

[Cosmos Database Table]

Store a copy of each events with TTL

Projection Database

[Postgres SQL Database Table]

BUA

OMS/PLUTUS

SETTLEMENT

UPP

Epay

FDF

Entity/
Projection

Case 1

Order_1001

Case 3

Order_1003

Tender - P1001

Tender - P1003, A_id=A101

Auth - P 1001

Accounting -P 1003, A_id=101

Accounting -P 1001

Normaliser

uniﬁed
Message

StateMachine

Settlement - P 1001

ETL

pull all the case 3 entities and try to
merge them

Case 2

Order_1002

Tender - P1002

Auth - P 1212

Accounting -P 1001

Settlement - P 1212

Case 3

Order_A101

Auth - P=1213 A_id=A101

Settlement - P1213 A_id=A101

Case 3

Order_1004

Tender - P1004 A_id=A102

Accounting -P 1004 A_id=A102

Case 3

Order_A102

Auth - P 1214 A_id=A102

Settlement - P 1214 A_id=102

PaymentExceptions UI

[Container: ReactJS, WCNP, Docker]

Frontend for Exceptions Dashboard

for Business users to take action

PaymentExceptionsProcessor

[Container: WCNP, Docker]

Backend for frontend to process

actions on exceptions

Order_1003

Tender - P1003

Auth - P 1003

Accounting -P 1003

Settlement - P 1003

Case 1 : Happy path where the order_id and payment_id all match, no issues and puzzle solved

Case2 : Order_id matched, but payment_id not, in that case it is within the same entity in the sate macine the reconcilation can be done by using the alternate_pyment_id

case3: Order_id not matched, then we have merge the Tender and accounting  with Auth and Settlement, uing the alternate_payment_id

Partial Auth ??

Refund to match orginal sales order

Disccused in the call we no need to match the refund slaes order to orginal selase order.

Note: The Unified settlement teams aslo needs to generate the alternate_payment_id by applying same logic as UR will be doing.

Empty order_id and payment_id from Auth system Epay and UPP

In case of empty order_id and payment_id we will copy alternate_payment_id and use it.

Example SQL

select a.alternate_payment_id, a.order_id, a.payment_id, t.order_id, t.payment_id from stfc_ur.tender t, stfc_ur.auth a  where 

This will give all the Tender detaisl which have wrong order_id and payment_id with correct order_id and payment_id

Now the ETL can fire some batch query post the Tender and settlement event with right order_id and payment_id

MoM of 24th September meeting - Recon with alternate payment_id

To simplify reconciliation, we have agreed to use a single key, payment_id, for the process. The normalizer will follow the steps below to achieve reconciliation using payment_id:

It will copy the alternate_payment_id to the payment_id field, and the original payment_id  will be moved to a new field called `original_payment_id`.
It will enrich the accounting event using a CTH lookup to include the alternate_payment_id in the payment_id field while preserving the original payment_id in the
original_payment_id field.

After the above changes there will not be any case2, we just need to update the order_id and republish the events

select
a.order_id as "old_order_id",
a.original_payment_id ,
t.order_id as "new_order_id",
t.original_payment_id

from stfc_ur.tender t, stfc_ur.auth a 
where t.payment_id =a.payment_id  and t.order_id !=a.order_id

--- Publish the auth message with new order_id
--- publish all the setellment meesaage with new order_id

No labels
```
