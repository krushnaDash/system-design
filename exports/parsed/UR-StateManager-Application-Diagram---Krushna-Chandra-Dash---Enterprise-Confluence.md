# UR StateManager Application Diagram   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid
disruption See details.

UR StateManager Application Diagram

Created by Krushna Chandra Dash on Sep 10, 2025

DATA Source

CTH

BUA

Plutus

OMS

UPP

Uniﬁed
Settlement

FDF

EPAY

CTH Topic

BUA Topic

Plutus Topic

OMS Topic

UPP Topic

US Topic

Hawkshaw
 Enabled

GCS Bucket
Cloud Storage

UR-Normalizer

Spring Boot Application

UR - State Manager

UR-Uniﬁed Topic

Akeyless Vault

Hawkshaw
 Enabled

Akka Kafka Cluster
Sharding

Akka Event Sourcing

Akka Graph

Ak

Order-Id

Actor

Transactions with
Unique keys mapped
to Graphs

Events sent as Envelop

Reconciled Event Triggered

Unique transaction when receive
sources is marked as recon

Events
Persisted

GCP

Azure Cosmos DB

AKKA 

Sharded/Partitioned
Event Journals Tables

Test Suites

Unit/Integration
Test Gate

Sonar Code
Coverage

Code Coverage
Gate

Akeyless Vault

Pull Secrets
from Vault

Pushes Changes 

All Gates Passed

Validation Checks

CI /CD 

Developer

Gates

Any Gate Failes

In
Out of im

Stop Deployment/
Roll Back to
previous version

No labels
```
