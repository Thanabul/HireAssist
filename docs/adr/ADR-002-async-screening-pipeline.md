# ADR-002: One queued message per resume for batch screening

**Date:** 2026-09-11
**Deciders:** Patiphon Puntusin, Thanabul Parodom, Thanwarat Korcharoenkiat, Rerngrit Jangsri

> In the context of UC-2, facing a batch of resumes whose per-file processing takes seconds to
> minutes and depends on an external model that will fail, we decided to make each resume an
> independently queued unit of work on RabbitMQ with bounded retry and a dead-letter path, to
> achieve throughput that rises with the number of workers and a batch that survives partial
> failure and an LLM outage without losing work, accepting that results become eventually
> consistent and that a resume may occasionally be processed — and paid for — twice.

---

## Summary

### Issue

UC-2 is the use case the whole project exists for, and it is the one that cannot be built the
obvious way.

A recruiter drops 20–200 resumes onto an open position. Each one has to be parsed out of a PDF
— UC-2 accepts nothing else, and a non-PDF file is rejected at upload before any of this begins
(FR-2.1) — normalised into a Candidate Profile, scored against weighted criteria, and given a
written justification. The scoring step is at least one LLM call: seconds when things are
healthy, tens of seconds for a long resume, and unbounded when the provider is rate-limiting.
A batch of 200 is therefore minutes of work in the good case. No HTTP request survives that, and
no recruiter should be watching a spinner while it happens — the proposal commits to accepting
the batch immediately and filling the screen in progressively.

Failure is not the exceptional path here, it is the normal one. UC-2's own alternate flows
already name three kinds: a corrupt file or a scanned image with no text layer (3a), the scoring
service being unavailable (4a), and results a recruiter needs to override (6a). To those, running
against a hosted model adds rate limits, timeouts, and truncated responses. In a batch of 200,
something failing is close to certain.

What makes the design question sharp is the unit of failure. A recruiter who uploads 200 resumes
and receives nothing because file 147 was a scanned image has been failed by the system. Getting
199 results and one entry marked *needs manual review* is not a degraded outcome — it is the
correct outcome.

This is also where the project's demonstrated software quality attribute lives. The attribute
is **Scalability**, and NFR-07 is its measurement: batch throughput must rise in proportion as
screening workers are added. Alongside it, NFR-10 requires that no accepted resume is ever lost.
Both are claims about this pipeline, both can be falsified here, and — as the argument below
makes explicit — the second is what keeps the first honest.

### Decision

**Each resume is one message. The batch is a count, not a unit of work.**

1. **Accept and return.** Hiring Service validates the upload — rejecting anything that is not a
   PDF (FR-2.1) — stores the files, creates a `ScreeningBatch` row with one `pending` entry per
   resume, publishes one `screening.requested` message per resume, and responds `202 Accepted`
   with the batch ID within the two seconds NFR-04 allows, independent of batch size. The
   recruiter is never blocked.
2. **Consume in parallel.** Resume Processing Service runs N replicas, each with a bounded
   prefetch. One message is one resume: parse → `ScoreProfile` over gRPC → persist the result →
   publish `screening.result.ready`. Concurrency is changed by changing N, and nothing else.
3. **Guarantee delivery, not exactly-once.** Durable quorum queues, persistent messages,
   publisher confirms on the Hiring side, and manual acknowledgement only after the result is
   committed. A consumer that crashes mid-resume has not acknowledged, so the message is
   redelivered — at-least-once, deliberately.
4. **Make redelivery harmless.** Results are written keyed on `(batch_id, resume_id)` as an
   upsert, so a redelivered message overwrites its own earlier result rather than creating a
   second one.
5. **Classify failures before retrying.** A *permanent* failure — a corrupt file, or a scanned
   image with no extractable text layer — is never retried; the entry goes straight to
   `needs_manual_review` with the reason (an unsupported format never gets this far: it was
   rejected at upload). A *transient* failure — HTTP 429, 5xx, a broken connection, or a scoring
   attempt that exceeds the 60-second bound NFR-02 sets — is retried up to a bounded number of
   attempts with exponential backoff and jitter, implemented with a delay queue and a per-message
   attempt count.
6. **Dead-letter what does not recover.** Once the retry budget is exhausted the message is
   dead-lettered to `screening.dlq` and the entry is marked `needs_manual_review` with the last
   error recorded. Dead-lettered work is visible to an operator and replayable; it is never
   silently scored zero and never silently dropped.
7. **Completion is a computed state.** A batch is complete when every entry has reached a
   terminal state — `scored` or `needs_manual_review` — and reaching it is what triggers the
   batch-finished notification FR-2.12 requires. There is no all-or-nothing outcome. A periodic
   reconciliation sweep re-publishes entries that have sat `pending` past a threshold, which is
   the only defence against a message that vanishes without a trace.
8. **Stream results to the screen.** `screening.result.ready` events drive the shortlist view
   over server-sent events, so the ranking fills in as results land rather than appearing at the
   end.

**The broker is RabbitMQ**, with quorum queues for durability, a dead-letter exchange for
exhausted work, and a delay queue for backoff.

### Status

**Accepted**

### Group

Communication · Scalability · Reliability

---

## Details

### Assumptions

- A batch is 20–200 resumes; a resume file is at most 10 MB (NFR-08) and usually far smaller.
  Nothing here assumes tens of thousands of files, and the design would need revisiting if it did.
- The LLM provider will be unavailable or rate-limiting some of the time, and there is no
  fallback model to switch to ([ADR-004](ADR-004-llm-access.md)). Waiting is the only recovery.
- Scoring one resume is independent of scoring any other. Nothing in UC-2 requires cross-resume
  context, so ordering does not matter and parallelism is free.
- Re-running a resume through the model costs money but is otherwise harmless — the output is
  regenerable, not authoritative.
- Recruiters tolerate a batch that fills in over minutes, provided they can see it progressing.
  NFR-06 bounds "minutes" at ten for 100 resumes on four workers. This is an assumption about
  users that we have not validated (see `docs/CONTEXT.md`).

### Constraints

- The course requires at least one service communicating through a message broker
  (`docs/course/REQUIREMENTS.md`), and two load tests with an explanation of the results.
- NFR-04, NFR-06, NFR-07 and NFR-10 (`docs/NON-FUNCTIONAL-REQUIREMENTS.md`) fix the numbers this
  design must hit: a two-second acknowledgement, 100 resumes in ten minutes on four workers,
  throughput proportional to worker count, and no accepted resume ever lost.
- The service boundary this queue crosses was fixed by [ADR-001](ADR-001-service-decomposition.md).
- UC-2's stated behaviour is binding (FR-2.2, FR-2.4, FR-2.6, FR-2.7, FR-2.12): return a batch ID
  immediately, process each resume independently, update the ranking as results arrive, flag
  unreadable files without affecting the rest of the batch, retry a failing scorer and fall back
  to *needs manual review* rather than a zero score, and tell the Recruiter when the batch is done.

### Positions

1. **Synchronous REST — the recruiter waits for the batch.**
2. **One message per batch** rather than per resume: the consumer loops over 200 resumes inside a
   single message.
3. **RabbitMQ** (chosen) — a task queue with per-message acknowledgement, retry and dead-lettering.
4. **Apache Kafka** — a partitioned, replayable log; the default answer in most microservice
   coursework.
5. **NATS JetStream** — light, Go-native, fast to stand up.
6. **A PostgreSQL job table polled by workers** (`SELECT … FOR UPDATE SKIP LOCKED`), with no
   broker at all.

### Argument

**Why not synchronous (1).** It fails on the first resume: the request outlives any sane gateway
timeout, there are no partial results, there is nowhere to retry from, and the recruiter's
browser becomes the thing holding the state of a five-minute job. It also makes the LLM's
availability the API's availability.

**Why per-resume rather than per-batch (2).** This is the decision that matters most in this
record, and it is the one that is easy to get wrong because per-batch looks simpler. With one
message per batch: a single corrupt file fails the message, and a retry re-processes all 200
resumes — re-paying every LLM call already made. There is no concurrency inside a batch without
building a second, in-process work distributor. Progress cannot be reported. And a batch stuck
behind one pathological file blocks the consumer that holds it. Per-resume messages make the
failure unit the same size as the failure: one bad resume damages one result.

**Why RabbitMQ over Kafka (4).** Kafka is an ordered, replayable log, and our workload is none of
those things — unordered, independent tasks that need per-message retry and a place to put work
that will not succeed. Kafka gives neither natively: retry and DLQ are assembled from additional
topics and consumer logic. Worse, its consumption model is per-partition and ordered, so one
resume that takes five minutes blocks every message behind it in the same partition —
head-of-line blocking, which is exactly the failure mode this ADR exists to prevent. RabbitMQ's
model — a message, an ack, a bounded prefetch, a dead-letter exchange — is the shape of the
problem. It also costs less to run, which matters when six services and two databases are
already sharing a cluster.

**Why RabbitMQ over NATS JetStream (5).** JetStream would work and is pleasant in Go. Two things
decided it: nobody on the team has used either, so familiarity was not a tiebreaker, and
RabbitMQ's management UI makes queue depth, consumer count, redelivery and the dead-letter queue
visible in a browser. We have to *demonstrate* the reliability attribute, not merely have it —
showing a marker the DLQ filling during an injected outage and draining afterwards is worth more
than a metric in a log file.

**Why a broker at all, over a database job table (6).** Honest answer first: `SKIP LOCKED` on
PostgreSQL is a genuinely good pattern, and with one fewer moving part it would be defensible
here. It loses on two counts. The course requires a message broker, and — independently — the
polling table puts the batch workload's contention on the same PostgreSQL instance that serves
the recruiter-facing transactional reads, which is exactly the coupling
[ADR-001](ADR-001-service-decomposition.md) drew a boundary to avoid. Under the load test we
intend to run, the database would be measuring itself — and NFR-03's two-second ranked list
would be competing with the batch for the same locks.

**How this delivers the quality attribute.** Scalability here means one falsifiable claim,
NFR-07: *add screening workers and batch throughput rises in proportion.* The per-resume message
is what makes it true — there is no in-process work distributor to saturate, no batch-level lock,
and no ordering constraint, so the fourth consumer is as useful as the first, until the model
provider's rate limit rather than our design becomes the ceiling. The comparative load test the
course requires runs the same 100-resume burst at one, two and four workers and plots completion
time against worker count; NFR-06's ten-minute target at four workers is the pass mark.

The second load test is the one that keeps the first honest: NFR-10's fault-injection test, with
the model provider deliberately failed for a period — zero lost messages, retries backing off,
the dead-letter queue receiving exactly the work that exhausted its budget, and the batch
completing once the provider returns. Throughput that is bought by dropping work is not
throughput, and a scalability demonstration that cannot show this second graph has not shown the
first.

### Implications

**What this buys us**

- A batch degrades resume by resume instead of failing whole. UC-2's alternate flows 3a and 4a
  stop being special-case error handling and become ordinary states of an entry.
- Throughput is a deployment parameter: more consumers, more concurrency, no code change. NFR-06
  and NFR-07 are met by configuration, which is what makes Scalability demonstrable live rather
  than only in a report.
- An LLM outage becomes latency rather than data loss, which is what makes
  [ADR-004](ADR-004-llm-access.md)'s decision to run without a fallback model survivable.
- The dead-letter queue turns silent failure into visible failure — the single most valuable
  property in a system whose output a recruiter is trusting.

**What it costs us**

- **At-least-once means occasionally twice.** A consumer that dies after calling the model but
  before acknowledging will re-score that resume, and we pay for the call again. The upsert makes
  the data correct; it does not make the bill correct.
- **Results are eventually consistent, and the UI has to say so.** There is no moment when the
  answer is complete unless the screen tracks it, so UC-2's ranked list must present progress and
  a partial ordering. Ranking is computed at read time from whatever has landed, never from
  arrival order.
- **"Is this batch finished?" is now a derived question** that can be answered wrongly. A message
  lost between publish and consume leaves an entry `pending` forever; the reconciliation sweep in
  the decision exists solely to bound that, and it is extra machinery that must be written and
  tested or the guarantee is decorative.
- **The broker becomes a single point of failure for screening.** RabbitMQ down means no batch
  progresses. We accept a single node for the term project and record it as a known risk for the
  risk matrix rather than pretending a cluster is in scope.
- **The dead-letter queue needs an owner and a replay tool.** Without one it becomes a place
  failures go to be forgotten, which is worse than not having it — it converts a visible failure
  into a filed one.
- **Publisher confirms plus per-resume messages make the accept path chattier**: 200 confirmed
  publishes inside the request that must return quickly. Publishing needs to be batched or moved
  behind the response, or the "immediate 202" claim quietly stops being true at the top of the
  range.

---

## Related

### Related decisions

- [ADR-001](ADR-001-service-decomposition.md) — established the Hiring / Resume Processing
  boundary this queue crosses and the AI Service the consumer calls.
- [ADR-004](ADR-004-llm-access.md) — the absence of a fallback model is why the retry and
  dead-letter policy here has to be as explicit as it is.
- [ADR-003](ADR-003-polyglot-persistence.md) — the per-resume result document written on each
  successful consume.

### Related requirements

- **Use cases:** UC-2 in full — main flow steps 2 (immediate batch ID), 3–4 (concurrent parse and
  score), 5 (streamed results and batch-finished notification); alternate flows 3a (unreadable
  file), 4a (scorer unavailable → retry → *needs manual review*, never a silent zero). UC-4
  consumes the domain events this pipeline publishes. D-1 would reuse the same queue shape over
  the talent pool.
- **Functional requirements** (`docs/FUNCTIONAL-REQUIREMENTS.md`): FR-2.1 (PDF only — the
  validation that happens before the queue); FR-2.2 (acknowledge without waiting); FR-2.4 (each
  resume independent — the per-resume message is this requirement made structural); FR-2.6
  (ranking updated as results arrive); FR-2.7 (retry, then manual review, excluded from the
  ranking rather than scored); FR-2.12 (batch-finished notification, emitted from the computed
  terminal state).
- **Non-functional requirements** (`docs/NON-FUNCTIONAL-REQUIREMENTS.md`): NFR-02 (the 60-second
  abandon-and-retry bound is the definition of a transient failure here); NFR-04 (two-second
  acknowledgement, independent of batch size); NFR-06, NFR-07 and NFR-08 (throughput, its
  proportionality to worker count — **the demonstrated quality attribute** — and the burst it must
  sustain); NFR-10 (no accepted resume lost, verified by fault injection).
- **Course requirements** (`docs/course/REQUIREMENTS.md`): the message-broker service; the two
  load tests and their explanation (the NFR-07 comparative test and the NFR-10 fault-injection
  test); the demonstrated software quality attribute (**Scalability**); and the risk matrix, to
  which this ADR contributes the single-broker and provider-outage risks.

### Related artifacts

`docs/PROPOSAL.md` — UC-2 and the Non-functional Requirements section. The load-test plan and the
risk matrix, when written, are both derived from this record.

### Related principles

- *Explainability is required, not optional* — which is why an unscored resume is marked
  *needs manual review* with a reason instead of receiving a zero that would silently rank it
  last.
- *The human still decides* — work that the system cannot judge is handed back to a person, not
  guessed at.

---

## Notes

This record was first drafted with *Reliability* as the quality attribute the project
demonstrates, on the argument that never losing work is the design's most distinctive property.
It was re-pointed at *Scalability* the same day, when it was rebased onto the requirements work
that had already chosen NFR-07 as the course measurement. Nothing in the Decision changed — the
per-resume queue delivers both — and the reliability claim survives intact as NFR-10 and its
fault-injection test, which the Argument now treats as the check on the scalability numbers
rather than as a separate claim. The reasons Scalability was kept, beyond not overturning a
teammate's merged decision for no design gain, are in the changelog entry of 2026-09-11.

We briefly considered making the retry budget generous enough to ride out any plausible provider
outage — hours rather than minutes — so that nothing would ever reach manual review for
availability reasons. It was rejected because it hides the outage: a recruiter would see a batch
that never finishes and no explanation. A bounded budget followed by an explicit
*needs manual review* state tells the truth, and the truth is recoverable — the entries can be
replayed once the provider is healthy.

Redis Streams was raised and dismissed without much discussion: we do not currently run Redis
([ADR-003](ADR-003-polyglot-persistence.md)), and adopting a datastore in order to use its
queueing as a side effect is the wrong order of reasoning.
