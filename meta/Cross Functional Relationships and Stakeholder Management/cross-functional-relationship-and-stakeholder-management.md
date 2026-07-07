# Cross-Functional Relationship and Stakeholder Management

Discussion-based interview to assess how you grow and foster cross functional partnerships. Expect questions on managing competing interests across organizations and aligning on shared impact.

Guidance:
* Have an example of a partnership that didn’t go well and how you would improve it
* Alternatively, a partnership that did go well, but areas that could have been better

---

## Round Summary
Assesses relationship building, conflict resolution, influencing without authority, and collaborating across orgs with differing goals and context. E7 signal emphasizes operating beyond team boundaries, securing buy-in from unfamiliar partners, and sustaining multi-team initiatives.

## Scenarios Discussed
- Deep domain collaboration across Search and Ads orgs at Google and Apple; trusted technical partner among long-tenured experts.
- Handling pushback from senior leads while maintaining backbone and constructive tone.
- Multi-team collaboration across research and infra with differing backgrounds and incentives.

UR program examples (from Confluence exports):
- Lightbend design review and approval for UR State Machine v2 (single actor at order level) with follow-up action items and MoM.
- Coordination across BUA, CTH, OMS, PLUTUS, UPP, FDF to align on identifiers, message schemas, and state transitions.
- Joint decision to adopt Akka Persistence R2DBC (Postgres) over Cassandra for projection reliability and cost; planned AKKA→PEKKO migration post feature readiness.

## Challenges and Trade-offs
- Navigating specialized domains where influence is predicated on technical credibility vs. broad org influence.
- Balancing data-driven decisions with interpersonal techniques when data alone is insufficient.
- Reconciling different org priorities and timelines while driving a common roadmap.

## Strategies and Tactics
- Lead with expertise and empathy; validate partner constraints before proposing solutions.
- Use experiments/A-B tests to ground decisions and reduce contention.
- Operate in consultant mode for resistant partners (e.g., YouTube) by enabling them to implement solutions themselves.
- Build long-term trust via consistent wins and transparent communication.
Specific tactics applied in UR:
- Produced POC code and ran load tests (RDS db.m5d.2xlarge; EKS 5× m5.xlarge) to de-risk; shared evidence (~20,283 req/s over 1M requests across 2,000 entities).
- Captured decisions and responsibilities via MoM; assigned owners (e.g., projections fix vs new SM v2 feature work).
- Socialized C4 and state diagrams to align on boundaries and data/flow contracts.

## Outcomes and Impact
- Drove collaboration across multiple teams; secured support for V1 with fixed time/budget, iterated post results.
- Established measurement rigor to avoid overstated impact claims.
- Built reputation as a go-to expert enabling adoption across org boundaries.
UR program outcomes:
- Design sign-off from Lightbend; convergence on order-level actor strategy and R2DBC partitioning.
- Stabilized projections path and clearer failover approach; reduced ops burden vs Cassandra.
- Shared source of truth with artifacts (C4, state diagrams, comms design) and repository links.

## What Went Well
- Clear, concise, enthusiastic communication; validated assumptions and adjusted scope as needed.
- Strong relationships with peers and leads; effective handling of pushback.
- Persistence and adaptability in difficult org setups.

## Improvements
- Provide examples where influence relied more on interpersonal strategy (not only data).
- Demonstrate influence beyond narrow expert domains to broader org contexts.
- Strengthen decision records highlighting trade-offs and stakeholder mapping.

## What Could Have Been Better
- Earlier cross-domain E2E testing and shared test catalogs to surface contract gaps sooner across CTH/OMS/UPP/BUA/FDF/PLUTUS/URS.
- A single, always-on pre-prod environment with stable seeded data for continuous end-to-end validation.
- Promote BDD and domain-owned behavior coverage (~100%) with shared specs for reuse across teams.
- Earlier discovery/communication of domain edge cases (e.g., PLUTUS invoices without successful auth do not emit captured events) via contract tests and clear ownership.

## Follow-ups
- Prepare 2–3 cross-org stories with explicit stakeholder maps, conflicts, and resolution techniques used.
- Collect artifacts (experiment plans, measurement frameworks) that show rigor and alignment.
- Identify opportunities to scale influence outside primary domain via frameworks, docs, or enablement programs.
UR artifacts to include:
- PDFs/MDs: exports/pdf/*UR-*.pdf, exports/parsed/*UR-*.md (C4, state machine, communication, flat design, plans, redesign).
- Repo: https://gecgithub01.walmart.com/FRE-STFC/ur-statemanager
- MoM excerpt and owner mapping within UR State machine Design document.

