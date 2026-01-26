# Filter non URS Transaction for OMS   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid disruption See details.

Filter non URS Transaction for OMS

Created by Krushna Chandra Dash on Sep 10, 2025

Problem Statement:

As part of MVP 1, we want 10% of Fiserv credit card transactions to follow through URS. Currently, not all upstream processes are adding the flag to
identify if a transaction belongs to URS or not. This means we need to design a system to identify non-URS transactions and exclude them from the
URS system.

.Com Transactions

For the .com trascaton we will get the flag from Plutus, FDF, Auth, and Unified settelement team but not from the OMS. This means we need have a
mahanish to to properly handle the invouce messages from OMS.

Option 1 : Allow all the OMS messages from the Normaliser

Since OMS messages do not have the flag, we will allow all OMS messages to pass from the normalizer to the state machine. In the state machine, if
we receive matching events from any other upstream source, we will recognize it as a valid UR transaction.

We will run ETL jobs in the projection database to pull all OMS invoices that are older than a configurable number of days and lack matching events
from any upstream source. These invoices will be marked as non-URS transactions, deleted from the projection database, and excluded from mismatch
consideration.

Risk

To mitigate the risk of failing to report valid URS invoices when upstream sources fail, we can enhance the ETL jobs. This involves checking related
auth/plutus events, identifying the tender, and cross-referencing with UPP auth messages to flag potential URS invoices.

OMS

No ﬁlter

PLUTUS

ﬁlter

Normaliser

uniﬁed
Message

StateMachine

UPP

ﬁlter

ETL

FDF

ﬁlter
based on ﬂag

Entity/
Projection

Inv 1001

Tender T1
Settlement S1
Accounting A1

Inv 1002

Tender T3

Inv 100n1

Inv 100n2

ETL

Option2: Allow Verified UR Messages from OMS to the State Machine

In this approach, OMS messages that are verified as UR messages will be allowed to proceed to the state machine. When the normalizer receives an
OMS message, it will check if a PLUTUS message with the same order_id and invoice_od has been received. If the PLUTUS message is a UR
message, the OMS message will be allowed to proceed to the state machine. Similarly, when a valid PLUTUS message is received, the system will
check for any OMS messages with the same order_id. If found, the OMS message will be retrieved from COSMOS and sent along with the PLUTUS
message.

An ETL process can be executed on the OMS and PLUTUS message storage to identify all invoices for which no PLUTUS messages have been
received. These invoices may be URS invoices, and we will report them accordingly.

The ETL process can check the projection data base, if there is any PLUTUS data with out the invoice infromation and it will look up the missing invoice
will push the same to the SM.

ETL

Report all invoices for which there are no
corresponding OMS messages, as these
may be URS invoices.

OMS
Message Storage

PLUTUS
Message Storage

Projection
Data Storage

push missing
OMS message

look up by
invoice and order id

look up by
invoice and order id

PLUTUS

OMS

Normiliser

publish
oms/plutus
message

SM

Start

Start

Received OMS
Invoice message 

Received PLUTUS
Tender message 

Received
Corresponding
PLUTUS message

Received
Corresponding
OMS message

No

yes

No

yes

Push OMS message

Push OMS and
PLUTUS message

Push
PLUTUS message

stop

stop

Option3 : 

Block all OMS messages from flowing through the normalizer, and run an ETL job to push the OMS messages from the projection once we receive the
PLUTUS messages.

ETL

Report all invoices for which there are no
corresponding OMS messages, as these
may be URS invoices.

OMS
Message Storage

PLUTUS
Message Storage

Projection
Data Storage

PLUTUS

OMS

publish OMS message

Normiliser

publish PLUTUS message 
BLOCK OMS message

SM

Over all Risk

Since there is no flag in OMS to identify whether an invoice belongs to the URS system, we rely on upstream sources for this information. If a particular
invoice is missed from PLUTUS, we cannot determine if it belongs to URS. In such cases, we might incorrectly report these invoices as URS invoices
which are misssing settlements.

Apprache

PROS

CONS

Option1

No perfromance impact on processing of messages in
NM
Easy to implement, since its a ETL job will not impact
the performance

Option2

State machine will not have any un-wanted actor and
hence no clean up needed at state machine

State machine will have a lot of un-wanted actor, which needs a
clean up by the ETL

Might impact the performance of Normaliser, as for each
messages from OMS and PLUTS it will do data base look up
Might increase the cost

Option 3

Seprate process to PUSH the OMS meessage, hence
no load on Noramsliser or State machine

Need to develop the ETL process to process the OMS messages

  We are going ahead with option 2

cc   @ Karunanithi Sivasubramanian    @ Praveen Duttuluri  

No labels
```
