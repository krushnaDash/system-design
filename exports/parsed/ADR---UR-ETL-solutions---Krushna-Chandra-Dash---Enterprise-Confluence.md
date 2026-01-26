# ADR   UR ETL solutions   Krushna Chandra Dash   Enterprise Confluence

```
Link to Confluence's data policy. FY26-Q3: Roadmap - link.

Team and Personal spaces which are not classified will default to Private starting Oct 7, 2025

REST API Authentication is changing, API Tokens will be the only supported method for API calls. Migrate now to avoid disruption See details.

ADR - UR ETL solutions

Created by Krushna Chandra Dash on Sep 10, 2025

Requirements:

Below are the requirements for UR, which needs some ETL solutions.

1. Take data from the operational DB like cosmos, Azure SQL, PostgreSQL to Bigquery for analytics purpose and from Bigquery to DB2 for the legecy system to work
2. Run differnt reporting, busines rule for alert and process the differnt input files from upstream like Epay and FDF

For the first type of ETL jobs, which involve moving large amounts of data, we have chosen UDP. UDP uses Spark internally to handle these large-scale data transfers efficiently.For
the second type of ETL jobs, which deal with smaller amounts of data, using UDP would be over-engineered and not cost-effective. These jobs do not require data processing tools like
Spark. Therefore, we are designing a custom ETL solution for these smaller data transfers.

Previous experiance with UDP for running small and simple ETL jobs

There was no built-in means to assess the data's sanity or quality as the job progressed, which is being tweaked as per our requirement.
There is no out-of-box retry mechanism, resulting in a continuous process that must be actively watched.
Around $300 per day for running 90 simple ETL jobs with a total data volume of less than 10GB.
The error rate was remarkably high at 67% per month as each of the components is managed by a different vendor and solutions integrate them into one box. If one component
has updated and other are not coordinated, then there is high
possibility that feature breaks.
Lack of customization leads to the running of duplicate jobs for different destinations, increasing cloud costs and requiring extra monitoring effort.
With all the issues, there was a pressing need to create a new ETL solution to meet our business goals and address them.
As a result, the business need is to have a lightweight, cloud-native, dependable, cost-effective, and highly customizable ETL solution that can process data from various
sources and write to multiple destination.

Development and design of ur-etls-job

The ur-etl-jobs (https://gecgithub01.walmart.com/FRE-STFC/ur-etl-jobs) is the core of ETL application. This design considers the following functional design aspects. One instance of
the application can process only one ETL job at a time. Data sanity tests can be configured as a post-process setting in the ETL workflow. The strategy design pattern was used to
create this application, which aids in the selection of the appropriate algorithm or worker class during runtime dependent on the configuration. The application will have multiple readers
and writers' classes that are responsible for reading and writing data to multiple sources and destinations. Along with this, the application has multiple transformation classes that can
be configured if there is a transformation needed to be done. We have developed custom integrator with source and destination. We have kept it native so that data read and write will
be fast.

To run an ETL job, a user needs to submit a configuration file that has sources and destinations, as well as reader and writer mapper classes. The application then reads the
configuration and initializes different readers and writer’s classes to do the ETL jobs.

Platfrom to run the ur-etls-job

The first choice to run any schdule jobs is WCNP cron job. WCNP recommended using of WCNP cron job if you want to execute short-lived processes like ETL jobs. The problem with
WCNP cron jobs is that they can't be invoked on demand. This means it will be a manual process for the below problems.

Rerunning failed jobs
Triggering a JOB only when certain conditions are met.
Orchestrate the job flows
Event-based trigger of jobs.
Dynamic pod size with run-time arguments

To solve the above problem which has with WCNP cron jobs, we need to look for alternate solution and we came across  WCNP Kubie. We did a copule of POC and explore the
Qubie and below are limitation of Kubie.

 Quibe can not run multiple instance of same job with different env arguments, it's desingn to run one after another
 Kubie API does not provide the status of the orginal josb which passed or falied  example : With Kubie API, for all flow triggers we are getting 200 response but job is not
created in WCNP if same flow is already running. we are expecting error response during this scenario.
Kubie does support of having dydnamic POD size based on the input data volume.

Ticket creted with Kubie team


STRAPPSRV-4076 - Jira issue doesn't exist or you don't have permission to view it.

Since WCNP cron or kubie job are not fullfilling our requirements, we started desing of custom solutions which consist of development of below applications.

1. The microservice which can invoke the ur-etls-job by allocating H/W resources like CPU (Central Processing Unit) and memory, called ur-run-job :

https://gecgithub01.walmart.com/FRE-STFC/ur-run-job

2. The Scheduler job, which takes care of monitoring and deciding when and how to trigger an ETL job called "ur-scheduler" : https://gecgithub01.walmart.com/FRE-STFC/ur-

scheduler

3. The custom helm chart which provide capbility to ur-etls-job to trigger a WCNP cron job on demand with override of env variable and POD size :

https://gecgithub01.walmart.com/FRE-STFC/ur-helm-chart

Development and design ur-run-job

Development of ur-run-job was needed to run the ur-etls-job application in a container. To run multiple ETL jobs simultaneously, we need to have multiple PODs of varied sizes to
process each ETL job independently. The ur-run-job service exposes APIs (application programming interfaces) to trigger an ETL job by specifying the POD size and run time details.
ur-run-job makes use of k8s APIs to generate POD and run the ur-etls batch job for ETL. This service helps us to create a POD of the exact size based on the ETL type to save cloud
costs.

Development of ur-scheduler

Now we have an ETL application that can run an ETL job based on configuration, and we have a service called ur-run-job that has APIs to invoke an ETL job in the cloud. But the
problem is that we need an automated solution that triggers the ETL jobs and monitors them. If there is a failure, it will even retry to run the job till the retry limit. So, we developed ur-
scheduler. It runs as a batch job, has different schedulers, and monitor jobs for different ETL needs from the business. The ur-scheduler monitors the source system and triggers the
ETL jobs and monitors running jobs and updates pass/fail status in the audit log based on the job exit codes. ur-scheduler maintains all details of each ETL job in an audit log table,
which helps maintain details of each ETL job and check its status.

Architecture

Source system

monitor

ur-schedule

Submit Job Request
REST call

GSLB routing

WCNP cluster-1

Node1

Pod1

ur-run-job

Pod3

UR ETL Job

Pod2

Pod20

UR ETL Job

UR ETL Job

WCNP cluster-2

Node1

Pod1

Pod3

UR ETL Job

ur-run-job

Pod2

UR ETL Job

No labels
```
