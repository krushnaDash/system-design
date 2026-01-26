# UR low level design and details   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid
disruption See details.

UR low level design and details

Created by Krushna Chandra Dash, last modified 9 minutes ago

ADR - UR ETL solutions
Auth message Processing Design from PLUTUS
Data movement
Design solutions to convert from append blob to block blob Objective:
Filter Criteria for Auth Message
Filter non URS Transaction for BUA
Filter non URS Transaction for OMS
Mismatch Schema
Order_id and Payment_id mismatch with store txns
Processing Auth message without Order_id
Processing Supplemental Auth Messages
Unified Reconciliation - C4-design Diagram
UR State machine Design

SSP n/w digram PL1

SSP digram

Upstream

gl-journal-
post.api.prod.walmart.com
         SSP00001245

SAP/GL
SSP00001245

Epay
SSP00003453

BUA
SSP00002906

CTH
SSP00001114

OMS
SSP00001106

PLUTUS
SSP00001106

FDF
SSP00007585

Uniﬁed Settlement
SSP00007718

UPP
SSP00005669

httos/443

TCP/9093

TCP/9093

TCP/9093

TCP/9093

https/443

TCP/9093

TCP/9093

https
443

GCP
BigQuery
SSP00002191

GCS bucket

BUA topic

UR topic

CTH topic

OMS topic

plutus topic

GCS bucket

US topic

UPP topic

https/443

tcp/9093

tcp/9093

https/443

TCP/9093

TCP/9093

https/443

WCNP-kubie

https/443

https/443

TCP/9093

S
SSP0

ur-gl-adjuster
(Microservice)

ur-etl-jobs

ur-statemanager
(Microservice)

ur-run-job

ur-schduler

ur-normaliser
(Microservice)

ur-payment-expection-be
(Microservice)

ur-payment-expectio

(Microservice)

URS application suite

https/443

https/443

https/443

UPP
smart proxy
SSP00005669

http://smart-proxy.prod.walmart.com

UR SSP PL2- Latest

https/443

https/443

https/443

https/443

https/443

https/443

Azure Cosmos
SSP00002693

Azure SQL
SSP00001125

GCP
postgresql

Azure BLOB
Storage

CCM 2
SSP00005407

Akeyless Vault
SSP00002852

https/443

https/443

https/443

Storage systems

G
Big
SSP0

htt

Uniﬁed Data Pipeline
Spark job

SSP digram

Upstream

gl-journal-
post.api.prod.walmart.com
SSP00001245

SAP/GL
SSP00001245

Epay
SSP00003453

BUA
SSP00002906

CTH
SSP00001114

OMS
SSP00001106

PLUTUS
SSP00001106

FDF
SSP00007585

Uniﬁed Settlement
SSP00007718

UPP
SSP00005669

httos/443

TCP/9093

TCP/9093

TCP/9093

TCP/9093

https/443

TCP/9093

TCP/9093

https
443

GCP
BigQuery
SSP00002191

GCS bucket

BUA topic

UR topic

CTH topic

OMS topic

plutus topic

GCS bucket

US topic

UPP topic

https/443

tcp/9093

tcp/9093

https/443

TCP/9093

TCP/9093

TCP/9093

https/443

SSP: 
SSP00000048

ur-etl-jobs

ur-statemanager
(Microservice)

ur-run-job

ur-schduler

ur-normaliser
(Microservice)

URS application suite

https/443

https/443

https/443

https/443

https/443

https/443

https/443

UPP
smart proxy
SSP00005669

http://smart-proxy.prod.walmart.com

Azure Cosmos
SSP00002693

Azure SQL
SSP00001125

GCP
postgresql

Azure BLOB
Storage

CCM 2
SSP00005407

Akeyless Vault
SSP00002852

https/443

https/443

https/443

Storage systems

G
Big
SSP0

htt

Uniﬁed Data Pipeline
Spark job

From SSP point of view

Sno

System type

System Name

Integration (Kafka/ file/API)

Status

Coments

1

2

3

4

5

Upstream

OMS

GTP managed Kafka

Upstream

PLUTUS

GTP managed Kafka

Upstream

UPP(PGpay)

GTP managed Kafka

Upstream

FDF

GCS bucket

Done

Done

Done

Done

Upstream

Unified Settlement

GTP managed Kafka and BigQuery

Done

Upstream

EPAY

GCS bucket 

Done

Sno

System type

System Name

Integration (Kafka/ file/API)

Status

Coments

6

7

Down stream

UPP

REST API

Down stream

GL Journal

REST API

Done

Done

Please check this for Upstream Kafka Details

cc  @ Nidhi Gupta  ,  @ Sunitha Seeram  

Page viewed 19 times

User

Krushna Chandra Dash

Edits

2

Comments

0

Labels

0

No labels
```
