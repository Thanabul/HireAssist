# ADR-001: Capability-aligned service decomposition behind an API gateway

**Date:** 2026-09-11
**Deciders:** Patiphon Puntusin, Thanabul Parodom, Thanwarat Korcharoenkiat, Rerngrit Jangsri

> In the context of building HireAssist as a set of microservices, facing three workloads that
> differ in who triggers them, how long they may take, and what data they own, we decided to
> split the system into five services behind a single API gateway — drawing the boundaries by
> capability rather than by technical layer — to achieve independent scaling of the screening
> workload and a single enforcement point for workspace isolation, accepting that data
> ownership is now distributed and that erasure and reporting must cross service boundaries.

---

## Summary

### Issue

HireAssist has to be decomposed before anything else can be designed: the message broker, the
datastores and the LLM integration all sit at boundaries that do not exist until the boundaries
are drawn. The course requires microservices with REST, gRPC and a message broker, an API
gateway, and a documented approach to service discovery — but those are constraints on the
answer, not reasons for one. The forces that actually shape the split are these:

**UC-2 contains two workloads that do not belong in the same process.** Accepting a batch of
resumes is a fast, interactive request that must return in milliseconds. Screening one of those
resumes is parsing plus one or more LLM calls — seconds normally, minutes for a long file, and
occasionally never, when the model provider is rate-limiting or down. If the same process serves
both, the recruiter-facing API inherits the latency and the availability of the slowest external
dependency in the system.

**UC-4 and UC-5 are the only clock-driven behaviours, and UC-5 is destructive.** Retention
enforcement deletes candidate data wherever it lives and must produce an audit trail proving it
did. That is a very different responsibility from serving a recruiter's screen, it runs when
nobody is watching, and it needs an owner that can be reasoned about on its own — a PDPA
obligation with no clear home is a PDPA obligation nobody implements.

**Every use case reads and writes personal data scoped to one workspace.** Tenant isolation is
the one rule that must never be violated, and a rule enforced in five places is a rule enforced
in four places plus a bug.

**The team is four students learning this stack while building it.** Every service costs a
deployment, a pipeline, a schema, a set of logs to correlate, and a place for a bug to hide.
Over-decomposition is not a theoretical risk here; it is the most likely way this project fails
to ship.

### Decision

HireAssist is five services and one gateway, aligned to capabilities:

| Service | Owns | Serves |
|---|---|---|
| **API Gateway** | No domain data | Single public entry point. Terminates TLS, validates the session token, resolves workspace and role, applies rate limiting, routes to services. |
| **Identity & Workspace Service** | Accounts, workspaces, memberships, roles, sessions | UC-0 |
| **Hiring Service** | Job openings, criteria, screening batches, decisions, interview guides | UC-1, UC-2, UC-3 |
| **Resume Processing Service** | Candidate profiles, parsed resume text | UC-2 (the per-resume work) |
| **AI Service** | Prompts and the model credential — no domain data | UC-1, UC-2, UC-3 |
| **Compliance & Insights Service** | Retention policy, pipeline metrics, audit log | UC-4, UC-5 |

**Communication style follows the kind of conversation that crosses each boundary:**

- **Client → Gateway → Identity / Hiring / Compliance: REST over HTTP/JSON.** These calls are
  browser-facing and public. REST is readable in a browser's network tab, needs no client
  toolchain, and is what a front-end developer on a four-person team can debug without help.
- **Hiring and Resume Processing → AI Service: gRPC.** This is a high-volume internal call on a
  contract that must not drift: *(candidate profile, criteria) → (score, must-have check,
  justification)*. Protobuf makes that contract explicit and versioned instead of leaving it to
  a hand-written JSON convention, the generated Go clients remove a class of integration bug,
  and server streaming lets a long guide or a batch of scores arrive incrementally.
- **Hiring → Resume Processing, and domain events → Compliance & Insights: RabbitMQ.** Screening
  work is queued rather than called; see [ADR-002](ADR-002-async-screening-pipeline.md).

**Service discovery is Kubernetes.** Each service is a Deployment fronted by a ClusterIP
Service; services address each other by in-cluster DNS name (`ai-service.hireassist.svc`), and
kube-proxy load-balances across the healthy Pods behind it. Readiness probes decide which Pods
are in that set, so discovery and health checking are the same mechanism rather than two systems
that can disagree. No separate service registry (Consul, Eureka) is deployed.

### Status

**Accepted**

### Group

Decomposition · Communication

---

## Details

### Assumptions

- Go is the backend language for all services. gRPC, protobuf and the Kubernetes client are
  first-class there, and a single language keeps four students able to read each other's code.
- The system is deployed to Kubernetes — a managed cluster or a local one (kind/minikube) for
  the demo. This is an assumption worth re-checking: if the team cannot get a cluster running
  early, discovery has to be reconsidered, because everything here depends on it.
- Expected load is one workspace's hiring, not a public site: tens of concurrent recruiters,
  batches of 20–200 resumes. Nothing here is sized for internet-scale traffic.
- Each service is operated by the same four people. There is no platform team, so operational
  weight is paid by the same students writing the features.

### Constraints

- The course requires at least one REST service, at least one gRPC service, at least one service
  using a message broker, an API gateway, and a documented service discovery approach
  (`docs/course/REQUIREMENTS.md`). A decomposition that does not exercise all three
  communication styles is not acceptable regardless of its other merits.
- PDPA makes personal data location a design concern: the fewer services that hold resume
  content, the smaller the surface that retention, access control and breach response must cover.

### Positions

1. **Modular monolith plus one background worker.** Two deployables, one schema, no network
   between the parts. Genuinely the least work, and for a system this size it would be a
   defensible production choice.
2. **One service per use case** — Identity, Job, Screening, Parsing, Scoring, Interview,
   Dashboard, Retention: eight services.
3. **Decomposition by technical layer** — an API service, a parsing service, a scoring service,
   a persistence service.
4. **The chosen split, but with the AI Service merged into Resume Processing.** Four services
   instead of five; the LLM lives where most of the LLM work happens.
5. **The chosen split, but with UC-4/UC-5 folded into Hiring Service.** Compliance is small; a
   scheduler inside Hiring would run it.
6. **Consul as a service registry on Docker Compose**, instead of Kubernetes DNS.

### Argument

**Against the monolith (1):** it fails the course requirement outright — there is no boundary
across which gRPC or a broker would be anything but ceremony. Independently of the course, it
also puts the recruiter-facing API in the same process as work that blocks on an external model;
an LLM outage would degrade sign-in and the dashboard, which are otherwise unaffected.

**Against one service per use case (2):** UC-1, UC-2 and UC-3 are three views of the same two
aggregates — the Job Opening and the Candidate Profile. Splitting them puts a network call and
an eventual-consistency problem between "the criteria" and "the score against the criteria", and
buys nothing: they are deployed together, changed together, and scale together. The cost is real
and immediate — eight pipelines, eight sets of logs, eight schemas — and the benefit is
hypothetical.

**Against layered services (3):** a layer is not a capability. Adding one field to a criterion
would touch the API service, the scoring service and the persistence service; every change
becomes a coordinated three-service release. This is the decomposition that looks organised on a
diagram and behaves worst in practice.

**Against merging the AI Service (4):** UC-1 extracts criteria from a paragraph the recruiter is
watching, and UC-3 writes an interview guide on demand. Both are interactive; neither is batch
work. Merging would either route interactive calls through a batch worker or duplicate prompt
and credential handling in two codebases. Keeping every model call behind one service is also
what makes [ADR-004](ADR-004-llm-access.md) implementable: one place holds the credential, one
place caps spending, one place changes when the provider changes.

**Against folding compliance into Hiring (5):** it is small today, and would grow into the same
service that serves recruiter traffic — meaning a retention sweep and a recruiter's dashboard
request compete for the same process. More importantly, UC-5 needs to be auditable in isolation:
"which component may delete candidate data?" should have a one-word answer.

**Against Consul on Compose (6):** it means running and explaining a second discovery mechanism
when the deployment platform already provides one, and it puts registration in application code,
where a service that crashes without deregistering leaves a stale entry. Kubernetes derives the
same information from readiness probes it is already running. The cost is that the team must
learn Kubernetes — which is the honest downside, recorded below.

**The positive argument for the split we chose:** the three boundaries fall where three
properties genuinely differ.

- *Who triggers the work* — a human (Hiring, Identity), a queued message (Resume Processing), or
  the clock (Compliance & Insights).
- *How long it may take* — milliseconds, minutes, or as long as a sweep of the talent pool takes.
- *What it owns* — the transactional hiring record, the derived candidate profile, or the
  retention policy and audit log.

A boundary that separates two things differing on all three axes is a boundary that will still
be in the right place in six months.

### Implications

**What this buys us**

- The screening workload scales by adding Resume Processing replicas without touching the
  recruiter-facing API — which is NFR-07, the quality attribute the project demonstrates, and the
  path the course's load tests will exercise.
- The gateway is the single place where a request is bound to a workspace and a role, so tenant
  isolation is enforced structurally rather than by convention in five codebases.
- The AI Service is the entire blast radius of the model credential and the entire cost centre
  for tokens, which is what makes the provider a configuration choice rather than a rewrite.
- Scoring stays a separable *(profile, criteria)* behaviour reachable by any caller, which is the
  property the deferred D-1 re-matching use case depends on.

**What it costs us**

- **UC-5 must erase data it does not own.** Compliance & Insights holds the policy but candidate
  data lives in Hiring and Resume Processing, so erasure becomes a multi-service protocol with a
  verification step. "Deleted" is now eventually consistent — precisely the property a regulator
  asks about, and the architectural cause of UC-5's *deletion pending* state (alternate flow 5b).
- **UC-4's dashboard cannot be a query.** Metrics span services, so Compliance & Insights must
  maintain them incrementally from domain events rather than joining tables. Numbers on the
  dashboard can therefore lag reality, and a lost event means a permanently wrong count unless
  there is a reconciliation path.
- **No distributed transactions.** A batch accepted by Hiring whose messages are never consumed
  is inconsistent state that nothing detects on its own; a reconciliation sweep is now a
  requirement, not a nicety.
- **Workspace identity must travel on every internal call**, including broker messages. If the
  gateway is the only place that checks, an internal caller with a wrong workspace ID silently
  reads another company's candidates. Every gRPC and message contract needs the field, and the
  services need to enforce it, not merely receive it.
- **The team now has to learn Kubernetes** on top of Go, protobuf and RabbitMQ. This is the
  largest schedule risk this ADR creates, and it lands on all four members.
- **Six deployables plus PostgreSQL, MongoDB and RabbitMQ is heavy for a laptop.** Local
  development needs resource limits and probably a reduced profile, or the demo machine becomes
  the constraint on what can be shown.

---

## Related

### Related decisions

- [ADR-002](ADR-002-async-screening-pipeline.md) — the Hiring → Resume Processing boundary
  created here is the one the screening queue crosses.
- [ADR-003](ADR-003-polyglot-persistence.md) — per-service data ownership assumed here is what
  makes the PostgreSQL/MongoDB split enforceable.
- [ADR-004](ADR-004-llm-access.md) — depends on the AI Service existing as a separate service.

### Related requirements

- **Use cases:** UC-0 (Identity & Workspace Service, gateway authorisation), UC-1/UC-2/UC-3
  (Hiring Service, AI Service, Resume Processing Service), UC-4/UC-5 (Compliance & Insights
  Service). D-1 remains reachable because scoring is a service operation, not a step inside a
  batch.
- **Course requirements** (`docs/course/REQUIREMENTS.md`): REST — gateway to Identity, Hiring and
  Compliance; gRPC — to the AI Service; message broker — Hiring to Resume Processing and domain
  events to Compliance; API gateway — the gateway service; service discovery — Kubernetes
  Services and in-cluster DNS, described above.
- **Functional and non-functional requirements** (`docs/FUNCTIONAL-REQUIREMENTS.md`,
  `docs/NON-FUNCTIONAL-REQUIREMENTS.md`): FR-0.3 and FR-0.6 — workspace scoping and role
  enforcement, bound to the request at the gateway; NFR-04 and NFR-07 — the interactive path
  acknowledges a batch in seconds while the screening workload scales by adding Resume Processing
  replicas, which is the demonstrated quality attribute; NFR-10 — no failure in the batch path may
  lose accepted work or take the interactive path down with it; NFR-17 — the scoring model and
  prompt change inside the AI Service alone; FR-5.5 and FR-5.11 — erasure must reach every
  service holding candidate data, which this decomposition turns into a cross-service protocol.

### Related artifacts

`docs/PROPOSAL.md` — the ADR summary section and the Non-functional Requirements section, once
written. The architecture diagram and the Service–Operations–Collaborators table required for
the *Microservice Design with Collaborations* deliverable are both derived directly from this
decomposition.

### Related principles

- *The human still decides* — the gateway and Identity Service exist so that the decision-maker
  is always an identified person in a known workspace.
- *Easily reversible* — merging two of these services later is a refactor; splitting a monolith
  later is a project.

---

## Notes

The strongest argument raised against this ADR was that the modular monolith (position 1) is the
better engineering choice for a system this size, and that we are decomposing because the course
requires it. That is partly true and worth recording honestly: with no course constraint we would
likely have started with two deployables and split when a boundary hurt. What survives the
constraint is the *shape* of the split — the boundaries above are the ones we would have arrived
at anyway, because they follow trigger, latency and ownership rather than the requirement to have
three protocols.

We also considered titling this record "decomposition and communication", then split the
communication decision out to keep one decision per ADR — and put it back, because the protocols
here are not an independent choice. Each boundary's style was determined by what crosses it, so
recording them apart would have meant repeating the boundary rationale twice.

The service owning UC-4 and UC-5 was referred to as *Insights & Notifications* in the changelog
entry that reconciled the requirements, before this record existed. It is named **Compliance &
Insights** here because retention ownership is its defining responsibility — "which component may
delete candidate data?" is the question it exists to answer — and because notifications are not a
service: each event's owner emits its own (FR-2.12 from Hiring, FR-4.4 and FR-5.3 from Compliance
& Insights). A shared notification *channel* may exist later; it would be infrastructure, not a
boundary.
