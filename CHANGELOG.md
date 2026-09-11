# Changelog

A running summary of what changed in this project's documentation and why.

One entry per working session, newest first. Entries record **decisions and their reasons**,
not file diffs — Git already has the diffs. If a change is worth someone asking "why did we
do that?", it belongs here.

Each entry is written once and then left alone. Later work gets a new entry, even on the same
day — an entry describes what a session decided, and rewriting it destroys the record of when
and why something changed.

---

## 2026-09-11 — Requirements: reconciled, extracted, and rebuilt around quality attributes

**UC-2 accepts PDF only.** Settled while reviewing draft functional requirements: DOCX was
dropped from the accepted formats, so the use case now states PDF in its description, requires
the Recruiter to upload PDFs, and has the System reject non-PDF files at validation.

Unsupported formats moved out of the *unreadable file* alternate flow, since they are now
rejected up front rather than failing during parsing. That flow keeps the two cases that
survive validation — a corrupt file, and a scanned image with no extractable text layer — so
the scanned-resume problem is still handled without needing a second file format.

**Functional requirements written up and moved out of the proposal.** They now live in
`docs/FUNCTIONAL-REQUIREMENTS.md` — 50 requirements numbered `FR-<use case>.<n>` so each traces
to the use case it serves and so adding one never renumbers the rest. `PROPOSAL.md` keeps a
pointer and a per-use-case summary table. The deferred use case D-1 has no requirements.

**Two independent drafts were reconciled.** A teammate had filled in flat-numbered `FR-01`–`FR-33`
directly in `PROPOSAL.md` while a per-use-case set was being reviewed here. The reviewed set was
taken as the base, and six requirements from the other draft were absorbed because they covered
behaviour the base set missed — five merged into existing requirements rather than added
alongside them:

- *not qualified* outcome when a must-have criterion is unmet → merged into FR-2.5
- filtering the ranked list by minimum score and by criterion → merged into FR-2.6
- collection date and lawful basis for processing → merged into FR-2.11
- retaining a generated interview guide for later retrieval → merged into FR-3.1
- erasure across every place the data is held, as a single operation leaving no partial record
  → merged into FR-5.5
- batch-completion notification → added as FR-2.12, the only one with no natural home

Two requirements from that draft were deliberately not carried over: a snapshot of the criteria
in effect when a job opening was saved, and an explicit 0–100 score range.

**Conflicts resolved in favour of the reviewed set:** PDF-only intake (the other draft allowed
DOCX), and pause/resume/close lifecycle rather than close alone.

**Staleness is measured per job opening, not per workspace.** The two drafts disagreed: a
per-job *expected time-to-fill* set by the Recruiter at creation (FR-1.6), versus a single
workspace-wide threshold in days configured by an Admin. We chose per job.

The deciding argument is that one global threshold cannot serve roles with genuinely different
hiring horizons — set low enough to catch a stalling support role and it floods alerts for a
niche senior role; set high enough for the niche role and easy roles rot unnoticed, which is
the exact problem UC-4 exists to solve. Per job also keeps the rule local: the threshold is a
field on the job opening, so Insights & Notifications can evaluate staleness from the
`JobOpeningCreated` event it already consumes, instead of reading workspace configuration owned
by another service.

The cost accepted is that the Recruiter must supply an estimate on every job opening, and a
Recruiter who does not know the answer will guess. A workspace default with a per-job override
was considered and rejected as more machinery than this project needs.

This surfaced a gap in both drafts: nothing recorded *when* an opening was opened, which
days-open depends on. Merged into FR-1.7.

**Use cases and requirements reconciled.** A full cross-check was run in both directions — every
use case behaviour against a requirement, and every requirement against use case prose — and
thirteen discrepancies were fixed in `PROPOSAL.md`. None changed what the system does; they
removed statements the requirements no longer backed, or described behaviour the requirements
had gained.

Behaviour the use cases promised but no requirement backed, now removed from the prose:

- rate limiting of failed sign-ins (UC-0)
- exporting or sharing an interview guide (UC-3) — the guide is viewed in the application
- the "resume-specific coverage is limited" fallback for a thin resume (UC-3)
- stage-to-stage conversion on the dashboard (UC-4)
- staleness alerts for an unreviewed batch and for an undecided shortlisted candidate (UC-4),
  leaving expected time-to-fill as the single rule
- the empty-state dashboard when no positions are open (UC-4)

Behaviour the requirements gained but the use cases never described, now written into the prose:

- pause, resume and close a job opening, and the date an opening was opened (UC-1). UC-4's
  alternate flow already assumed pausing existed, so this closed a dangling reference.
- marking a candidate *not qualified* when a must-have criterion is unmet, and filtering the
  ranked list by minimum score or by criterion (UC-2)
- recording the collection date and lawful basis alongside consent status (UC-2)
- notifying the Recruiter when a batch finishes processing (UC-2)
- retaining a generated interview guide for retrieval before the interview (UC-3)
- erasure reaching profile, resume file, screening results, justification text and interview
  guides as one operation leaving no partial record (UC-5)

UC-4's description was also rewritten to explain *why* the threshold is per opening rather than
per workspace, so the decision is visible to a reader who never opens the changelog.

**Non-functional requirements rewritten around quality attributes**, and moved to
`docs/NON-FUNCTIONAL-REQUIREMENTS.md`. The teammate draft had 23 grouped by loose category
(Operational, Performance, Security, Cultural and Legal, Usability); the replacement has 17
grouped by the quality attribute each serves, every one paired with how it is verified. The
brief was to keep the set small and give the architecture direction rather than aim for
completeness.

Cut, with reasons:

- *Duplicates of functional requirements* — role-based access control, workspace isolation, and
  the rule that a score is never disclosed to the candidate. All three are already FR-0.4,
  FR-0.3 and FR-2.10. A requirement stated twice eventually gets stated two different ways.
- *Not a requirement* — "shall be deployed on cloud infrastructure" is an architectural
  decision and belongs in an ADR.
- *Unverifiable* — "shall comply with the PDPA". Compliance is not testable as a statement; it
  is the combined effect of NFR-12 to NFR-14 and FR-5.1 to FR-5.12, and the document now says
  so in prose instead of pretending otherwise.
- *No architectural consequence* — the Computer Crime Act, already covered by NFR-11 and NFR-12.
- *Untestable as written* — "usable without prior training". A real goal, but with no
  measurement attached it is decoration.

Added:

- **NFR-07**, throughput rising proportionally with worker count. This is the measurement for
  the course's "demonstrate one quality attribute" requirement, and it reuses the load test
  already owed.
- **NFR-10**, no accepted resume is ever lost. Once a batch is acknowledged before processing,
  a Recruiter cannot distinguish a lost resume from a slow one, so the guarantee has to be
  explicit.
- **NFR-17**, scoring model and prompt changeable within one service boundary — the thing that
  will change most often in this system.

**Scoring latency corrected.** The first draft required parse-and-score within 5 seconds, a
figure that only makes sense for deterministic parsing. Scoring is a language-model call whose
latency is dominated by generated output — realistically 8–15 seconds, longer at the tail. The
requirement was split: parsing within 5 seconds (NFR-01), scoring within 20 seconds with a
60-second abandon-and-retry bound (NFR-02). That bound also gives FR-2.7 a definition of
"failed" that it previously lacked.

The batch figure was then checked against it rather than left to contradict it: 100 resumes at
roughly 12 seconds each is about 20 minutes sequentially, so the 10-minute target holds only
with concurrency. NFR-06 now states the worker count it assumes, which makes NFR-07 the
mechanism that delivers it instead of an unrelated claim.

**Scalability chosen as the demonstrated quality attribute**, closing an open decision in
`CONTEXT.md`. It is measurable, demonstrable in a live demo, and shares a load test with an
existing requirement.

**ADR candidates now derived from requirements.** `docs/adr/INDEX.md` lists eight, each with the
requirement that forces it, rather than the loose list of topics it held before.

**Changelog reminder automated.** A `PostToolUse` hook (`.claude/settings.json` plus
`.claude/hooks/changelog-reminder.py`) now fires whenever any file under `docs/` is modified
and injects a reminder to record the change here. Committed at project level so it applies to
the whole team, not one machine.

It decides by **file modification time**, not by inspecting the tool's arguments. The first
attempt matched the string `docs/` in the tool input, which was wrong in both directions: it
would have fired on a read such as `sed -n '1,50p' docs/PROPOSAL.md`, which mentions the path
but changes nothing, and it depended on knowing which argument of which tool carries a path.
Checking what actually changed on disk catches an edit however it was made — the Edit and Write
tools, a scripted Bash heredoc, `sed -i`, a redirect — and never fires for a read.

It stays silent when `CHANGELOG.md` was part of the same change, and remembers the last change
it reported so it does not repeat itself for the same edit.

`.gitignore` previously excluded all of `.claude/`, which would have kept the hook on one
machine. It now shares `.claude/settings.json` and `.claude/hooks/` with the team while still
ignoring `.claude/settings.local.json` and anything else personal.

**Still outstanding.** No ADRs are written yet. The use case diagram still needs redrawing in
proper UML for submission.

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
