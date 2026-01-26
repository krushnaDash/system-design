# Design solutions to convert from append blob to block blob Objective    Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid
disruption See details.

Design solutions to convert from append blob to block blob
Objective:

Created by Krushna Chandra Dash on Sep 10, 2025

Problem Statement:

In the current system STFC EPC 2.0,  Most of the Applications  we are persisting into Azure Append blob for storing the
upstream data.
Azure Append blob has the following cons:

1. Limited Size: Append blobs have a maximum size limit of 195GB, which may not be sufficient for some large-scale
applications.

2. No Random Access: Unlike block blobs, append blobs do not support random access. Data can only be added to the
end of an append blob and cannot be updated or deleted.

3. Append Only: Once the data is appended, it cannot be modified or deleted until the entire blob is deleted. This could
be problematic for applications that require frequent updates or modifications to the stored data.

4. Performance: The speed of appending data to a blob could decrease as the blob size increases. This can affect the
overall performance of applications that need to append data frequently.

5. Costs: Azure storage costs can add up quickly, especially if you're storing a large amount of data in append blobs.

6. Limit on Number of Blocks: There is a limit on the number of blocks that can be uploaded to an append blob. After
reaching the limit of 50,000 blocks, no more data can be appended.

In addition to the aforementioned drawbacks, a significant disadvantage of using Append Blob is the lack of Lifecycle
Management. This implies that data will remain in the append blob indefinitely. Consequently, if the data in the blob is not
being utilised, it could lead to unnecessary and potentially high costs with Azure. 

Please refer to the attached screenshot below an Append Blob, where there is no option for data archiving – only deletion
of the blob is possible. However, if you look at the second and third screenshots for Block Blob, there are numerous
options available for data lifecycle management.

To address the issues mentioned above, we have decided to opt for Block Blob.

What is a Block Blob?

Block blobs are optimised for uploading large amounts of data efficiently. Block blobs are composed of blocks, each of
which is identified by a block ID. A block blob can include up to 50,000 blocks. Each block in a block blob can be a
different size, up to the maximum size permitted is 4000 MiB for Version 2019-12-12 and later.

we need to design a system that converts the current writing of events from append blob to block blob format. The system
should organize block blobs to allow efficient searching of events by their IDs, while adhering to the limitation of 50,000
block per blob. Each event will be stored as JSON data, and the system should handle a throughput of 2,000 events per
second.

Solution Design

Key Considerations:

Block Blob Limitation:Maximum of 50,000 block per block blob.
Event Throughput:** 2,000 events per second.
Data Storage Format:** JSON.
Search Capability:** Events should be searchable by their IDs which means it has to be indexed.

Architecture Overview

1. **Data Ingestion Layer:**

   Batch Processing: Group incoming events into batches for efficient writing to block blobs (e.g., 500 events
per batch).

2. Block Blob Storage Strategy:
    Blob Naming Convention: Use a naming strategy for block blobs that incorporates time-based identifiers and shard
identifiers to facilitate quick access and organization.
     - Format: `yyyyMMddHHmmss_shardId.json`
     - Example: `20240725120000_001.json` where `001` is a shard identifier.
   - **Sharding Strategy:** Divide the event data across multiple blobs to balance the load and stay within the 50,000 block
blob limit.
     - Shards can be based on time intervals or hash values derived from event IDs.

3. **Blob Management and Searchability:**
   - **Metadata Storage:** Maintain a lightweight index or metadata storage to track event IDs and their corresponding blob
locations. This can be implemented using:
     - Azure Table Storage for quick lookup by event ID.
     - A distributed NoSQL database like Azure Cosmos DB for scalability and speed.
   - **Event Indexing:** Store a mapping of event IDs to their respective blob URIs and offsets within the JSON array inside
the blob.

4. **Data Writing Strategy:**
   - **Parallel Writes:** Implement parallel writes to multiple block blobs to accommodate the high event throughput.
   - **Batch JSON Structure:** Each block blob contains a JSON array of event objects, facilitating efficient storage and
retrieval.
   - **Blob Size Management:** Limit the number of events per blob to ensure blobs do not exceed Azure's block blob size
limits (currently up to 190.7 TiB per blob).

5. **Blob Creation and Rotation Policy:**
   - **Rotation Trigger:** Rotate blobs either based on time (e.g., every minute) or when a certain number of events (e.g.,
10,000 events) is reached.
   - **Archiving:** Implement the life cycle management to move the BLOB from hot >> clod >> archive

6. **Fault Tolerance and Scalability:**
   - **Retry Logic:** Implement retry mechanisms for failed writes to ensure data consistency.

Option 1 : write the events to Block Blob with blocks based on Time:

Organize the data into Block Blob on an timely basis, within the date folder. Events should be grouped or windowed for
smaller time interval(let's say 10mins) and these blocks are finally written as block blob for every bigger time interval(Let's
say 1hr). Once an hour has passed, the data should be written into the next block blob. This means that each block blob
will have 6 blocks and each blocks having 10mins of events. Inparallel, we can uploading 6 blocks at a time to a block
blob. 

   
Refer to the diagram below for more clarity. The date folder name will correspond to the date the data is written into Azure
block blob, for instance, '2024-08-05' if the data was written today. 

For instance, the block blob file at 12'0 clock would be named '012.json', containing the blocks of 12th hour. For the next
hour, the 13th hour, the file will be named '013.json'. 

S.no

Pros

Cons

1

2

3

Data Organization: This approach provides a
systematic way of organising data into block blobs. It
makes data retrieval easier based on date and more
efficient since data is categorised based on date and
time. Near real-time data availability can be achieved. 

Data Segregation: By separating data into hourly
chunks, it is easier to manage. If there is an error or
issue, it can be isolated to a specific hour block blob,
reducing the impact on the entire system.

Data Accessibility: Store metadata of each events
while committing blocks to block blob so that we can
using them for data retrieval during eventId search. 

Complexity: This method requires complex
coding to ensure that data is correctly split,
organised and stored in the correct block blobs.

Potential Data Overhead: Organising the data
into multiple blocks might result in data
overhead, as each block will have metadata
associated with it. If the amount of data is too
large, this might result in storage inefficiency.

Data Integrity: If a block fails to upload
correctly, it might affect the integrity of the entire
block blob. This could result in data loss or
corruption.

Option 2 : write the events to Block Blob based on event id:

Organize the data into Block Blob according to each event id number. 

We need to create a separate block blob file for each event id number with blob index tag having key as eventId. This
process continues for each day. 

In this method, for data retrieval, a simple REST call using the blob index tag can retrieve the bob without using any
metadata. Azure maintains this information for every event writes. But the user must have the necessary permission to
access the container blob.

please refer the below diagram for the same

S.no

Pros

Cons

1

2

Data Organization: Organising data in Block
Blob based on event id makes data retrieval
easier and faster, especially if you are looking for
information related to a specific event id.

Complexity: This approach can become complex and
difficult to manage as the volume of data increases.
Parallel writes to blob is not achievable.  Causes small
files issue impacting performance in writing and
reading.

Data Integrity: Each blob can be independently
uploaded, which provides a high level of data
integrity.

Option 3 : Convert the append blob to Block blob:

In our ongoing Integration application, we write data to an Append blob every hour throughout the day, resulting in 24 files
daily. We convert these Append blobs to Block blobs by executing the ETL cron job each day.

please refer the below diagram for the same.

S.no

Pros

Cons

1

Scalability: Since block blobs are designed to
handle large amounts of unstructured data, this

Performance Impact: The conversion process may
have an impact on system performance, particularly if

S.no

Pros

Cons

approach scales well with increasing volumes of
data.

large volumes of data are being converted.

2

Simplified Data Management: By converting
append blobs to block blobs and executing the
ETL cron job, the data management process
becomes simplified and automated.

Potential Data Loss: If the conversion process is not
properly managed, there is a risk of data loss & Time-
Consuming: Depending on the amount of data, the
conversion process can be time-consuming.

Option 4 : Using the metafile:

 
cc  @ Krushna Chandra Dash   @ Daniel Devadoss  

No labels
```
