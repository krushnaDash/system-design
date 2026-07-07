Refrence :
https://www.hellointerview.com/learn/system-design/patterns/realtime-updates
https://www.hellointerview.com/learn/system-design/core-concepts/api-design

## API types
- REST
- graphQL
- RPC (gRPC)
- web socket

## REST

Example
``` JSON
GET /events                    # Get all events
GET /events/{id}               # Get a specific event
GET /venues/{id}               # Get a specific venue
GET /events/{id}/tickets       # Get available tickets for an event
POST /events/{id}/bookings     # Create a new booking for an event
GET /bookings/{id}             # Get a specific booking
```

- Resource/things always to be in plurals
- we can use query string for optional filter and sorting parameter
- we can use both hierarchy resource or flat structure like POST /events/{id}/bookings or POST/booking?event_id=<>

whether the relationship is required or optional. 
Use path parameters (or nested resources) when the value is required - like /events/{id}/tickets where you always need to specify which event's tickets you want. 

Use query parameters when the filter is optional - like /tickets?event_id=123&section=VIP where you might want all tickets, or tickets filtered by event, or tickets filtered by both event and section

Path parameters : identify specfic resource you are working with
Query parameter : filter, sort, or modify how you retrieve resources

## GraphQL
 - solve mainly the ubder fetching and over fetching
 - it allows to query multiple resources in one query
 - It create N+1 problem, 
 - GraphQL also handles authorization, as it is single end-poins it is tricky to solve this.

``` JSON
type Event {
  id: ID!
  name: String!
  date: DateTime!
  venue: Venue!
  tickets: [Ticket!]!
}

type Venue {
  id: ID!
  name: String!
  address: String!
}

type Query {
  event(id: ID!): Event
  events(limit: Int, after: String): [Event!]!
}
```    
**GraphQL federation**
it is an architectural pattern that allows organizations to create a single, unified GraphQL API (a supergraph) by combining multiple smaller, independent GraphQL services (called subgraphs)

**Subgraphs**: These are individual, standalone GraphQL services, often developed by different teams, each responsible for a specific business domain (e.g., products, orders, or users). They can be built using different languages and frameworks.

**Supergraph Schema**: The combined, unified schema that results from composing all the subgraph schemas together. It serves as the single source of truth for the entire API.

**Gateway (or Router)**: This is the central component that sits between clients and the subgraphs. It receives client requests, intelligently determines which subgraphs are needed to fulfill the query, orchestrates parallel calls to those subgraphs, and aggregates the results into a single response.

**Schema Composition**: The process of merging subgraph schemas into the unified supergraph schema. This process validates the compatibility and integrity of the schemas and uses special directives (like @key and @extends) to manage relationships and shared data types across services.
**Schema Registry**: A centralized repository that manages schema versions, performs validation checks (ensuring no breaking changes), and provides the composed supergraph schema to the gateway

## RPC
- gRPC is a high-performance, open-source universal RPC framework that is based on HTTP/2 and Protocol Buffers (protobuf)

- REST is resource oriented where RPC is procedure/action oriented
- gRPC is binary where REST is text based
- gRPC is faster than REST  
- it is like calling procedure in remote machine 

```
 REST GET /events/{id}
 gRPC GetEvent(id)
 // Instead of GET /events/123
getEvent(eventId: "123")

// Instead of POST /events/123/bookings
createBooking(eventId: "123", userId: "456", tickets: [...])

// Instead of GET /events/123/tickets
getAvailableTickets(eventId: "123", section: "VIP")
```

## Pagination
- offset pagination
/events?offset=20&limit=10 gets records 21-30
This is intuitive and easy to implement, but it has problems with large datasets. If someone adds a new event while you're paginating through results, you might see duplicates or miss records as the data shifts.

- cursor pagination
/events?cursor=abc&limit=10 gets records after abc

Cursor-based pagination solves this by using a pointer to a specific record instead of counting from the beginning. Here's how it works in practice:

First request: /events?limit=10
Response includes the events plus a cursor pointing to the last record:

{
  "events": [...],
  "next_cursor": "cmd9atj3p000007ky19w1dpy2"
}

Next request: /events?cursor=cmd9atj3p000007ky19w1dpy2&limit=10
Response includes the events plus a cursor pointing to the last record:

 Cons :  it's harder to implement features like "jump to page 5."