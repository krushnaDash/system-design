# UR State machine communication design   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid
disruption See details.

UR State machine communication design

Created by Krushna Chandra Dash on Sep 10, 2025

Introduction 

For the unified reconciliation, the state machine needs to consume data from multiple sources such as OMS, PLUTUS,
FDF, EPAY, UPP Store, UPP.com, BUA, CTH, Unified Settlement, etc ref: n/w digram. Each upstream source has its
own mechanisms for auditing and reconciling data. Most upstream sources that make data available through Kafka should
use Hawkshaw for auditing and reconciliation. However, not all upstream sources send data via Kafka, and there are other
mechanisms by which data is available. Additionally, not all upstream sources support Type 1 reconciliation for Hawkshaw.

Due to these complexities and varying rules for data consumption, allowing the state machine to directly consume data
from upstream and send Hawkshaw signals would result in a convoluted and tightly coupled state machine with a lot of
boilerplate code. Therefore, the suggested design below outlines a better communication approach for the state machine.

FDF

US recon
data

Epay

BUA

CTH

OMS

PLUTUS

Uniﬁed
Settlement

UPP

GCS bucket

GCP BigQuery

GCS bucket

BUA topic

CTH topic

OMS topic

PLUTUS topic

PLUTUS topic

UPP topic

producer Hawkshaw on boarding

uniﬁed
message

ETL JOBS

UR-Normiliser

Hawkshaw ack signal

producer Hawks
on boarding

Hawkshaw

Hawks
sig
for UR

State machine

The state machine will always consume data from one topic, using a unified message structure.
After consuming the data, the state machine will send the Hawkshaw signal for the UR topic.
The state machine will have a single stream to process data from Kafka, allowing it to use external shard allocation
to match Kafka partition consumption with shard locations.
Since the state machine processes data from a unified structure, it is not affected by any changes in the message
structure from upstream sources.
The state machine code will remain simple, as it only needs to understand one type of message and follow one
process for reconciliation and auditing.
State machine will have proper error handelling machinism to handelling any faulty message

Normiliser or ETL jobs

They are the gatekeepers of the UR system, validating all upstream data and converting it to a unified structure
before writing it to an internal Kafka topic for the state machine to consume. There are no exceptions to this rule; all
upstream data must go through the normalizer.
The normalizer will first write the message to the internal topic and then send the Hawkshaw signal.
The normalizer should be able to filter the faulty messages and put them to a error queue.

Unified Message Structure

{
"orderId": String Type , //OrderId
"invoiceId": String Type, //InvoiceId
"payloadType": Enum Type, //PayloadType(Invoice/Tender/Auth/Accounting Stream)
"payload": { UnifiedPayload Type } // UnifiedPayload Model (Invoice/Tender/Auth/Acco
}

Refer: https://gecgithub01.walmart.com/FRE-STFC/ur-unified-model

Business Key Format:   

urn:bkey:wm:us:<event_date>:

<ENTITY_NAME>_<ENTITY_ID>_<SUB_ENTITY_ID>

1) <event_date>: Need to verify whether we get order data in all upstreams (Daniel will validate for all source)

2) <ENTITY_NAME> Should contain entity name( Cosmos Collection name)

3) <ENTITY_ID>  This should be unique key that is used in cosmos DB for the particular source record 

4) <SUB_ENTITY_ID> (Optional) This is applicable for kafka record with more than one message(eg: for BUA and CTH).
Append sub entity id.

Source and Key Table: -To be added by Daniel

Source ID

Keys

Comment

Note:

1. Producers should keep this business key unique per event
2. Ensure this key carries some metadata info about the business transaction
3. Make sure this is not crossing 100 Bytes limit to avoid heavy payloads

Recon API Request:

When message needs to be re consumed. UR Normalised should expose an API which will intake businessKey from
hawkshaw recon message and process it to identify the source table and respond with source data. 

HTTP.GET: /api/v1/recon/<BusinessKey>

Success Response:

HTTP Code : 200
Response:
{
message: "Success"
payload: <PAYLOAD>
}

Message not Found Response:

HTTP Code : 404
Response:
{
message: "Message Not found"
payload: null

 
 
 
 
}

Error Response:

HTTP Code : 500
Response:
{
message: "Error Details"
payload: null
}

No labels
```
