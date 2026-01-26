# Filter non URS Transaction for BUA   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid
disruption See details.

Filter non URS Transaction for BUA

Created by Krushna Chandra Dash on Sep 10, 2025

Problem Statement:

As part of MVP 1, we want 10% of Fiserv credit card transactions to follow through URS. Currently, not all upstream
processes are adding the flag to identify if a transaction belongs to URS or not. This means we need to design a system to
identify non-URS transactions and exclude them from the URS system.

Store Transactions

For the store trascaton we will not get any flag, we can use the store number (business unit id) to unboard to URS, plus
the upstream like CTH, UPP and EPAY will have the provider details which will help us tp identify the URS trnanscation.
But the upstream BUA is currently missing the provider details in the message, so we need a mechanism to identify the
BUA messages which should be pass to URS.

We can follow a similar approach as describe here Filter non URS Transaction for OMS for OMS.

Allow Verified UR Messages from BUA to the State Machine

In this approach, BUA messages that are verified as UR messages will be allowed to proceed to the state machine. When
the normalizer receives an BUA message, it will check if a CTH message with the same order_id  has been received. If
the CTH message is a UR message, the BUA message will be allowed to proceed to the state machine. Similarly, when a
valid CTH message is received, the system will check for any BUA messages with the same order_id. If found, the BUA
message will be retrieved from COSMOS and sent along with the BUA message.

An ETL process can be executed on the CTH and BUA message storage to identify all URS orders for which no BUA
messages have been received. These orders may be URS invoices, and we will report them accordingly.

The ETL process can check the projection data base, if there is any CTH data with out the accounting infromation and it
will look up the missing accounting event will push the same to the SM.

ETL

Report all URS orders/invoice for which
there are no corresponding BUA messages,
as these may be URS orders.

BUA
Message Storage

CTH
Message Storage

push missing
BUA message

look up by
order_id

look up order_id

CTH

BUA

Normiliser

publish CTH/BUA
message

Start

Start

Received BUA
Accounting messages 

create multiple accounting
messages with order_id
payment_id

Received CTH
Order message 

create one invoice and
multiple Tender message
with order_id and
payment_id

Received
Corresponding
CTH message

yes

No

Push BUA message

stop

For each Tender
message check
matching
BUA message

No

yes

Push BUA and
CTH message

stop

Push
Tenders and Invoic
message

No labels
```
