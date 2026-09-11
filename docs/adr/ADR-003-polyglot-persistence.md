# ADR-003: PostgreSQL as system of record, MongoDB for AI-derived documents

**Date:** 2026-09-11
**Deciders:** Patiphon Puntusin, Thanabul Parodom, Thanwarat Korcharoenkiat, Rerngrit Jangsri

> In the context of storing hiring records alongside data the model derives from resumes, facing
> two kinds of data with opposite needs — one that must never be wrong and one whose shape
> changes every time we improve a prompt — we decided to keep the system of record in PostgreSQL
> and the derived documents in MongoDB, to achieve enforced integrity where PDPA and auditing
> demand it and schema freedom where the model's output evolves, accepting that one candidate's
> data now spans two stores and that every erasure must succeed in both.

---

## Summary

### Issue

The data HireAssist holds splits cleanly in two, and the split is not about volume — it is about
what happens when the data is wrong.

**One half must never be wrong.** Workspace membership and roles decide who may see whose
candidates: the tenancy boundary is a foreign key. A job opening's weighted criteria are what a
score is defensible against; a Decision records a rejection and its reason, and an override
records that a human disagreed with the model. Consent state and the retention policy determine
what the company is lawfully allowed to keep, and the audit log is the evidence it did what it
claims. These are relational, stable, and need constraints, transactions and deliberate
migrations. Losing referential integrity here is not a bug, it is a compliance incident.

**The other half is derived, and its shape is unsettled.** A Candidate Profile parsed from a
resume is deeply nested and extremely sparse — three jobs or eleven, a publications list or
none, skills grouped one way this month and another way next. Scoring output carries per-criterion
sub-scores, a must-have check and a written justification, and its structure will change every
time we improve the prompt. Modelling that relationally means a table per nested collection, a
migration for every prompt change, and a wide row of nullable columns for the fields most
resumes lack.

**PDPA cuts across both.** UC-5 must erase a person from *everywhere* on a schedule, and it
offers two expiry actions — delete outright, or anonymise while preserving the aggregate counts
the UC-4 dashboard is built from. Anonymisation is only clean if the identifying material and the
statistics are separable in the first place.

The course additionally requires at least two database types, one relational and one NoSQL. That
constraint is real, but it is not the reason for the split below, and this record would be a poor
one if it were.

### Decision

**PostgreSQL is the system of record.** It holds everything whose correctness is load-bearing:

- workspaces and users (UC-0); memberships and roles (UC-6)
- job openings and their weighted criteria (UC-1)
- screening batches and the per-resume status of each entry (UC-2)
- decisions — shortlist or reject, with the reason, the AI score and any human override (UC-2)
- candidate identity; consent status with the date the data was collected and the lawful basis
  for processing it (FR-2.11); and the retention anchor date (UC-2, UC-5)
- retention policy per workspace; the append-only erasure audit log, which references a candidate
  only by a pseudonymous identifier and holds no personal data (FR-5.7, FR-5.8); and the access
  audit log NFR-12 requires (UC-5)
- the pipeline counters UC-4 reports from

**MongoDB holds what the model derives.** Documents, read whole, replaced whole:

- the normalised Candidate Profile parsed from a resume
- extracted resume text
- per-criterion scoring output with its evidence, and the written justification — persisted with
  the score rather than regenerated on demand, as NFR-15 requires
- generated interview guides (UC-3)

**Resume files themselves live in object storage** (S3-compatible; MinIO locally), not in either
database. PostgreSQL holds the object key.

**The rule we will apply to future data,** recorded so this boundary does not rot:

> If getting it wrong is a correctness or compliance problem, it goes in PostgreSQL. If the model
> produced it and its shape will change when the model or the prompt changes, it goes in MongoDB.
> Nothing in PostgreSQL may depend on a MongoDB document for its correctness.

**Linking and erasure.** Every MongoDB document carries `workspace_id` and `candidate_id` and is
indexed on both, so retention can delete a person's derived data directly rather than by
traversing relationships. PostgreSQL is authoritative for the existence of a candidate; MongoDB
is authoritative for nothing.

**Ownership follows the service boundary** from [ADR-001](ADR-001-service-decomposition.md): each
service owns its own schema or database and no service reads another's tables. Two services
needing the same fact exchange it as an event, not a join.

### Status

**Accepted**

### Group

Data

---

## Details

### Assumptions

- Data volume is modest — thousands of candidates per workspace, not millions. Neither store is
  chosen for scale; both are chosen for fit.
- Derived documents are read whole and written whole. We never update one field of a profile in
  place, so document semantics lose us nothing.
- MongoDB documents are regenerable from the stored resume file, right up until retention deletes
  that file. After erasure nothing is regenerable, which is the intended behaviour.
- The team can run both stores locally and in the cluster. Two datastores plus a broker plus six
  services is a real load on a development machine.
- Both are open source and free to run for a term project, so licensing does not enter the
  decision.

### Constraints

- The course requires at least two database types, one RDBMS and one NoSQL
  (`docs/course/REQUIREMENTS.md`).
- PDPA requires that erasure be complete and provable, which means every store holding personal
  data must be reachable by the retention process and must appear in the audit trail.
- [ADR-001](ADR-001-service-decomposition.md) fixed per-service data ownership; this decision
  operates inside that.

### Positions

1. **PostgreSQL only, with `jsonb` columns for profiles and scoring output.** One store, one
   transaction, GIN indexes over the document fields.
2. **MongoDB only.** One store, no migrations, everything a document.
3. **PostgreSQL + Redis** as the second database type.
4. **PostgreSQL + Elasticsearch** — profiles indexed for full-text search over the talent pool.
5. **PostgreSQL + MongoDB** (chosen).
6. **One shared database for all services** instead of per-service ownership.

### Argument

**PostgreSQL-only with `jsonb` (1) is the position that deserved the most argument,** because it
is genuinely strong: schema freedom without a second store, real transactions across the record
and the derived data, one backup, one set of credentials, one thing to learn. It was rejected on
three grounds, only one of which is the course requirement.

The architectural reason is UC-5's *anonymise* action. When a candidate's retention expires and
the policy says anonymise rather than delete, the company keeps the hiring statistics and destroys
the person. If the identifying material lives inside `jsonb` columns on the same rows as the
counts, anonymisation becomes a careful surgical rewrite of every row — the kind of operation that
is one missed column away from a compliance failure. With the derived documents in a separate
store, anonymisation is *drop this candidate's documents, keep the rows*: coarse, verifiable, and
easy to prove to a regulator.

The second reason is operational blast radius: the scoring output is the part of the system that
will change shape most often and be rewritten most carelessly, and keeping it out of the database
that holds consent and the audit log means an experiment with the parser cannot take a lock on,
or bloat, the table that proves we complied with the law.

The third reason is the course requirement, and it is listed third deliberately. Had it not
existed, position 1 would have been a defensible choice and we would have had a harder argument.

**MongoDB-only (2)** fails in the opposite direction. Consent state, membership, retention policy
and the audit log are precisely the data that must not drift, and we would be hand-rolling
referential integrity and cross-document transactions in the one area where being wrong is
expensive. Multi-document transactions exist in MongoDB, but choosing a store whose defaults work
against the guarantee you most need is a poor trade.

**PostgreSQL + Redis (3)** was rejected because Redis is a cache, not a store. Using it as the
system's second database type would mean either treating a cache as durable — the classic way to
lose data quietly — or nominating a "second database" that holds nothing anyone would miss. We may
well add Redis later as a cache in front of the AI Service ([ADR-004](ADR-004-llm-access.md)); that
is not this decision and would not change this one.

**PostgreSQL + Elasticsearch (4)** solves a problem we have deferred. Full-text ranking across the
talent pool is D-1's requirement, and D-1 is parked. Nothing in UC-0 through UC-6 needs to search
resume text — UC-2 scores a known set of files against known criteria. Adopting a search cluster
now buys a capability nothing uses and costs memory on a cluster already carrying six services,
two databases and a broker.

**One shared database (6)** would undo [ADR-001](ADR-001-service-decomposition.md) from below:
services that share tables are not independently deployable, and the first cross-service join
someone writes silently makes two services one.

### Implications

**What this buys us**

- Constraints do the work the tenancy rule cannot afford to leave to application code: a
  candidate cannot belong to no workspace, a decision cannot reference a job opening that does
  not exist.
- Anonymisation under UC-5 becomes a coarse, auditable operation rather than a field-by-field
  rewrite — *drop the documents, keep the counts*.
- Changing the parser or a prompt changes a document shape, not a schema; no migration, no
  coordinated release.
- The audit log lives in an append-only relational table where its integrity is enforced, which
  is what makes it usable as evidence.

**What it costs us**

- **There is no transaction across the two stores.** A candidate row can exist with no profile
  document, and — the case that actually matters — a profile document can survive a successful
  PostgreSQL delete. FR-5.5 asks for erasure as a single operation leaving no partial record;
  what this split can offer is a sequenced operation with a verification pass and the
  `deletion pending` state FR-5.11 defines, completing within the 30 days NFR-13 allows. That is
  the architectural cause of UC-5's alternate flow 5b. Deleting the object-storage file is a
  third step with the same problem.
- **Two stores to back up, monitor, secure and hold credentials for**, and two places a breach
  can happen. The PDPA surface is larger than it would be with one store — this is the honest
  cost of the anonymisation benefit above.
- **UC-4 cannot join across the split.** Dashboard metrics have to be maintained in PostgreSQL
  from domain events as they happen, not computed on demand from profile documents. That is more
  code, and it means a lost event is a permanently wrong number until something reconciles it.
- **The split rule has to be enforced by people.** The first time someone puts a decision reason
  in MongoDB "because it was easier", the boundary starts rotting and the anonymisation argument
  above stops being true. This needs to be checked in review, not assumed.
- **Two data models for four students to learn**, including the parts that bite — migrations and
  connection pooling on one side, index behaviour and document-size limits on the other.
- **Referential integrity stops at the service boundary** in any case: because each service owns
  its own schema, a foreign key cannot span services, so some invariants are enforced by
  convention and events regardless of which store holds them.

---

## Related

### Related decisions

- [ADR-001](ADR-001-service-decomposition.md) — per-service data ownership; this record refines
  it into a concrete store-by-store split.
- [ADR-002](ADR-002-async-screening-pipeline.md) — writes exactly one derived document per
  successfully consumed message, and one PostgreSQL status transition per entry.
- [ADR-004](ADR-004-llm-access.md) — the model version recorded alongside each score is stored
  with the scoring document, which is what makes an old justification reconstructable.

### Related requirements

- **Use cases:** UC-0 (users and sessions), UC-6 (memberships and roles), UC-1 (job openings and criteria), UC-2 (batches,
  profiles, scores, justifications, decisions and overrides), UC-3 (interview guides), UC-4
  (pipeline counters), UC-5 (consent, retention policy, audit log, and both expiry actions —
  delete and anonymise). D-1 would read profile documents from MongoDB and remains possible
  without a new store.
- **Functional requirements** (`docs/FUNCTIONAL-REQUIREMENTS.md`): FR-0.3 (workspace scoping —
  a foreign key, not a convention); FR-1.7 (job opening, its criteria and original description);
  FR-2.5, FR-2.8 and FR-2.9 (score, must-have check, override and decision with reason, all in
  PostgreSQL so the ranked list never depends on a document read); FR-2.11 (consent, collection
  date, lawful basis); FR-3.1 (interview guides retained); FR-5.1 (retention policy); FR-5.5 to
  FR-5.8 (erasure across both stores and object storage, anonymisation as "drop the documents,
  keep the counts", and an audit log that names no one); FR-5.11 (deletion pending); FR-5.12
  (expired candidates gone from the pool).
- **Non-functional requirements** (`docs/NON-FUNCTIONAL-REQUIREMENTS.md`): NFR-03 (ranked list
  served from PostgreSQL columns within two seconds); NFR-11 (encryption at rest applies to both
  stores and to object storage — three places to configure, not one); NFR-12 (access audit log,
  append-only in PostgreSQL); NFR-13 (the erasure sequence must complete within 30 days); NFR-15
  (per-criterion evidence persisted with the score).
- **Course requirements** (`docs/course/REQUIREMENTS.md`): the two-database-type requirement —
  PostgreSQL as the RDBMS, MongoDB as the NoSQL store, with a stated reason for what lives in
  each.

### Related artifacts

`docs/PROPOSAL.md` — the glossary terms in `docs/CONTEXT.md` map one-to-one onto the storage
split above, and the Service–Operations–Collaborators table will name the store each service owns.

### Related principles

- *Explainability is required, not optional* — the justification is stored with the score, not
  regenerated on demand, so what a recruiter saw is what can be reviewed later.
- *Easily reversible* — collapsing MongoDB into `jsonb` columns later is a migration; splitting a
  single store after retention logic has been written around it is not.

---

## Notes

Recorded plainly, because a future reader will suspect it anyway: the course requires two
database types, and that requirement is what forced the question. What we did with the question
was not arbitrary — the UC-5 anonymisation argument stands on its own and would have justified
the split without the requirement — but it is fair to say we would probably have shipped
PostgreSQL with `jsonb` first and reached this split only when anonymisation was implemented.

Redis is likely to appear later as a cache for AI Service responses. When it does, it is a cache
and must be treated as one: nothing may be true only in Redis. That is a note here, not a
decision, and needs its own record if it happens.
