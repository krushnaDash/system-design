# Auth message Processing Design from PLUTUS   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid
disruption See details.

Auth message Processing Design from PLUTUS

Created by Krushna Chandra Dash on Sep 10, 2025

Problem Statement

When failed settlements are retried from PLUTUS, if the authorization successes upon reattempt, PLUTUS will proceed
with capture. However, if the authorization fails after all retries, there will be no capture message. To distinguish this case,
the URS system must process the authorization messages to determine if the final retry of the authorization was
unsuccessful.

Message structure

PLUTUS will emit all authentication messages, and among those messages, we need to process the ones where
'isFinalRetry' is set to true. When we receive an authentication message with isFinalRetry set to true, Normaliser will write
the Tender event to the internal topic with writeOff as true. The state machine will then process the tender added events,
and since writeOff is set to true, it will mark the tender as written off and perform the necessary GL adjustments.

{
"orderId": "1001",
"invoiceId": "I1001",
"payloadType": "Tender",
"payload": {
    "paymentId": "1001",
    "provider": "firserv",
    "cardType": "VISA",
    "amount": 10.5,
    "gtn": "W301GPX00TA6",
    "eventTime": "timestamp",
    "clientRequestId": "ae7714d1-a753-44ab-bbfb-0fb9a2f095a7",
    "clientMatcherId": "098fcdef-3f7c-4805-ab94-d88e79a4febf",
    "writeOff": "True" [True, False, Conditional]
    }
}

Ref: CPIDCOMS-24290 - Write-off indicator flag

Processing Capture message with 

When processing a capture message with "isFinalRetry: true", the normalizer will generate the 'Tender' event as a
conditional write-off. If the write-off value is conditional, the state machine will determine whether to mark the transaction
as a write-off based on the settlement result."

Mapping

Capture message with "isFinalRetry: false" → Tender event with "writeOff": "False"

Capture message with "isFinalRetry: True" → Tender event with "writeOff": "Conditional"

Auth message with "isFinalRetry: false" → No message

Auth message with "isFinalRetry: true" and pgPmtTxnStatus is not  "SUCCESS" → Tender event with "writeOff": "True"

No labels
```
