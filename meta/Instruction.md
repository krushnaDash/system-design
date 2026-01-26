Create a one pager document for the technical retrospective.

Project name : Unified Reconciliation and Settlement (URS)

Project details :
Unified Reconciliation and Settlement (URS) is Walmart's enterprise-wide system that unifies payment settlement, reconciliation, and financial reporting across all retail channels (stores, e-commerce, and international banners).

Today, Walmart maintains separate settlement systems for physical stores versus online, resulting in duplicated costs, slower time-to-market for new payment processors, and inconsistent reconciliation processes. URS consolidates these into a single event-driven platform with two loosely coupled components:

A Unified Settlement System that manages batch settlement with third-party processors (Visa, Mastercard, Discover, Synchrony, etc.), and
A Unified Reconciliation System that ensures 100% accuracy by matching authorization records, sales orders, and general ledger postings within 24 hours of settlement, automatically resolving exceptions via configurable business rules.
The system delivers transformational business value by enabling configuration-based onboarding of new payment processors (reducing time-to-market from months to days), providing complete end-to-end transaction traceability for audit and SOX compliance, automating manual reconciliation processes, and empowering business teams with self-service analytics and dashboards.

By capturing detailed transaction lifecycle data across all channels—from authorization through settlement, funding, and chargeback—URS creates a unified financial intelligence platform that supports enterprise-wide payment analytics, Treasury's expansion into new payment methods, and strategic decision-making while maintaining rigorous security (PCI tokenization), regulatory compliance, and 7-year audit trails.

Goals
Eliminate duplicate settlement/reconciliation systems across stores and e-commerce, create a unified platform with best features from both, accelerate new tender onboarding, and reduce unexplained GL imbalances.
Deliver improved business and retail customer experiences, modern secure products that empower treasury teams, and seamless integration for settlement system consumers.


Here is the complete story about the URS project : 

How it is started : Business noticed the gap between stores and e-commerce in terms of settlement and reconciliation. For the .com slaes which is just 30 % of total sleas, the out of balance amount is $ 150 million and store is $ 50 million. Aprat form this for stores system is capable of highilighing which order and which payment id causing the out of balance, but for the .com it is not possible to find out which order and which payment id causing the out of balance, this becuase the .com system doing reconcialling at the payement provider tender level with simple job called SHipped not bill, this JOB process the aggragted data from BigQuery for accouting at each payement provider level and do the reconcialling, by checking the total credited amount to the walmart bank account.

The store system does the reconciliation at the order level for each payment id it will check the order level data and do the reconciliation, if the order is not reconciled then it will highlight the order and the payment id causing the out of balance.

Which means for the store system we have answer on which all credit card/tender we could not capture the fund and what happened to the fund.

With this problem Business asked to build a unified system for both stores and .com to have a single view of the reconciliation and settlement and take the store software system to support both store and .com. orders and build a unfied reconciliation and settlement system.


Technical challenges : 

The store system reconile engine process the  Order from CTH, accouting infromation BUA and payment provider infromation UPP. and all the system have the order_id and payemtn_id for each payment method.

Its uages the a staemet machine for each txn to do the reconciliation. The actor are created with a order_id and payment_id and it will do the reconciliation for each payment method.

As mention above for the .com system it is doing the reconciliation at the payement provider level with simple job called SHipped not bill, this JOB process the aggragted data from BigQuery for accouting at each payement provider level and do the reconcialling, by checking the total credited amount to the walmart bank account.


Now the challenge is to do the reconciliation at the order/Invoice level for each payment method for the .com system.

The order lifecycle is as follows in .com is very complex and all the upstrem does not prosess the same set of minimum keys like order_id, invoice_id, payment_id etc.

To make current system work for .com I need to build a state machine which can process the orders from any system.

That how the State machine v2 is built, where one actor is created for each order.


Credit card receivable :  include the total amount daywise

Pyament provider : Fiserv North and ByPass (Visa and Master card) 
                   AMEX Batch
                   Chase
                   FIS
                   Discover
                   Synchrony
                   PayPal

What is out of balance : Out of balance is the difference between the amount of money that is accounted in the general ledger and the amount of money that is actually received in the bank account.

