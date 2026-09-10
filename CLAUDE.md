# CLAUDE.md — working rules for this repository

HireAssist is a Software Architecture term project. Right now it is **documentation only**;
implementation comes later. The documents *are* the deliverable, so keeping them accurate is
not housekeeping — it is the work.

---

## The core rule

**Every change or decision updates the docs in the same session it is made.**

Not "later", not "before submission". A decision that lives only in a chat transcript is lost.
If we agree something in conversation, it is not done until it is written down in the right
file, every place that contradicts it has been fixed, and `CHANGELOG.md` records it.

---

## The changelog is not optional

**Any change to the documentation gets an entry in `CHANGELOG.md`.**

It is a *summary* log, not a diff — Git already has the diffs. Record the decision and the
reason for it, in prose a teammate can read months later. The test: if someone could
reasonably ask *"why did we do that?"*, the answer belongs in the changelog.

- One entry per working session, newest first, dated `YYYY-MM-DD`.
- Write **why**, not just what. "Deferred re-matching" is useless; "deferred re-matching
  because it cannot be demonstrated without a deep talent pool and raises purpose-limitation
  questions UC-5 must answer first" is the point.
- Record decisions that were *reversed* or *reconsidered* too. Knowing that something was
  tried and rejected is worth as much as knowing what was chosen.
- Note what is still outstanding at the end of an entry.
- Append to the current session's entry rather than creating a second entry for the same day.

---

## Where things live

| File | Holds | Never holds |
|---|---|---|
| `docs/PROPOSAL.md` | **Source of truth.** Everything settled: name, problem, customers, use cases, requirements, ADR summaries. | Unresolved questions, internal deliberation |
| `docs/CONTEXT.md` | Only what is *not* settled: open questions, open decisions, glossary, provenance. | Anything already stated in PROPOSAL.md |
| `docs/adr/` | One file per architectural decision, plus `INDEX.md`. | Decisions still being debated |
| `README.md` | Orientation: pitch, team, doc index, use case list, repo status. | Detail that belongs in PROPOSAL.md |
| `CHANGELOG.md` | A dated summary of what changed and **why**, newest first. | File-by-file diffs |

**No duplication between `PROPOSAL.md` and `CONTEXT.md`.** They overlapped once and it went
stale immediately. When something moves from open to settled, it moves *out* of CONTEXT and
*into* PROPOSAL — copying is not moving.

---

## When a use case changes

Use cases are referenced from many places. Changing one means touching all of these — check
every one, every time:

1. The use case's own section in `docs/PROPOSAL.md`
2. The **overview table** at the top of *Scenario (use-case & description)*
3. The **actors table** — actor descriptions name the use cases they participate in
4. The **use case diagram** (Mermaid block) — nodes and associations
5. The **relationships rationale** below the diagram, if any «include»/«extend» is affected
6. **Cross-references inside other use cases** — grep for `UC-` and read each hit in context
7. The use case list in `README.md`
8. The provenance table in `docs/CONTEXT.md`
9. `CHANGELOG.md` — what changed and why

Stale cross-references have been the single most common defect in this repo. After any
renumbering, grep for every `UC-` and `D-` reference and verify each one still points at what
it claims.

**Use case IDs:** UC-0 through UC-5 active, D-1 deferred. If a use case is removed, close the
numbering gap and re-check every reference. If one is deferred rather than dropped, it moves
to the *Deferred Use Cases* section with a stated reason — deferral is a decision and gets
recorded like one.

---

## ADRs

Format is fixed by the course: **Context · Decision · Status · Consequences**. Use
`docs/adr/TEMPLATE.md`; the reasoning behind the format is in that file, drawn from the
lecturer's good and bad samples in `docs/reference/`.

- Write the ADR when the decision is made. Reconstructing the reasoning later does not work —
  the alternatives that were rejected are exactly what gets forgotten.
- Add the `INDEX.md` row in the same commit as the ADR.
- If you cannot name a rejected alternative, it is not an ADR.
- Superseding never edits the original: set the old status to *Superseded by ADR-NNN*.
- A decision recorded in an ADR that contradicts `PROPOSAL.md` means `PROPOSAL.md` is now
  wrong — fix it.

---

## Terminology

Use the glossary in `docs/CONTEXT.md`. The terms are deliberate and consistent across
documents: *Workspace, Job Opening, Criterion, Candidate Profile, Screening Batch, Screening
Score, Justification, Decision, Interview Guide, Talent Pool, Stale Position, Retention Policy.*

If a new domain term is needed, add it to the glossary rather than improvising a synonym.
Silent synonyms are how a domain model rots.

---

## Writing style for these documents

- Explain *why*, not just *what*. A grader is reading for understanding of the system's
  behaviour and scope — an ambiguous or over-terse use case loses marks explicitly.
- State trade-offs honestly, including negative consequences. Sections that are entirely
  positive read as unexamined.
- Scope decisions are load-bearing: when something is deliberately excluded, say so and say
  why. "Not a job board", "not an ATS", D-1 deferred — these are decisions, not gaps.
- Prefer prose that a reader can follow over bullet fragments that need decoding. Tables are
  for genuinely tabular material.

---

## Constraints that shape every decision

- **Course requirements** (`docs/course/REQUIREMENTS.md`) are non-negotiable: REST + gRPC +
  message broker, API gateway, service discovery, RDBMS + NoSQL, 2 load tests, risk matrix,
  one demonstrated quality attribute. Any architecture proposal must satisfy all of them.
- **PDPA** is a first-class design force, not a feature. Consent and retention gate what the
  system may do with candidate data.
- **Never commit real resumes or candidate data.** `/data/` and `/uploads/` are gitignored.
  Use synthetic examples in documentation.

---

## Team

Per-member Git contribution is graded. Commit under your own account; do not batch other
people's work into your commits.
