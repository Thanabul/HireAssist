# ADR-008: Turning a resume into a candidate profile is a model call

**Date:** 2026-10-01
**Deciders:** Patiphon Puntusin, Thanabul Parodom, Thanwarat Korcharoenkiat, Rerngrit Jangsri

> In the context of resumes whose layout is chosen by the candidate and cannot be specified in
> advance, facing a rule-based parser that must guess at a document it has not seen, we decided to
> extract the structured candidate profile with a language model, through the same service that
> already holds the model credential, to achieve a parser that degrades visibly instead of
> silently, accepting one more model call on the highest-volume path, a slower parsing bound, and
> the loss of a privacy guarantee that until now held by the shape of the contract.

---

## Summary

### Issue

Screening a resume has two steps before a score exists. A PDF becomes text, and that text becomes
a **candidate profile** — the normalised record of work history, skills and education that
scoring is performed against.

The first step is genuinely deterministic and stays that way. The second was specified as
deterministic too, with a 5-second bound, on the assumption that it is text processing. It is not.

**The input is adversarial by nature, not by intent.** A resume's layout is chosen by the person
being evaluated, for aesthetic reasons, from a template we have never seen. We cannot specify it,
cannot reject it, and cannot ask for a resubmission — the candidate is not our user and has no
interface to the system. Every rule a parser applies is a guess about a document that has not
arrived yet. Two columns, a table, a designer's layout, or a Thai resume dating its jobs in the
Buddhist era, and the guess is wrong.

**And wrong quietly.** A rule-based parser that pairs a job title with the wrong employer does not
fail. It emits a well-formed profile, which is scored with confidence, and produces a ranking with
a justification that reads plausibly and is about a career the candidate does not have. That is
not a parsing defect one layer down; it is the product's central failure — a candidate judged
without anyone having actually read them — reintroduced in the one place nobody is looking.

The forces:

- **We have no leverage over the input format**, and no ability to obtain a corrected one.
- **A silent wrong profile is worse than a loud failure.** Marking a resume for manual review
  costs a recruiter two minutes; a plausible wrong score costs a candidate the role.
- **Structuring is what language models are good at**, and what regular expressions are worst at.
- **Thai and English mixed in one document** is normal in this market, and multiplies the number
  of rules a deterministic parser needs.
- **Every model call is paid for, and this is the highest-volume path in the system** — once per
  resume, two hundred times for one recruiter action.
- **Sending a whole resume to a model means sending the parts we deliberately exclude from
  scoring** — name, age, nationality, photograph.

### Decision

**The candidate profile is produced by a model call, served by the same service that holds the
model credential, as a fourth operation alongside criteria extraction, scoring and interview
questions.**

- **Text extraction stays deterministic and stays where it is.** The service that owns resume
  files turns the PDF into text in process. No model sees a file.
- **The new operation takes resume text and a language, and returns a candidate profile.** It is
  the only operation that receives unstructured resume text.
- **The profile is extracted once per resume and stored**, in the document store that already
  holds candidate profiles. Scoring is once per resume per job opening; extraction is not repeated
  when a second opening is scored, when a batch is re-run, or when the talent pool is re-matched.
- **Protected attributes are dropped during extraction.** Gender, age, marital status, religion,
  nationality and photograph are not fields of a candidate profile, so the extraction operation is
  instructed not to carry them into one, and nothing downstream can reintroduce them.
- **A resume the model cannot structure is marked for manual review**, under the same
  retry-then-abandon path that already governs a failed score. It is never given an empty profile.

**The parsing bound moves from 5 seconds to 20 seconds at the 95th percentile, with a 60-second
abandon** — the same figures scoring already carries, because it is now the same kind of work.

### Status

**Accepted**

### Group

Data · Integration · Privacy

---

## Details

### Assumptions

- A language model structures a resume more reliably than a rule set we could write and maintain
  in the time available. *This is the assumption the decision rests on, and it has not been
  measured — see Notes.*
- Extraction output is small and mostly input tokens, so its cost per resume is below scoring's.
- Resume text extracted from a PDF is faithful enough to structure. Scanned images are out of
  scope; those need character recognition, which is a separate decision.
- The document store can hold profiles long enough to make caching worthwhile, within the
  retention policy that already governs candidate data.

### Constraints

- Four part-time developers on a deadline, none of whom has written a production resume parser.
- Personal data law makes what is sent to a third-party processor a compliance question, not only
  a cost one.
- The model provider's rate limit, not our hardware, bounds throughput on this path.

### Positions

1. **Rule-based structuring** — layout-aware extraction with coordinates and font weights, section
   segmentation by heading keywords, a skills dictionary, and date regular expressions.
2. **Model-based structuring through the service holding the credential.** *(Selected.)*
3. **Send the resume file itself to the model**, and let it do extraction and structuring in one
   call.
4. **Structure nothing.** Put the whole resume text in the profile's free-text field and let
   scoring read it unstructured.
5. **Rule-based first, model only on the residue** — parse what matches confidently, ask the model
   about the rest.

### Argument

**Against rule-based structuring (1).** Not that it cannot be built — parts of it work well. A
skills dictionary is genuinely reliable, because membership of a known list is not inference.
Dates yield to enough regular expressions. What does not yield is the association: deciding which
title belongs to which employer over which period, which is layout-dependent and therefore
unbounded. That is also the part scoring depends on most, since every criterion about experience
is answered from it. The decisive objection is the failure mode, not the accuracy: a rule set that
mis-associates produces a confident, plausible, wrong profile, and nothing in the system can tell
that from a right one.

**Against sending the file (3).** It saves a step and costs the boundary. The service holding the
credential would take an arbitrary binary from a caller, and the rule that it receives only what a
judgement needs — which is what keeps the cost and the exposure of the model path reviewable in
one place — would no longer be true of it. Text extraction is the one part of this pipeline that
*is* deterministic, and there is no reason to buy it from a model.

**Against structuring nothing (4).** Attractive, and nearly viable: scoring already reads the
profile's free-text field, so an unstructured resume would still be scored. It fails on two
counts. The recruiter-facing views need structure — filtering a shortlist by criterion, showing
years of experience, recognising a candidate who has applied before — and none of that is possible
over a blob. More seriously, it destroys the privacy property described below: a raw dump carries
every excluded attribute into every scoring prompt, on every resume, forever.

**Against the hybrid (5).** The best idea here and the wrong one for now. It needs the rule set
*and* the model path *and* a confidence measure to decide between them — three things to build and
tune where we have time for one. It is the natural optimisation once there is a measurement to
optimise against, and it is worth revisiting when the cost per batch is known.

**For model-based structuring (2).** It puts the judgement where judgement is possible, and it
puts it behind the boundary that already exists for exactly this kind of work — one credential,
one place where prompts live, one place where cost is metered, and no new component. Caching makes
the cost bearable: extraction is per resume, not per resume per opening, so the expensive case —
a talent pool re-matched against many openings — pays for it once. And it turns the privacy
handling from something a rule set would have to do by hand into a single instructed step in one
prompt.

### Implications

**What this buys us**

- The profile is produced by the thing best suited to producing it, on documents whose shape we
  cannot predict.
- A resume that cannot be structured is *marked for manual review*, not silently mis-structured.
  The failure becomes visible, which is the property the product is built around.
- Thai and English need no separate rule sets.
- Extraction is the one place where excluded attributes can be dropped deliberately, rather than
  by hoping no rule accidentally captures a photograph caption.
- A stored structured profile is what re-matching a talent pool against a new opening requires,
  so this decision pays for a capability that is currently deferred.

**What it costs us**

- **One more model call on the highest-volume path.** Amortised over re-scoring, but the first
  screening of a batch now makes two calls per resume instead of one. A runaway batch costs twice
  as much as it did.
- **Parsing is no longer fast.** The bound quadruples, from 5 seconds to 20. Perceived batch
  latency rises, and the throughput target is now bounded by the provider's rate limit on both
  steps rather than one.
- **A privacy guarantee weakens from structural to instructed.** Until now, excluded attributes
  could not reach a prompt because the profile has no field to carry them — a property of the
  contract's shape, which no one could forget. Extraction sees the whole resume, so that guarantee
  now rests on the extraction prompt behaving, and on a test. This is a real reduction and is
  accepted deliberately: the alternative is a rule set that must achieve the same thing by hand,
  in more places, with no better assurance.
- **An argument for the current service split weakens.** The two services were separated partly
  because their work has opposite resource profiles — one processor-bound and quick, the other
  waiting on a remote call. Both are now waiting on a remote call. The split stands on its other
  reasons: a model outage must not reach sign-in or the dashboard, and only one service holds the
  credential. That argument, not the resource one, is now what carries it.
- **Extraction quality is unmeasured.** No resume has been through either path. The decision is
  made on the shape of the problem rather than on evidence.
- **Scanned resumes remain unhandled**, and now look like a gap in a model-based path rather than
  a known limit of a text extractor.

---

## Related

### Related decisions

- **ADR-001** drew the service boundaries, and argued for separating resume processing from model
  access partly on their opposite resource profiles. That specific argument no longer holds; the
  boundary stands on failure isolation and credential containment.
- **ADR-002** defines one independently retried unit of work per resume, with a bounded retry and
  a terminal *needs manual review* state. Extraction failure uses that path unchanged; the unit of
  work now contains two model calls rather than one.
- **ADR-003** places AI-derived documents in the document store and the system of record in the
  relational database. The extracted profile is an AI-derived document and goes where that record
  already says, so caching it introduces no new storage decision.
- **ADR-004** requires that the service holding the credential receive only what a judgement
  needs, and never a raw file. The file rule is unchanged. The minimisation rule is narrowed:
  this one operation receives unstructured resume text, and is the reason the excluded attributes
  are dropped there rather than assumed absent.
- **ADR-005** *(Proposed)* prefers Python for resume processing partly because of its
  PDF-and-text libraries. Text extraction still happens there, so the preference stands, on a
  smaller argument.
- **ADR-007** carries the model service's operations over a compiled contract. The new operation
  is defined in the same contract and generated the same way.
- **Still open:** whether a rule-based pre-pass in front of the model is worth building once cost
  per batch is measured; and character recognition for scanned resumes.

### Related requirements

- **FR-2.3** — a resume is parsed into a normalised candidate profile. Unchanged in what it
  requires; this record decides how.
- **FR-2.7** — retry failed attempts and flag what cannot be parsed or scored for manual review.
  Now covers a failed extraction as well as a failed score.
- **NFR-01** — parsing within 20 seconds at the 95th percentile, abandoning at 60. Raised from 5
  seconds by this decision.
- **NFR-13, NFR-14** — erasure, and the exclusion of protected attributes from scoring. NFR-14 is
  now enforced by instruction and test at extraction rather than by the profile's shape alone.
- **NFR-16** — Thai and English. The reason one path now serves both.
- **NFR-17** — the scoring model and prompt change within one service boundary. Extraction is now
  inside that same boundary and gains the same property.

### Related artifacts

The shared contract definition for the model service, the runtime description of batch screening,
and the per-service operations table, each of which currently states that profile extraction is
not a model call.

### Related principles

- *Prefer a loud failure to a plausible one.*
- *Do not write rules for input you do not control.*
- *Pay once for what is reused* — extraction is per resume, scoring is per resume per opening.
- *A guarantee by construction beats a guarantee by discipline* — and when one is traded for the
  other, say so rather than letting it lapse quietly.

---

## Notes

The assumption underneath this record is unmeasured: no resume has been run through either path.
It was taken on the structure of the problem — an input we do not control, and a failure that does
not announce itself — rather than on a comparison, because building the rule-based parser well
enough to compare fairly would cost most of the time the decision is trying to save.

The honest counter-argument is cost. Doubling calls on the busiest path is the kind of decision
that looks obvious in design and expensive in an invoice, and the hybrid in position 5 is the
answer if it does. Extraction caching is what makes the difference survivable, and it is the first
thing to verify actually works.

The privacy trade is the part worth returning to. Swapping a property the contract enforced for
one a prompt is asked to observe is a real loss, taken because the alternative offered no better
assurance and more places to get it wrong. If a rule-based pre-pass is ever built, restoring that
guarantee should be one of the things it buys back.
