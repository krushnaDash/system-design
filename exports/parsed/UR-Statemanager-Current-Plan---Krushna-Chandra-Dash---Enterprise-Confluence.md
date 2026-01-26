# UR Statemanager Current Plan   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid
disruption See details.

UR-Statemanager Current Plan

Created by Krushna Chandra Dash on Sep 10, 2025

Reviewed with team: Praveen Duttuluri, Arpit, Angello, Vishal, Daniel, Raja

Task

(state manager) Event Handler: instead of multi-map persist in 3 hashmaps

(state manager) Projections: Read state from event journal in new format and rewrite the
graph 

(state manager) Projections: Transaction Reconciliation (all reconciled transactions to
reconciled_transactions)

(state manager) Projections: Clean up data from 5 tables accounting, auth, invoice,
tender, settlements periodically (Future)

Persist data from PostGreSQL to BigQuery (only transaction recon table connect with IDC
- what is progress on this) 

Consolidated table containing all 5 entities in single table (tentatively new service)

Estimate

Status

1 week

2 week

1 week 

In
Progress

In
Progress

In
Progress

Batch job for Summary Table in Big Query

Identify and alert on Mismatches 

State manager Design changes

ur-normalizer

kafka

ur-statemanager
FSM

Event Handler

ur-statemanager
streams

Command Handler

state

invoice_id
payment_id
clientmatcher_id

Set of Entities

Changed: Multimap to Map of Set

journal

event
journal

New data structure for storing entities in UrFSM

This will replace the MultiMap

High level summary of recon 

Store(Invoice,
tender, Accounting)

Auth

Sams (tender)
(future)

Y

Y

Y

Provider(Settlement)

Y

Y

N

N

Y

Y

Y

N

N

N

Y

N

Y

N

N

N

Y

Y

N

N

N

Reconciled

Reconciled
with errors

Not
reconciled

Not
reconciled

Not
reconciled

Not
reconciled

(ecomm
side,
others ?)

Raw meeting Notes

--------------------

23 Jan 2025

 Reviewed with Arpit, Vishal, Naman, Angello, discussed below updates to the design.

We'll keep duplicate set of tenders in two places as map lookup is o(1) vs, list lookup is longer. 

Instead of keeping entire tender object, we'll keep only required identifiers. This will be applicable to all the entities
in set getting persisted part of state only

21 Jan 2025

 Reviewed with Praveen Duttuluri

10 Dec 2024

 Participants:  @ Arpit Agrawal   @ VISHAL VAITLA    @ Luis Bernaola Ibarra    @ Rupal Haribhakti  

Meeting Notes: 

Discussed new structure of state
High Level Design based on discussion 

Outstanding questions:

Are we going to have recon logic in FSM or projection (highlighted in red below)
How do we plan on reconciling from the new state?

For e.g, if we receive settlement event, how do we find matching invoice? 

09 Jan 2025

 Raja, Rupal, Karuna

Transaction level recon

Do we have all elements for dependent process
Timing mismatch - there is card
Redesign of state manager
Consolidated recon transaction

Alternate payment key

Primary key not working
For. Out of 6, 1, 2 4 5 6
For. Out of 6, 1, 2 3 5 6
Timezone format mismatch

Local
Gmt

Mistmatch (backend)

Rule based or ML
Mistmatch decision maker

Checks and balances to identify all data sources
GL Adjustment
Customer Adjust -> UPP / EPAY

PostGre / Cosmos to BigQuery

Summary Table

When it got uploaded, deposited, requested
When it is Accounting - business side (Walmart)
Wire, sailing funding come from unified settlement
Accounting from big query (SAP)

Missing data / columns in all 5 entities

15 Jan 2025

16 Jan 2025

 Arpit, Karuna, Rupal, Daniel, Raja

Summary of transaction level recon discussions:

When statemanager receives tender or settlement (in deposited state)

Inserts a new row into this table

if tender exists, mark tender to Y
settlment_deposited to Y  
if accounting entity exists, it will mark accounting to Y
if invoice exists, mark invoice to Y
if auth exists, mark auth to Y

Rename table recon_summary to transaction_recon or something better without summary suffix

 
We'll no longer add  partial_reconciled and reconciled columns

Transaction level recon (rename recon_summary to transaction_recon)

order_id PRIMARY KEY

invoice_id PRIMARY KEY

payment_id (PRIMARY KEY)

clientmatcher_id PRIMARY KEY, source tender

original_payment_id  PRIMARY KEY 

amount

settlement_deposited = Y when settlement = DEPOSITED, N otherwise

auth (Y/N)

accounting (Y/N)

tender (Y/N)

invoice (Y/N)

partital_reconciled  [ TBD ]

reconciled [ TBD ]

created_ts

last_updated_ts

mark_delete

function (coming from auth)

provider (coming from auth)

transaction_date timestamp NULL, source: tender.payment_timestamp

business_unit_id

-------------

Index: default on primary key, transaction_date

Questions

Do we need partial reconciled flag? (when all entities are received and matching but auth is missing) : No we don't
need it [ we'll derive it from all other flags present] 
Do we need reconciled flat? (when all entities are received and matching): No we don't need it [ we'll derive it from
all other flags present] 

No labels
```
