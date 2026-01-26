# UR State Machine Flat Design   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid disruption See details.

UR State Machine Flat Design

Created by Krushna Chandra Dash on Sep 10, 2025

UPP = Auth

CTH = (Tender, Invoice)

PLUTUS = Tender

OMS = Invoice

BUA = Accounting

FDF = Accounting

Unified Settlement = Settlement

Problem Statement

We are getting 5 different entities in state manager, there are various many to many relationships which are not allowing us to create a proper hierarchy to do state transitions on.  One
of the requirements of this state machine is to trigger alerts or side effects upon receiving any one of these entities.  To properly implement we would need the current entity and all the
entities that correspond to it.  We need to keep our design flexible enough to incorporate new business rules, as well as any new entities we could be receiving in the future.

Akka State Machine Background

Pertinent background information of the inner working of an implemented akka state machine is that it requires a persistent id, command handler, and an event handler.  The persistent
id pertains to what you are keeping track of, for example in our case the persistent id would be the order id this represents a full sales transaction whether that be through Brick and
Mortar or E-commerce.  A command handler defines a function to handle incoming entities to our state machine, so every entity type that comes into our state machine would need to
be mapped to a command, for example an Auth entity would be mapped to an addAuthEntity command.  This command would wrap the entity and then add any other meta data that
we would the command handler to have.  Once in the command handler the entity would be persisted to the backend storage we have defined, then it converts the command to an
event and then the event handler would receive this and transition the state.  Once the event handler has transitioned this state the command handler can get the new state and
perform any necessary logic on the state.

Proposed Solution

Command Handler

Event Handler

addEntityCommand

mapToEventEntityCommand

Event Received

Deposit Entity to Bucket

Persist Event

Send to Event Handler

State

Auth

Tender

Tender

Accounting

Invoice

Use Akka Graph DSL to
piece all entities together

5 bucket received

Use current entity and
return from previous
function to trigger alerts
or side effects

The proposed solution would have us start out with the entity command, and do a transformation to an event, this would be persisted in our postgresql back end.  From here the event
handler will run by adding the entity into the current state.  The command handler would then receive the state of the order id which would be 5 buckets with all entities received until
now, and the current entity, it would run the 5 buckets through an Akka DSL graph, which defines a stream.  We will have a stream per each type of entity.  The output of this function
would have all current items related to the current entity, and from here we can trigger any events related to the accumulated items, with the addition of this new entity.

In order to make sure we can link all relevant entities together the below diagram shows how you can link them altogether regardless of what entity is received.

Linking Items

AUTH

Get

Field:
Payment Id

Filter

Filter

Filter

Settlement

Tender

Get

Get

Get

Get

Field:
Client Matcher

Filter

Filter

Field:
Invoice Id

Fitler

Field:
Client Matcher

Filter

Filter

Field:
Invoice Id

Fitler

List<Tender>

Accounting

List<Settlement>

List<Settlements>

List<Tenders>

Invoice

List<Settlements>

List<Tenders>

Invoice

Get

Get

Field:
Client Matchers

Filter

Filter

Get

Get

Get

Get

Field:
Payment Id's

Fitler

Filter

Field:
Payment Id's

Fitler

Filter

List<Tender>

List<Settlement>

List<Auth>

Accounting

List<Auth>

Accounting

Get

Get

Get

Get

Filter

Field:
Payment Id's

Filter

Field:
Invoice Id's

Filter

List<Auth>

Accounting

List<invoice>

Acounting

Get

Get

Field:
Payment Id

Fiiter

Filter

Field:
Invoice Id

Filter

List<Tender>

List<Settlement>

Invoice

Get

Get

Field:
Client Matchers

Filter

Filter

Invoice

Get

Field:
Invoice Id

Filter

Filter

List<Tender>

List<Settlement>

Get

Get

Field:
Payment Id's

Filter

Filter

List<Tender>

List<Settlement>

List<Auth>

Accounting

Get

Get

Field:
Payment Id's

Filter

List<Auth>

Tasks

DeadLine

%complete

Implement Auth graph for assembling

Implement Invoice graph for assembling

Implement Settlement graph for assembling

Implement Tender graph for assembling

Implement Accounting graph for assembling

August 29

100%

August 29

100%

September 6

100%

September 6

100%

September 6

100%

Integrate changes in processing messages to be persisted and fed to graph

September 6

75%

Implement data structure for storage and lookup of graph

September 6

50

Implement basic business rules for state transition alerts

TBD

State Manager Redesign Considerations:

1) Rename the attribute payment id to Recon_key in all projection table and code, Because that field contains invoice + payment id during ecom transaction and alternate payment
id during epay transactions. 

No labels
```
