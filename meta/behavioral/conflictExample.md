## How to handle conflict

- Act with empthy and open mind
- Understand the other side, why they are saying what they are saying
- Try to find common ground
- Be prepared to compromise

## Example Where I was wrong
- BFF pattern for TOR mini apps (solution to use gatways federated capbilty to build BFF)
- Pure outbox pattern vs having hybrid version where we alows the dual write

## Example Where I was right
- Using a SQL database with partitioning to scale out, instead of using NoSQL database
- Doing the data distribution in app layer instead of using the database sharding
- Adding a normilization layer to fan-in and have single kafka topic for all the events, instead of having multiple kafka topics for different events, a service which will read from kafka and write back to kafka.
- Using java as development language instead of using Scala
- Using a single actor per order model instead of using multiple actors per order
- Decision of builing the v2 of state machine, instead adding complexity on existing state machine
- Decision of Taking the data from source of truth system instead of using the database
- Building of the URS project with realtime events.
- Unified system for .com and store
- Using R2DBC for projection instead scala reactive lib 
- Not using JPA for a API which need to pull 10000 of rows and using native query.
- Turning of kafka auto commit 



Write about how you’ve taken the initiative on teams you’ve been a part of. Where have you gone beyond what was expected?
-> Documentation and ADR for each decision with MoM for each meeting
-> Proper agenda for each meeting.
-> Reduce the number of meetings, by trying chat in teams/ creating one pager not work then meeting
-> BDD for each feature, define the feature first and prioritez the E2E testing
-> Cloud cost optimisation from be begining


Write about the managers and coworkers who’ve impacted you the most. Consider also the most difficult work relationships you’ve encountered.

### Managers/Coworkers Who Impacted Me the Most

-> **Lightbend Consultant (External Reviewer for URS)**
   - During the URS state machine v2 design, we engaged Lightbend for an architecture review.
   - Their endorsement of the single-actor-per-order model gave me confidence to push back on internal pressure to use per-tender actors.
   - Key lesson: external validation from domain experts (Akka/Lightbend) accelerates internal alignment and de-risks bold architectural decisions.
   - Impact on me: I now actively seek external expert review for critical design decisions — it's not a sign of weakness, it's leverage.

-> **The EM from BUA Team (Partnership That Could Have Been Better)**
   - When I moved from BUA to URS, I assumed my prior relationship with the BUA team meant I could informally request changes to their system.
   - The EM pushed back: "We don't have bandwidth in Q2." It felt frustrating because I knew the system well.
   - Impact on me: Taught me that relationships don't replace process. Even with strong rapport, I should follow formal intake, engage TPMs, and respect capacity constraints. I now always go through the formal process regardless of how well I know the team.

-> **FDF Team Lead (Most Difficult Work Relationship)**
   - FDF was under a different VP (Fintech vs Transactions). They were not open to publishing individual tender-level accounting events for URS, and were reluctant to even explain how we could get the required data.
   - I tried multiple approaches: direct technical discussions, escalation through my manager, and proposing minimal-effort options for their team.
   - Eventually needed VP-level alignment. Our team built the solution to extract data from FDF BigQuery tables ourselves.
   - Impact on me: Learned that when cross-org incentives are misaligned, no amount of technical persuasion works — you need executive sponsorship AND a fallback plan. I now always prepare a "Plan B we can execute independently" before entering difficult cross-org negotiations.

-> **Senior Dev Who Challenged My Scala Decision**
   - A senior developer on the team strongly advocated for Scala (existing codebase was Scala-heavy). I pushed for Java citing hiring pool, maintainability, and Spring ecosystem.
   - The disagreement was healthy — they raised valid points about Scala's expressiveness for actor patterns.
   - We resolved it by evaluating: team skill distribution, onboarding cost for new hires, and long-term maintainability. Java won on all three.
   - Impact on me: Taught me that the best technical decisions are made with people/org constraints, not just technical merit. I now frame every tech choice with a "who will maintain this in 2 years?" lens.

-> **Feedback on Forum Choice (Manager Who Gave Difficult Feedback)**
   - A manager told me that raising critical architectural issues in broad team meetings was causing anxiety for junior developers.
   - Initially I felt defensive — I valued transparency and thought everyone should hear the risks.
   - I shifted to raising concerns in 1:1s with decision-makers first, then bringing outcomes (not raw problems) to the wider group.
   - Impact on me: Communication channel is as important as the message. Choosing the right forum preserves psychological safety without sacrificing transparency. I now default to "smallest effective audience first."

### Pattern I've Noticed Across These Relationships
- The most impactful people challenged my assumptions (Lightbend, BUA EM, Scala advocate).
- The most difficult relationships had misaligned incentives, not personal conflict (FDF team).
- In every case, the lesson was about process, empathy, or communication — never purely technical.