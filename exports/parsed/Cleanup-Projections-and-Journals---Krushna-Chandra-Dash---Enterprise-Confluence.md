# Cleanup Projections and Journals   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid
disruption See details.

Cleanup Projections and Journals

Created by Krushna Chandra Dash on Sep 10, 2025

Cleanup mark as delete transactions from projections tables.

Tables : settlement_details,accounting,auth,tender

Cleanup Before :  7 Days

ETL Time : 1 AM GMT

Cleanup reconciled transactions from projections tables.

Tables : settlement_details,accounting,auth,tender,invoice

Cleanup Before :  2 Months

ETL time : 2 AM GMT

Cleanup Journal from Journals Table

Tables : event_journals

Cleanup Before : 90 Days

Details : Pull reconciled details from Tender table and run r2dbc cleanup api to clean the persistence ids.

ETL Time : 1 AM GMT

No labels
```
