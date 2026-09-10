# Changelog

A running summary of what changed in this project's documentation and why.

One entry per working session, newest first. Entries record **decisions and their reasons**,
not file diffs — Git already has the diffs. If a change is worth someone asking "why did we
do that?", it belongs here.

Each entry is written once and then left alone. Later work gets a new entry, even on the same
day — an entry describes what a session decided, and rewriting it destroys the record of when
and why something changed.

---

## 2026-09-10 — ADR template rebuilt, and external context brought into the repo

*(After the initial commit `b4b9a3c`.)*

**ADR template rebuilt on Jeff Tyree & Art Akerman** rather than the simpler
Context/Decision/Status/Consequences format used in the first commit. The course's ADR deck
presents several templates; we chose this one because it forces the two things the lecturer's
deliberately bad sample was missing into their own required fields — the rejected alternatives
(**Positions**) and the mapping from decision to requirement (**Related requirements**).

Three additions to the original 14 fields, documented inside the template so the deviation is
explicit:

- **Date and Deciders** header — the original carries no traceability line, and per-member Git
  contribution is graded.
- **A one-sentence Alexandrian summary** at the top. It doubles as a readiness test: if the
  sentence will not form, the decision is not clear enough to record.
- **Optional fields marked as optional.** Fourteen mandatory sections on a term project
  produces filler, and filler buries the real content. Omit rather than pad with "N/A".

Nygard's guidance on length and voice is kept — one to two pages, written as a conversation
with a future developer.

**External context brought into the repo.** `CLAUDE.md` had been pointing at
`slides/4-1-ADRs.pdf`, which lives outside the repository — a dead reference from any clone.
More seriously, the assignment brief and submission guideline existed only in email and in
class, so a future session would have had no way to know the required headings, the "at least
3 use cases" rule, the warning that terse or ambiguous use cases lose marks, or the
instruction not to add «include»/«extend» decoratively.

- `docs/course/ASSIGNMENT.md` now holds the brief and the guideline in the original Thai with
  English glosses, and a note under each clause saying what it means for our documents.
- `CLAUDE.md` gained a *Context outside this repository* section with the rule: anything that
  influences the documents must be captured inside the repo, external files are summarised
  rather than linked by path, and provenance is named so a reader does not need the source.
- The lecturer's slide decks and the syllabus stay out of the repo deliberately — they are the
  lecturer's material, and this repo holds documentation we wrote.

**Changelog policy changed.** Entries are now written once and left alone; later work gets a
new entry, even on the same day. The `2026-09-10 — Initial proposal and repository setup`
entry is frozen as the baseline covering everything up to the first commit. Previously the
rule was to append to the current day's entry, which would have meant rewriting committed
history in prose.

---

## 2026-09-10 — Initial proposal and repository setup

> **Baseline.** This entry covers everything up to the first commit. Frozen — do not edit it;
> add a new entry above instead.

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
`/uploads/` — real candidate data must never be committed), `CLAUDE.md`, an ADR template following the
lecturer's Context/Decision/Status/Consequences sample, and an ADR index.

**Documentation split fixed.** `PROPOSAL.md` and `CONTEXT.md` had overlapping content that
went stale immediately. `PROPOSAL.md` is now the single source of truth for anything settled;
`CONTEXT.md` holds only open questions, open decisions, the glossary, and provenance.

**Still outstanding:** Functional Requirements, Non-functional Requirements, and at least
three ADRs. The use case diagram needs redrawing in proper UML notation for submission.
