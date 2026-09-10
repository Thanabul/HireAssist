# HireAssist — Working Notes

> **`PROPOSAL.md` is the single source of truth** for the project name, problem, target
> customers, use cases, requirements and ADRs. Nothing settled is repeated here.
>
> This file holds only what the proposal deliberately does **not** carry: unanswered
> questions, decisions still open, and shared vocabulary for the documents that come next.
> Course constraints live in [course/REQUIREMENTS.md](course/REQUIREMENTS.md) and
> [course/GRADING.md](course/GRADING.md).

---

## 1. Open questions — to validate

Assumptions currently stated in the proposal that we have not verified:

- [ ] Application volume per opening. Proposal claims ~20–200 — is that real for a Thai tech SME?
- [ ] Where resumes arrive today: email, JobsDB/JobThai, LINE, Google Form?
- [ ] Do target companies already use an ATS, or is it genuinely spreadsheets + inbox?
- [ ] Which resume formats must we parse — PDF, DOCX, scanned images? Thai + English mix?
- [ ] Typical expected time-to-fill, to make UC-4's staleness thresholds realistic.
- [ ] Realistic default retention period for UC-5 (6 / 12 / 24 months?).

---

## 2. Open decisions — ADR candidates

Each of these should become an ADR, or be folded into one, before the architecture diagram
and the Service–Operations–Collaborators table are produced.

- [ ] **Resume ingestion channel.** Batch upload is confirmed in UC-2. Is an automated channel
      (IMAP/webhook) in scope, or a stated future extension? *(Currently unresolved — the
      proposal's positioning says "plugs into existing channels" while UC-2 is upload-only.)*
- [ ] **LLM provider and placement.** Which model, self-hosted or API, and what happens when it
      is unavailable or slow. Cost bounding and caching strategy.
- [ ] **Service decomposition.** Where the boundaries fall, and which is REST vs. gRPC vs.
      broker-driven.
- [ ] **Datastores.** Which RDBMS, which NoSQL, and what belongs in each.
- [ ] **Async processing model** for UC-2 batches — queue topology, retry, partial failure.
- [ ] **Scheduler design** shared by UC-4 (staleness) and UC-5 (retention).
- [ ] **Which quality attribute** we demonstrate for the course requirement.
- [ ] ~~Re-match trigger (event vs. scheduled)~~ — moot while D-1 is deferred.

---

## 3. NFR seed material

Raw input for the proposal's *Non-functional Requirements* section, which is not yet written.
**Delete this section once those requirements are in `PROPOSAL.md`.**

Course-imposed (see [course/REQUIREMENTS.md](course/REQUIREMENTS.md)): microservices with REST + gRPC +
message broker, API gateway, service discovery, RDBMS + NoSQL, two load tests, risk matrix, and
one demonstrated quality attribute.

Domain-imposed:
- **Privacy / PDPA** — resumes are personal data; consent and retention are first-class.
- **Explainability** — a score without a stated reason is not usable by a recruiter.
- **Cost** — target customers are price-sensitive; LLM calls must be bounded and cached.
- **Throughput / latency** — a batch must be accepted immediately and processed concurrently.
- **Thai + English** language support throughout.
- **Bias / fairness** — screening must not discriminate; the human stays in the loop.
- **Auditability** — every AI score, human override and erasure must be reconstructable.

---

## 4. Glossary

Shared vocabulary for the proposal, the architecture diagram, and the
Service–Operations–Collaborators table.

| Term | Meaning |
|---|---|
| **Workspace** | One company's isolated tenant. All data access is scoped to it. |
| **Job Opening** | An open role, holding weighted screening criteria and an expected time-to-fill. |
| **Criterion** | One requirement of a job opening, flagged must-have or nice-to-have, with a weight. |
| **Resume** | The raw file a candidate submitted. |
| **Candidate Profile** | The normalised structure parsed from a resume: contact, history, skills, education. |
| **Candidate** | A person. May have profiles and decisions across several job openings over time. |
| **Screening Batch** | One submitted set of resumes processed asynchronously against a job opening. |
| **Screening Score** | The weighted match of a profile against criteria, always with a justification. |
| **Justification** | The written evidence-based reason accompanying a score. Internal only. |
| **Decision** | Shortlist or reject, recorded with its reason and with any human override of the AI score. |
| **Interview Guide** | The generated question set for one candidate against one job opening. |
| **Talent Pool** | All retained candidate profiles in a workspace, governed by consent and retention. |
| **Stale Position** | An open position breaching its staleness rule (e.g. past expected time-to-fill). |
| **Retention Policy** | Workspace setting: period, anchor date, and expiry action (delete or anonymise). |
| **PDPA** | Thailand's Personal Data Protection Act. |

---

## 5. Provenance — original ideas → current use cases

Kept only as a record of where the concept came from. The authoritative descriptions are in
`PROPOSAL.md`.

| Original idea | Became |
|---|---|
| AI Screen Resume | UC-2 |
| Reason for rejection (not sent to candidate) | An output field of UC-2, not a use case |
| Talent Pool Re-matching | **D-1 — deferred** (see *Deferred Use Cases* in the proposal) |
| PDPA Assistant | UC-5 (retention); consent gating remains an NFR |
| First draft email for interview meeting | «extend» on UC-2 |
| Notification for position open too long | Folded into UC-4 |
| *(new)* Job creation from natural language | UC-1 |
| *(new)* Candidate-specific interview questions | UC-3 |

---

## 6. File map

| File | Purpose |
|---|---|
| `PROPOSAL.md` | **Source of truth** — the submission document |
| `CONTEXT.md` | This file — open questions, open decisions, glossary |
| `adr/INDEX.md` | ADR index; `adr/TEMPLATE.md` is the format to use |
| `course/` | Course minimum requirements & grading breakdown |
| `reference/` | The lecturer's ADR samples (good and bad) |
