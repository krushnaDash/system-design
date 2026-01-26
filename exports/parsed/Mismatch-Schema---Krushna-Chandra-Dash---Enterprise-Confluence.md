# Mismatch Schema   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid
disruption See details.

Mismatch Schema

Created by Krushna Chandra Dash on Sep 10, 2025

UR Entity model Diagram

Authorization

Tender 

PK PaymentID VARCHAR(255) NOT NULL

PK

PaymentID/Handle VARCHAR(250) NOT NULL

PK

orderId VARCH

PK orderID VARCHAR(250)  NOT NULL

FK, PK orderId VARCHAR(250) NOT NULL

PK

invoiceId VARC

currency VARCHAR(50)

authResultCode INT

FK, PK invoiceId VARCHAR(250) NOT NULL

RequestedAmt DECIMAL(10,2)

authorizedAmount DECIMAL(10, 2)

paymentType VARCHAR(50)

basePaymentTimeStamp TIMESTAMP

txnType VARCHAR(50)

approvalNumber VARCHAR(50)

processedAmt DECIMAL(10, 2)

globalTxnNumber VARCHAR(250)

paymentTimestamp TIMESTAMP

networkId VARCHAR(50)

p2peToken VARCHAR(250) 

cardExpDate VARCHAR(50)

currency VARCHAR(50)

paymentSubType VARCHAR(50)

status VARCHAR(50)

paymentHandle VARCHAR(250)

paymentSubType VARCHAR(50)

function VARCHAR(250)

globalTxnNumber VARCHAR(250)

cardEntryMethodCode VARCHAR(250)

cardType VARCHAR(50)

Settlement

Accounting

PK, FK orderId VARCHAR(255)  NOT NULL

PK, FK

invoiceId VARCHAR(255) NOT NULL

PK, FK invoiceId VARCHAR(255) NOT NULL

PK, FK

orderId VARCHAR(255) NOT NULL

PK, FK PaymentID VARCHAR(255) NOT NULL

PK, FK

PaymentID VARCHAR(255) NOT NULL

cardType VARCHAR(50) 

txnType VARCHAR

result VARCHAR

clientId VARCHAR(255) - .com/store

amtRequested DECIMAL(10,2)

amtSettled DECIMAL(10,2)

amtRejected DECIMAL(10,2)

currency VARCHAR(255)

globalTxnNumber VARCHAR(250)

settlementMatchkey VARCHAR

amount DECIMAL(10,2)

businessDate DATE

PostingDate DATE

storeID VARCHAR(50)

ledgerAccountCode VARCHAR(50)

globalTxnNumber VARCHAR(250)

Comments

Status

Others

Need to add authorizer or provider fields in authorization

Yet to start

Need to add store number in all tables

Settlement identifier

Yet to start

Yet to start

InvoiceType VA

InvoiceDate DAT

currency VARCH

subTotal DECIM

Tax DECIMAL(1

Discount DECIM

shippingCharge

totalAmount DE

tcNumber VARC

S

PK, FK invoiceId VARC

PK, FK orderId VARCH

PK, FK PaymentID VAR

settlementExpec

modiﬁedDate DA

settlementDate 

uploadDate DAT

processorDate D

ammendDate D

No labels
```
