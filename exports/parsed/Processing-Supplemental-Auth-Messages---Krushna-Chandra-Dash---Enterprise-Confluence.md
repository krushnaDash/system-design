# Processing Supplemental Auth Messages   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid
disruption See details.

Processing Supplemental Auth Messages

Created by Krushna Chandra Dash on Sep 10, 2025

The Supplemental auth data will be mapped to Tender with repsect to unified data model. The Supplemental auth will be
process in normaliser to create a Tender message with below structure.

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
    "writeOff": "True" [True, False, Conditional, PartialAuth ],
    "paymentHandle" : "PH001"    
  }
}

Example of a Supplemental Auth

{
    "supplementalAuthorizationEvent": {
        "any": [],
        "eventId": "a945aec4-da1d-40ad-b7a4-7f7fbffe2502",
        "version": "1.0.0",
        "eventHeader": {
            "any": [],
            "orderId": "856b2cca-5524-400b-b999-984697082155",
            "customerOrderId": null,
            "ecommerceOrderId": null,
            "subOrderType": null,
            "eventTime": "2024-08-21T14:34:49-05:00",
            "businessUnit": {
                "any": [],
                "number": 5524,

                "country": {
                    "any": [],
                    "countryCode": "US"
                },
                "type": null,
                "banner": {
                    "any": [],
                    "code": "WALMART",
                    "description": null
                },
                "baseDivision": {
                    "any": [],
                    "code": "1",
                    "description": null
                },
                "address": {
                    "any": [],
                    "street": "512 W MARTIN LUTHER KING JR BLVD",
                    "additionalInfo": [],
                    "territory": null,
                    "city": "AUSTIN",
                    "state": "TX",
                    "postalCode": "78701-1231",
                    "country": {
                        "any": [],
                        "countryCode": "US"
                    }
                },
                "terminal": {
                    "any": [],
                    "id": 98,
                    "idName": null
                },
                "associate": {
                    "any": [],
                    "associateCompanyId": null,
                    "associateStoreId": null,
                    "deviceOperatorId": null,
                    "name": null,
                    "userName": null
                },
                "till": null,
                "temporaryNumber": null,
                "dispensingTerminal": []
            },
            "terminalTransactionId": 4697,
            "previousBalance": 0,
            "resolutionStatus": "SAF_RESPONSE_RECEIVED",
            "originalTransactionType": "SALE"
        },
        "instrumentReference": {
            "any": [],
            "instrumentId": "9313b8e8-5524-400b-b663-984697082181",

            "instrumentType": "CARD",
            "instrumentMediaType": "CREDIT",
            "productType": null,
            "instrumentSequence": null,
            "instrumentCard": {
                "any": [],
                "nonPciCardNumber": null,
                "expirationDate": "2027-05",
                "cvv": null,
                "cvvPrompt": null,
                "suffixDigits": "0012",
                "brand": "VISA",
                "brandSubType": null,
                "vendorId": null,
                "bin": null,
                "nonPciPin": null,
                "uab": null,
                "quantity": null,
                "panSurrogate": [
                    {
                        "any": [],
                        "type": "TOKEN",
                        "value": "8A99F65FF8A5E1C9A038E91089220706053859779916"
                    }
                ],
                "languageCode": null,
                "cardholderType": null,
                "purchaseOrderId": null,
                "iccDataPresent": null,
                "epsSequenceNumber": null,
                "epsTrackingNumber": null,
                "discretionaryData": null,
                "schemaReferenceData": null,
                "formFactor": null,
                "purchaseDeviceSequenceId": null,
                "cardEntryMethodCode": null,
                "currency": null
            },
            "instrumentCheck": {
                "any": [],
                "routingNumber": null,
                "accountNumber": null,
                "checkNumber": null,
                "checkType": null,
                "checkInputType": null,
                "checkProcessingType": null,
                "ecaTraceId": null,
                "ecaTransactionCode": null,
                "phoneNumber": null
            }
        },
        "authorization": {
            "any": [],

            "authResultCode": null,
            "authorizedAmount": 3,
            "id": null,
            "type": null,
            "timeStamp": "2024-08-21T14:31:13-05:00",
            "referenceNumber": "423400009143",
            "approvalNumber": "69537A",
            "networkId": "0056",
            "authResultDescription": null,
            "exceptionCode": null,
            "authorizerId": "19",
            "responseTime": null,
            "correlationId": null,
            "status": "COMPLETED",
            "partialAuthorization": null,
            "authorizedCashbackAmount": 0,
            "settlementMethod": "AUTHORIZER",
            "offlineAuthorization": null,
            "paymentCardAuthorization": null,
            "paymentAccountType": null,
            "authMethod": null,
            "requestedAmount": null,
            "offerTransactionId": null,
            "cardBalance": [],
            "incentiveDetails": [],
            "handler": null,
            "paymentHandler": [],
            "holderMessage": null,
            "settleDate": null,
            "ebtAuthorization": null,
            "safAuthorization": {
                "any": [],
                "actionCode": null,
                "responseCode": null,
                "safTimeStamp": "2024-08-21T14:34:48-05:00"
            }
        },
        "eventFooter": {
            "any": [],
            "originSystem": "GENERAL_SALES_APPLICATION",
            "originChannel": "AUTHORIZATION_MONITOR",
            "fulfillment": null,
            "orderFulfillment": [],
            "clientId": null,
            "clientDescription": null,
            "clientVersion": null,
            "clientTransactionHistory": [],
            "legacyVisitSubType": null,
            "associatedEvents": [],
            "legacyTransactionTime": null
        },
        "id": "856b2cca-5524-400b-b999-984697082155",
        "_rid": "oXBNAI3KihsBAAAAAAAAAA==",

        "_self": "dbs/oXBNAA==/colls/oXBNAI3Kihs=/docs/oXBNAI3KihsBAAAAAAAAAA==/",
        "_etag": "\"b903a9ae-0000-0800-0000-66c86f610000\"",
        "_attachments": "attachments/",
        "_ts": 1724411745
    }
}

Tender

orderId

invoiceId

Supplemental Auth

orderId

orderId

paymentId

instrumentReference.instrumentId

provider

authorization.authorizerId (mapping)

cardType

instrumentCard.brand

amount

authorizedAmount

gtn

eventTime

clientRequestId

clientMatcherId

N/A

N/A

N/A

writeOff

status and resolutionStatus,  

When status is COMPLETED  

Then writeOff  → False

When status is PAYMENT_REJECTED  or resolutionStatus is UNRESOLVED_TRANSACTION

Then writeOff  → True

when resolutionStatus TOKEN_RETRIEVED → Then writeOff  → True

paymentHandle

????

When a floor limit transaction is received from CTH, the normalizer will not generate a Tender for transactions subject to the
floor limit. A floor limit transaction can be identified by the property `paymentCard.panSurrogate.psType = "FLOOR_LIMIT" or
"floorLimit": true.

Partial Authorization

Partial authorization cases can be identified by the flag "authorization.isPartialAuthorization = True". If this flag is absent,
the transaction is considered a full authorization. Send the Tender event with writeOff as PartialAuth.

No labels
```
