# ADR-004: All model access through one AI Service, on a managed API that does not train on our data

**Date:** 2026-09-11
**Deciders:** Patiphon Puntusin, Thanabul Parodom, Thanwarat Korcharoenkiat, Rerngrit Jangsri

> In the context of every AI behaviour in UC-1, UC-2 and UC-3, facing resumes that are personal
> data under PDPA and a team with no GPU capacity, we decided to route all model calls through a
> single internal AI Service speaking to a managed API whose terms exclude training on our
> inputs, to achieve a disclosure we can lawfully justify and one place to control cost, prompts
> and failure, accepting a dependency we cannot repair ourselves and a period during which
> screening produces no scores at all.

---

## Summary

### Issue

Three use cases need a language model. UC-1 turns a paragraph of plain Thai or English into
weighted criteria. UC-2 scores a candidate profile against those criteria and writes the
justification that makes the score usable. UC-3 generates interview questions from the
intersection of a resume and a job opening. The model is not a feature of HireAssist; it is the
capability the product is sold on.

**What we send it is personal data.** A resume carries a name, contact details, employment
history and often more. Under Thailand's PDPA, sending it to a third party is a disclosure that
needs a lawful basis and terms that bound what the recipient may do with it. One clause decides
the whole question: if the provider may train on submitted data, then every resume becomes part
of a model weight we cannot reach into and delete. UC-5's entire promise — that a candidate's
data is erased on a schedule and the erasure can be proved — would be false the moment the first
batch was screened. A provider that trains on our inputs is not a cheaper option; it is an
incompatible one.

**We have no GPU and no budget for one.** Nobody on the team has hardware that runs a
competitive model, and the customers in the proposal are explicitly price-sensitive, so per-token
cost is an architectural concern rather than an operations detail: it scales linearly with
applicant volume, which is the very thing our customers have too much of.

**Resumes arrive in Thai and English, often mixed within one document.** Whatever we choose has
to read both competently, because a model that handles Thai poorly produces exactly the failure
the product exists to prevent — a good candidate rejected for their vocabulary.

**The model is the least reliable dependency in the system,** and NFR-10 commits us to never
losing an accepted resume regardless of what it does, while NFR-02 bounds how long any one
scoring attempt may wait for it. Rate limits, latency spikes and outages are certain, not
hypothetical — and the provider's rate limit, not our worker count, may turn out to be the ceiling
on the throughput NFR-07 measures.

### Decision

**1. Every model call goes through the AI Service. No other service holds a model credential or
a prompt.** The AI Service exposes gRPC operations in domain terms, not model terms:

- `ExtractCriteria(free_text, language) → proposed title, weighted criteria` (UC-1)
- `ScoreProfile(candidate_profile, criteria) → score, must-have check, justification` (UC-2)
- `GenerateInterviewGuide(candidate_profile, criteria, emphasis) → tagged questions` (UC-3)

Callers ask for a screening score, never for a completion. The provider, the model name, the
prompt and the token budget do not appear in any other service's contract. This is NFR-17 made
structural: the scoring model or prompt changes without modifying or redeploying anything else.

**2. The provider is a managed API whose terms exclude training on our inputs and outputs**, with
a stated retention window and a data-processing agreement we can put in front of a customer. The
initial choice is the **Anthropic Claude API**, which does not train on API inputs by default;
the OpenAI and Google Gemini paid API tiers carry comparable commitments and remain substitutes.
The provider is configuration, not code.

**3. There is no fallback model.** When the provider is unavailable the system does not switch to
a weaker one. Work waits in the queue, retries with backoff, and — if the retry budget is
exhausted — the affected resumes are marked *needs manual review*, exactly as
[ADR-002](ADR-002-async-screening-pipeline.md) specifies and as UC-2's alternate flow 4a already
promised.

**4. Cost and exposure are controlled inside the AI Service:**

- **Minimise what is sent.** The prompt receives the parsed profile fields the operation needs
  and the criteria — never the raw file, never fields irrelevant to the judgement, and never the
  attributes NFR-14 excludes from scoring. Gender, age, marital status, religion, nationality and
  photograph are stripped from the profile inside the AI Service, before any prompt is built, so
  that no caller can forget to.
- **Cache by content.** Results are keyed on the profile version and the criteria version, so
  re-running a batch or re-opening a guide does not re-pay for an identical call.
- **Budget per workspace and per batch.** A runaway batch hits a ceiling and reports it rather
  than producing an invoice.
- **Meter every call** — model, version, token counts, latency, outcome. The metering log
  contains no personal data.

**5. The model version is recorded with every score and justification.** Providers update models
underneath a stable name; without the version pinned and stored, a score from March cannot be
explained in September. NFR-15 requires the per-criterion evidence to be persisted with the
score; the version is what makes that evidence reproducible rather than merely retained.

**6. The provider is documented as a data processor.** The workspace's privacy notice and the
consent text must disclose that resumes are processed by a named overseas processor. This is a
product obligation created by this decision, not a footnote to it.

### Status

**Accepted**

### Group

AI/LLM · Security · Cost

---

## Details

### Assumptions

- The provider's terms genuinely exclude training on API inputs, and the retention window is
  short and documented. **This is the assumption the whole decision rests on and it must be
  verified against the provider's current data-processing terms before any real resume is
  processed** — not taken from this document, which will age.
- A frontier hosted model reads Thai résumés well enough to score them fairly. Not yet
  validated; it needs a small evaluation set of real-shaped (synthetic) Thai resumes before we
  rely on it.
- Per-token cost stays within what the pricing in the proposal can absorb at 20–200 resumes per
  opening.
- Provider availability is high but not total, and outages are minutes to hours rather than days.
  If that proves wrong, position 3 below is reopened.
- Team has no GPU, and the term project has no hardware budget.

### Constraints

- PDPA: personal data may be disclosed to a processor only under terms that bound its use, and
  must remain erasable on request or on expiry (UC-5).
- Customers are price-sensitive (`docs/PROPOSAL.md`, Target Customers), so per-candidate cost is
  bounded by what an SME will pay.
- [ADR-001](ADR-001-service-decomposition.md) established the AI Service as a separate,
  gRPC-only service not exposed through the gateway.
- [ADR-002](ADR-002-async-screening-pipeline.md) fixed how failures of this dependency are
  handled.

### Positions

1. **Self-hosted open-weight model** (Llama, Qwen, Typhoon and similar) on Ollama or vLLM —
   nothing ever leaves our infrastructure.
2. **Managed API with a self-hosted fallback** — the hybrid: use the API normally, fail over to a
   local model during an outage.
3. **Two managed providers with automatic failover** between them.
4. **A cheaper provider whose default terms permit training, with training opted out** in the
   account settings.
5. **Managed API only, one provider, mediated by our own AI Service** (chosen).
6. **No AI Service — each service calls the provider SDK directly** where it needs a model.

### Argument

**Self-hosting (1) is the strongest privacy answer and we still rejected it.** Nothing leaving
our infrastructure would remove the disclosure question entirely and make PDPA compliance
substantially easier to argue. It fails on capability rather than principle: there is no GPU and
no money for one, and the models small enough to run without one are materially weaker on Thai —
which converts a privacy win into a fairness loss in the one place the product must not fail.
It also moves the availability problem to four students who would then be the on-call team for a
model server, which is not obviously more reliable than a provider with an SLA. Worth
re-examining if the project ever has hardware; the AI Service boundary is what would make that
re-examination cheap.

**The hybrid (2) was reconsidered specifically because NFR-10 commits us to never losing
accepted work, and rejected anyway.** A fallback model makes a candidate's score depend on which
provider happened to be healthy when their resume was processed. Two candidates in the same batch
could be ranked against each other on scores produced by different models — indefensible in a
system whose entire proposition is a comparable, justified score, and unanswerable when a
recruiter asks why one was rated lower. It also doubles the prompt-tuning and evaluation surface
for a four-person team. NFR-10 asks for exactly what we can honestly promise and no more: *every
accepted resume reaches a terminal state* — scored, or flagged for manual review — not *the AI is
always available*. The queue holds the work; the recruiter is told; nothing is lost or silently
guessed.

**Multi-provider failover (3)** has the same comparability problem in a milder form, plus two
sets of terms to verify and keep verified. Deferred rather than dismissed: because every call is
already behind the AI Service's domain operations, adding a second provider later is a change in
one service. If outages turn out to be frequent, this is the first thing to revisit.

**Opt-out terms (4)** were rejected on the difference between a setting and a contract. An opt-out
can be reset by an account change, a plan migration, or someone else on the team; a contractual
term cannot. Where a compliance promise is being made to a customer, the guarantee has to be the
kind you can show someone, not the kind you have to remember to keep switched on.

**Direct SDK calls from each service (6)** would put the credential in three codebases, the
prompts in three places to drift apart, and no single point at which spending can be capped or a
provider swapped. Everything this record decides in items 2–5 would have to be implemented three
times and would be inconsistent within a month.

**What decided it, in order:** the training clause is non-negotiable because UC-5 depends on it;
hardware we do not have rules out self-hosting; Thai-language quality rules out the small models
we could otherwise run; and comparability of scores rules out mixing models. What remains is a
single managed provider — so the design work goes into making that dependency safe to have:
minimise what is sent, cache what repeats, cap what it costs, record what produced each answer,
and let the queue absorb its failures.

### Implications

**What this buys us**

- One credential, one prompt set, one cost centre, one place a provider swap happens.
- A lawful basis we can actually put in a privacy notice: named processor, no training,
  documented retention.
- UC-5's erasure promise stays true, because nothing we send is absorbed into a model.
- Every score carries the model version that produced it, so a justification can be reconstructed
  months later — the auditability requirement, satisfied structurally.
- D-1 re-matching, if reinstated, reuses `ScoreProfile` unchanged, and inherits the same budget
  and caching controls that keep it from multiplying cost across the archive.

**What it costs us**

- **During a provider outage, screening produces nothing.** Not slower results — no results. The
  queue holds the work and the recruiter waits; if the outage outlives the retry budget, those
  resumes land in *needs manual review* and a human has to do what the product was bought to
  avoid. This is the direct, accepted consequence of having no fallback, and it belongs in the
  risk matrix.
- **Cost scales linearly with applicants.** A customer with 2,000 applicants costs roughly ten
  times one with 200, while both may pay a similar subscription. Either pricing is per-volume or
  margins invert on exactly the customers the proposal says we serve best.
- **Personal data crosses a border.** Some customers will refuse on that basis alone, and the
  consent text must state it. This narrows the addressable market in a way a self-hosted option
  would not.
- **We cannot fix a quality regression.** When the provider updates a model, scores can shift
  under us with no code change on our side. Pinning the version limits it, but pinned versions
  are eventually retired, and a migration means re-validating every prompt.
- **Budget ceilings create a new failure mode**: a batch that stops mid-way because a workspace
  exhausted its allowance. That state has to be visible and resumable, or it looks identical to a
  bug.
- **The AI Service is a bottleneck for every use case.** UC-1's interactive extraction queues
  behind UC-2's batch scoring unless the service separates them — interactive and batch traffic
  need different rate-limit budgets, which is more machinery in the one service that already
  holds the credential. And the provider's rate limit, not our worker count, may become the
  ceiling on NFR-07: the scalability demonstration can be capped by a number we do not control,
  which is the risk-matrix item `docs/CONTEXT.md` already records and the reason a deterministic
  pre-filter remains a candidate decision.
- **Caching stores derived personal data.** A cache keyed on profile content is another place a
  candidate's data lives, so it must respect retention and be purged as part of the erasure
  FR-5.5 describes, within the 30 days NFR-13 allows — otherwise the cost optimisation quietly
  reopens the compliance hole.

---

## Related

### Related decisions

- [ADR-001](ADR-001-service-decomposition.md) — created the AI Service and made it gRPC-only and
  unreachable from the gateway; that boundary is what this record fills in.
- [ADR-002](ADR-002-async-screening-pipeline.md) — carries the failure handling this decision
  relies on. The two records are a pair: no fallback model is only acceptable because no work is
  lost.
- [ADR-003](ADR-003-polyglot-persistence.md) — scoring output and the recorded model version are
  stored as documents in MongoDB.

### Related requirements

- **Use cases:** UC-1 (criteria extraction), UC-2 (scoring, justification, and alternate flow 4a
  when the scorer is unavailable), UC-3 (interview guide generation), UC-5 (the erasure promise
  that the no-training term protects). D-1 depends on `ScoreProfile` being reusable over the
  talent pool.
- **Functional requirements** (`docs/FUNCTIONAL-REQUIREMENTS.md`): FR-1.2 (criteria derived from
  free text); FR-2.5 (score, must-have check and justification for every resume); FR-2.7 (retry,
  then manual review, when the model cannot answer); FR-3.1 to FR-3.4 (interview guide generation
  and regeneration with a stated emphasis); FR-5.5 (erasure reaches the cache too).
- **Non-functional requirements** (`docs/NON-FUNCTIONAL-REQUIREMENTS.md`): NFR-02 and NFR-05
  (scoring and guide-generation latency bounds, which the provider — not our code — largely
  determines); NFR-07 (the provider's rate limit as a possible ceiling on the demonstrated
  attribute); NFR-10 (no accepted resume lost, whatever the provider does); NFR-13 (erasure within
  30 days, including cached derived data); NFR-14 (protected attributes stripped in the AI Service
  before any prompt); NFR-15 (per-criterion evidence, reproducible because the model version is
  stored with it); NFR-16 (Thai and English); NFR-17 (model and prompt change within this one
  service).
- **Course requirements** (`docs/course/REQUIREMENTS.md`): the gRPC service; the demonstrated
  quality attribute — Scalability, NFR-07 — for which this record names the ceiling we do not
  control; and the risk matrix, to which this contributes provider outage, rate-limit ceiling,
  cost escalation, cross-border transfer, and model-drift risks.

### Related artifacts

`docs/PROPOSAL.md` — UC-1, UC-2, UC-3 and the Non-functional Requirements section. The privacy
notice and consent text, which do not exist yet, are a deliverable this decision creates.

### Related principles

- *The human still decides* — reinforced here: when the model cannot answer, the work goes to a
  person rather than to a guess.
- *Explainability is required, not optional* — a score without a reproducible justification is
  not acceptable, which is why the model version is stored with it.
- *Easily reversible* — the provider is behind a domain-shaped gRPC interface precisely because
  it is the part of this decision most likely to be wrong.

---

## Notes

The tension in this record was raised explicitly and is worth preserving. NFR-10 promises that no
accepted resume is ever lost, and this record then chooses a design with a single point of AI
failure and no fallback. That is deliberate: NFR-10 is a claim about the *system*, not the model.
Work submitted is never lost, no failure of the model takes down sign-in, the dashboard, or an
in-flight batch, and every resume the model could not judge ends in an honest state a human can
act on. A fallback model would have made a different claim — that a score is always produced —
at the price of scores that are not comparable to each other. We would rather be slow and
consistent than fast and incoherent.

Self-hosting was the position the team was most reluctant to reject; it is recorded as the first
thing to reconsider if hardware appears, and the AI Service boundary exists partly to keep that
door open.
