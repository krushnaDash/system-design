# Behavioral
### Additional STAR from Unified Reconciliation (UR) State Machine v2

 - Driving Results — UR State Machine v2 Adoption and POC
   - S: Needed to extend store-only reconciliation to .com with additional keys while keeping reliability and cost in check; legacy projections unstable.
   - T: Deliver a new state machine architecture and persistence approach that scales and is operable; gain cross-org approval.
   - A: Proposed single-actor-per-order model; ran POC with Akka + R2DBC Postgres data partitioning; documented trade-offs vs Cassandra; coordinated Lightbend review and design sign-off. Conducted load test on RDS db.m5d.2xlarge and EKS 5× m5.xlarge.
   - R: Sustained ~20,283 req/s over 1M requests across 2,000 entities (avg 484 ms; p95 under 2.85 s); design approved by Lightbend; roadmap to migrate AKKA→PEKKO; clear owner assignments and MoM.
   - L: For cross-org platform changes, measurable prototypes and external validation (e.g., vendor/consultant review) accelerate alignment and de-risk migration decisions.

 - Embracing Ambiguity — Keys and Upstream Variability
   - S: .com flows lacked consistent key sets; multiple upstreams with partial identifiers.
   - T: Ensure determinism and correctness in entity routing and state transitions.
   - A: Evaluated options (schema evolution + one-time migration vs dual-version vs order-level actor). Selected order-level actor with invoice-level state to reduce actor cardinality and preserve full order context.
   - R: Simplified routing (order key) while preserving detailed invoice state; recommended approach endorsed by external consultants; POC code published.
   - L: When upstreams have inconsistent identifiers, designing around a stable primary key with progressive enrichment avoids brittle coupling and reduces long-term complexity.

 - Growing Continuously — Fixing Projection Issues and Evolving Stack
   - S: Existing projection pipeline had reliability issues, raising operational risk.
   - T: Stabilize projections and improve operability without overhauling business logic.
   - A: Switched to Akka Persistence R2DBC with partitioning, introduced Akka Projection to SQL, planned migration from AKKA to PEKKO after feature parity.
   - R: Projection reliability improved; clearer failover guidance documented; reduced ops overhead vs Cassandra while keeping scale path via partitioned RDBs.
   - L: Operational simplicity is a first-class design goal—choosing simpler primitives with a clear scale-out story (partitioning) reduces incident load and improves delivery velocity.

Artifacts
- UR State machine Design (PDF/MD): exports/pdf/UR-State-machine-Design---Krushna-Chandra-Dash---Enterprise-Confluence.pdf, exports/parsed/UR-State-machine-Design---Krushna-Chandra-Dash---Enterprise-Confluence.md
- UR State Machine Flat/Comm Design: exports/pdf/UR-State-Machine-Flat-Design---Krushna-Chandra-Dash---Enterprise-Confluence.pdf, exports/pdf/UR-State-machine-communication-design---Krushna-Chandra-Dash---Enterprise-Confluence.pdf
- C4 Diagram: exports/pdf/Unified-Reconciliation---C4-design-Diagram---Krushna-Chandra-Dash---Enterprise-Confluence.pdf
- POC Repo: https://gecgithub01.walmart.com/FRE-STFC/ur-statemanager


You'll be meeting with an Engineering Leader who will be interested in learning about your choices and hopes for your career (trajectory), where your passions are in technology, desire for impact, why Meta, and possibly things you'd change/improve about Meta. The purpose of every question is to assess your motivations, vision for past/future work, skills, professional maturity, communication style and strengths and weaknesses in working within organizations.

Please explain the situation, what you did, what you would do differently, what you learned, etc.
* If relevant, it can be helpful to explain company culture and what was expected of you
* Understanding motivations for an individual/team/organization as well as both sides of a situation is ideal
* Understanding your own biases in a situation and how it impacts decision making and conflict resolution is also beneficial
* Applying a previous lesson you have learned is recommended

The team tends to appreciate the following areas as general themes in your answers: intrinsic motivation, empathy, being proactive, working in unstructured environments, conflict resolution, growth/reflection, and strong communication.

Sample questions:
1. Tell me about a time you were wrong and how you handled it
2. Tell me about a time you had to give/received difficult feedback
3. Tell me about a conflict and how it was resolved

---

## Round Summary
The behavioral framework emphasized five areas: driving results, resolving conflict, embracing ambiguity, growing continuously, and communicating effectively. Strong answers were structured, concise, data-informed, and demonstrated empathy, collaboration, and reflection.

## Questions Asked
Examples include: driving measurable results amidst roadblocks; resolving complex, large-scale conflicts; operating in ambiguity and driving clarity; learning from mistakes and responding to tough feedback; and demonstrating effective, adaptive communication.

## STAR Examples (Situation, Task, Action, Result)
 - Driving Results — Image Translation for Product Images
   - S: Product images contain embedded text requiring translation with style preservation.
   - T: Deliver scalable solution with measurable business impact.
   - A: Led ML solution combining LLM + RAG; identified what not to translate; handled short/ungrammatical text; font/fit handling for longer translations; secured VP buy-in with 50% prototype success; partnered with imaging team to adjust infra; validated demand via brand survey.
   - R: Launched cross-org project (grew from 2-person hackathon to 30 contributors over ~18 months); AB tests projected ~$1B sales uplift.
   - L: Early prototypes plus explicit business validation (surveys/AB tests) are critical to convert technical demos into funded, cross-org roadmaps.

 - Resolving Conflict — Challenging ROI Claim
   - S: Proposal claimed ~$500M impact with weak estimation methodology.
   - T: Ensure rigor without alienating partners.
   - A: Met TPM, offered collaboration; persisted despite pushback; ran A/B testing to produce reliable numbers; communicated empathetically while advocating for better measurement.
   - R: Measurement rigor adopted org-wide; stronger relationships; example of influence without escalation.
   - L: The most scalable conflict resolution combines empathy with shared facts—experiments/measurement frameworks turn debate into collaboration.

 - Embracing Ambiguity — QA Resource Attrition
   - S: Human QA for top sellers stalled due to attrition; risk of slip to next year.
   - T: Deliver something meaningful within constraints and deadlines.
   - A: Proposed stripped-down plan with shorter timeline; convinced director to invest; executed experiments; adapted to schedule slip (~1 month) while meeting holiday code-freeze constraints.
   - R: Successful outcome informed next year’s iteration; demonstrated flexibility and resilience.
   - L: In ambiguity, the best lever is reframing scope into an executable plan with clear trade-offs and decision points for stakeholders.

 - Growing Continuously — Feedback on Forum Choice
   - S: Feedback that raising critical issues in broad meetings caused anxiety for junior devs.
   - T: Maintain transparency while reducing unnecessary panic.
   - A: Shifted to 1:1s with decision-makers; brought outcomes back to the wider group; reflected on trade-offs.
   - R: Improved communication efficacy and stakeholder confidence; reinforced growth mindset and coaching others.
   - L: Communication channels are part of engineering effectiveness—choosing the right forum preserves psychological safety without sacrificing transparency.

 - Communicating Effectively — Interview Signals
   - S: Need to show structured, concise, yet detailed communication and active listening.
   - A: Use multiple channels (1:1s, team meetings, docs, code reviews); structure examples; leave space for questions; validate assumptions.
   - R: Clear, precise answers; strong rapport; thoughtful closing questions.
   - L: Strong communication is both content and pacing—structure answers to leave room for questions and validate assumptions early.

## What Went Well
 - Clear use of data and measurable outcomes.
 - Empathetic conflict resolution with collaborative win-win orientation.
 - Converting ambiguity into clarity and delivery plans.
 - Rapid learning loop and adjusting communication style based on feedback.
 - Strong structure and concision with space for interviewer interaction.

## Improvements
 - Continue tightening STAR with explicit metrics and baselines.
 - Proactively call out trade-offs and alternatives explored.
 - Where applicable, add more cross-team context and stakeholder mapping.

## Follow-ups
 - Prepare 7–10 STAR+L examples covering the five areas; ensure multiple data-backed results stories.
 - Draft succinct write-ups emphasizing empathy, collaboration, and measurable impact.
 - Identify artifacts: PRDs, docs, dashboards, experiment results that support claims.

