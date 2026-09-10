# Changelog

A running summary of what changed in this project's documentation and why.

One entry per working session, newest first. Entries record **decisions and their reasons**,
not file diffs — Git already has the diffs. If a change is worth someone asking "why did we
do that?", it belongs here.

---

## 2026-09-10 — Initial proposal and repository setup

**Project defined.** HireAssist — an AI-assisted hiring-support layer for companies that
receive more applications than they can screen carefully and interview well. Positioned
deliberately as an assistant layer over existing hiring channels, **not** a job board, job
application platform, or another ATS.

**Target customer defined by a ratio, not company size.** The qualifier is applications
received versus capacity to judge them properly, so a small startup and a mid-size company
with an outnumbered recruitment team are the same customer. Thai tech SMEs are the initial
beachhead, not the boundary.

**Two failure modes named as the core problem:** screening goes shallow, and interviews go
unprepared. The second was added after it became clear the interview-questions use case was
solving a problem the document never stated.

**Six use cases specified** (UC-0 to UC-5) with actors, flows, alternate flows and outcomes,
plus a use case diagram:

- UC-0 Authenticate and manage workspace access
- UC-1 Create a job opening from natural-language requirements
- UC-2 Batch-screen resumes against a job opening
- UC-3 Generate candidate-specific interview questions
- UC-4 Monitor hiring pipeline and stale positions
- UC-5 Enforce candidate data retention

**Decisions made while scoping the use cases:**

- **Rejection reasoning is not a use case.** It is a required justification output of UC-2's
  scoring and is stored on the rejection decision. Internal only — never sent automatically
  to a candidate.
- **PDPA was split.** Retention enforcement became UC-5, scheduler-driven and auditable.
  Consent gating remains a cross-cutting policy rather than a use case of its own.
- **Talent-pool re-matching deferred as D-1.** Parked, not dropped: it cannot be demonstrated
  without a deep talent pool, multiplies scoring cost across the archive, and raises
  purpose-limitation questions UC-5 must answer first. UC-2 still builds the normalised pool
  and scoring stays a separable *(profile, criteria)* behaviour so it can be reinstated
  without rework.
- **Actors reduced to Recruiter and Admin.** The separate Hiring Manager role was removed;
  Admin is a generalisation of Recruiter. Candidate is indirect, System Scheduler supporting.
- **All «include» relationships removed** from the use case diagram. Once re-matching was
  deferred, nothing shared a sub-behaviour, and factoring parts of UC-2 out purely to populate
  the diagram would have added notation without meaning. Only the conditional
  «extend» *Draft Interview Invitation Email* remains.
- **Non-customers section dropped** from Target Customers.

**Repository created.** Documentation-only for now, intended to become a monorepo once
implementation starts. Added `README.md`, `.gitignore` (which excludes `/data/` and
`/uploads/` — real candidate data must never be committed), `CLAUDE.md`, an ADR template
following the lecturer's Context/Decision/Status/Consequences format, and an ADR index.

**Documentation split fixed.** `PROPOSAL.md` and `CONTEXT.md` had overlapping content that
went stale immediately. `PROPOSAL.md` is now the single source of truth for anything settled;
`CONTEXT.md` holds only open questions, open decisions, the glossary, and provenance.

**Still outstanding:** Functional Requirements, Non-functional Requirements, and at least
three ADRs. The use case diagram needs redrawing in proper UML notation for submission.
