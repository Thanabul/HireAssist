# ADR-007: gRPC on the AI Service boundary

**Date:** 2026-09-20
**Deciders:** Patiphon Puntusin, Thanabul Parodom, Thanwarat Korcharoenkiat, Rerngrit Jangsri

> In the context of one internal boundary that carries the highest call volume in the system and
> the narrowest, most load-bearing contract, facing services that may each be written in a
> different language and a contract that changes whenever the model output does, we decided to make
> the AI Service speak gRPC while every other boundary stays REST, to achieve a compiled contract
> and generated clients on both sides instead of two hand-written JSON clients kept in step by
> discipline, accepting a second wire protocol, a code-generation step in every build, and the loss
> of a boundary anyone could debug with `curl`.

---

## Summary

### Issue

One protocol everywhere was chosen to get the boundaries placed before anything else was spent.
That has happened: the services, their data ownership and their collaborations are settled and have
survived an audit. The question now is whether every boundary should keep the same protocol
*because* they were drawn together, and one of them should not.

**The AI Service boundary is not like the others.** Three things separate it.

*Volume.* Every other internal call happens once per job opening, once per batch, or once per
retention sweep. This one happens once per resume — two hundred times for one recruiter action, and
it is the call the system's throughput target is measured against.

*Contract shape.* It is the narrowest interface in the system and the one that must not drift:
*(candidate profile, criteria) → (score, must-have check, justification)*. Every part of that is
load-bearing. A renamed field on one side produces a missing justification or a silently absent
must-have result rather than an error, and a score without its justification is exactly the output
the product exists to prevent.

*Language exposure.* Services may each choose their own language. This boundary is the one most
likely to be crossed by two different ones — the service holding the model credential has the
strongest pull toward Python, and the two services that call it need not follow. A hand-written
JSON client in two languages is two chances to disagree about a field name, and nothing catches it
until a resume scores wrong in production.

Underneath all three: the contract changes whenever the model output does, which is more often than
anything else in the system changes.

### Decision

**The AI Service speaks gRPC. Every other boundary stays REST over HTTP/JSON.**

- Its three operations are defined in a `.proto` as RPCs — criteria extraction from a description,
  scoring a profile against criteria, and generating interview questions. That file is the
  contract; clients and servers are generated from it in whatever language each service is written
  in, and no client for this boundary is written by hand.
- It stays internal. It is not exposed through the gateway and no browser reaches it, which is what
  makes a non-browser-friendly protocol acceptable here and nowhere else.
- Field numbers are never reused and fields are never removed, only deprecated, so an older client
  keeps working against a newer server through a deployment.
- Everything else — client to gateway, gateway to service, and every other service-to-service call
  — is unchanged. This record narrows one boundary, not the rule.

### Status

**Accepted**

### Group

Communication

---

## Details

### Assumptions

- The three model operations are stable in *shape* even though their content evolves: a profile and
  criteria in, a structured judgement out. If that shape turned out to change too, no contract
  mechanism would help.
- Every language a service might be written in has a maintained gRPC implementation. This is true
  of every mainstream candidate and is a gate on any unusual one.
- Call volume stays in the range of a few hundred per batch. gRPC is not being adopted for
  performance; the provider's own latency dominates anything the wire format contributes.
- Four people can carry one code-generation step in the build. Two would be a different decision.

### Constraints

- A gRPC service is required of us, and no boundary currently provides one. This record closes half
  of a gap that was recorded as deliberate rather than accidental; the message-broker half remains
  open.
- The boundary this applies to, and the rule that every boundary was REST, were set by
  [ADR-001](ADR-001-service-decomposition.md). This record overrides that rule for this one
  boundary and leaves the rest of it standing.
- The three operations themselves, and the requirement that the service is never reachable from the
  gateway, were fixed by [ADR-004](ADR-004-llm-access.md) and are not reopened here.
- Whatever is chosen must work across more than one implementation language, because language is a
  per-service choice.

### Positions

1. **Keep REST on every boundary**, holding the line set when the boundaries were drawn.
2. **gRPC on the AI Service boundary only** *(chosen)*.
3. **gRPC on every internal call**, REST only at the gateway.
4. **Keep REST, but generate the clients** from an OpenAPI document instead of writing them.
5. **GraphQL** for the internal calls.

### Argument

**Against holding the line (1).** The reason for one protocol was that boundaries are expensive to
get wrong and protocols are not — so place the boundaries first and pay for protocol variety later.
That argument does not say *never*; it says *not yet*. The boundaries are now placed and audited,
so the condition it was waiting on has been met. Keeping REST here would mean maintaining two
hand-written JSON clients across a language boundary for the highest-volume, least forgiving
contract in the system, which is precisely the case the deferral was meant to be revisited for.

**Why this boundary and not the others (3).** Erasure, the screening hand-off and the pipeline
pushes are low-volume, their shapes change rarely, and two of them are how services tell each other
work has happened rather than requests for a computed answer. Converting them buys little and costs
a second toolchain on every path, including the callback into the service that started the work.
The AI boundary earns the exception on all three counts the others fail: volume, contract
fragility, and the likelihood of two languages meeting across it.

**Against generated REST clients (4) — the closest alternative and the one that nearly won.** It
delivers the main benefit, generated clients, without a second wire protocol, and the discipline of
writing the contract before the endpoint is already required of us. It was rejected because the
document stays advisory: the generated client believes the document, the server can return
something else, and the two only disagree at runtime. With protobuf the schema *is* the wire
format, so a response that does not match the contract cannot be produced in the first place. On
the boundary where a missing field silently becomes a missing justification, that difference is the
whole point. Generator maturity across languages is also uneven in a way protobuf's is not.

**Against GraphQL (5).** It solves over-fetching across a graph of related resources, which is not
this problem. This is one call with a fixed input and a fixed answer.

**On "easier to consume", which is worth stating plainly** because it is the reason people usually
reach for the opposite conclusion. For a browser, an outside integrator, or anyone holding `curl`,
REST is easier and gRPC is worse — no network tab, no readable payload, a toolchain before the
first request. That cost is real and this boundary avoids it only because it has none of those
consumers: it is internal, and it is never exposed through the gateway. *Inside* the system, "easy
to consume" means a caller gets a typed client it did not write and cannot get wrong, which is what
this buys. If the AI Service ever needs an external consumer, that consumer gets a REST façade in
front of it and this decision is revisited.

### Implications

**What this buys us**

- The contract is a compiled artifact. A field renamed on one side fails at build time in the
  other, instead of producing a plausible-looking score with no justification attached.
- Neither side writes a client. Adding a third caller later costs a generation step, not a new
  hand-rolled client and a new set of bugs.
- Two languages can meet on this boundary safely, which is what makes per-service language choice
  affordable rather than theoretical.
- Streaming is available if a long generated answer should arrive incrementally. Nothing needs it
  today; it stops being a future rewrite.
- One of the two communication styles still owed is now delivered.

**What it costs us**

- **A second wire protocol, and it lands on the team, not just the code.** Everyone who debugs
  scoring now needs a gRPC client to see a request. The browser network tab, which shows every
  other call in the system, shows nothing here.
- **A code-generation step in every build** for every language a caller is written in, plus the
  `.proto` itself needing a home and an owner. Where shared contract definitions live is an open
  question this decision makes urgent rather than answers.
- **The rule "every boundary is REST" is no longer true**, so anything stating it as a blanket fact
  is now wrong, and every diagram and table showing collaborations has two protocols to mark
  instead of one. A uniform rule is cheaper to hold than a rule with one exception, and the
  exception has to keep earning it.
- **The guardrail that every boundary is defined by an OpenAPI document needs a second arm** for
  the boundary that now has a `.proto` instead. One contract mechanism becomes two.
- **A local demo needs the generated stubs present**, so a checkout that has not run the generator
  does not build. That is a new way for a new team member's first day to go wrong.
- **It reverses part of a decision taken nine days ago.** Whatever the argument, a reader is
  entitled to ask whether the first decision was made too quickly, and the honest answer is in the
  Notes.

---

## Related

### Related decisions

- [ADR-001](ADR-001-service-decomposition.md) — set one protocol on every boundary and named this
  call as the first place to revisit if a boundary demonstrated it needed something else. **This
  record overrides that rule for the AI Service boundary only**; it stands everywhere else.
- [ADR-004](ADR-004-llm-access.md) — defined the three operations and made the service unreachable
  from the gateway. This record changes how they are carried, not what they are or who may call
  them.
- [ADR-005](ADR-005-per-service-language.md) — per-service language choice is the force that makes
  a generated contract worth paying for, and its contract guardrail now covers two mechanisms.
- **Still open, and made more pressing:** where shared contract definitions live in the repository,
  and who owns the `.proto`.

### Related requirements

- **Criteria extraction from a free-text description** (UC-1, the use case for creating a job
  opening), **scoring with a justification** (UC-2, batch screening) and **interview question
  generation** (UC-3) are the three operations this boundary carries. FR-1.2, FR-2.5 and FR-3.3 —
  the derived criteria, the score with its must-have check and written justification, and each
  question tagged with the criterion it tests — are the fields the contract must not lose.
- **NFR-17** — the model and prompt change inside one service; a versioned contract is what keeps
  that true for callers when the shape of the output shifts with it.
- **NFR-06, NFR-07, NFR-08** — screening throughput and its proportionality to worker count. This
  is the call on that path; the wire format is not the bottleneck, but a broken contract stops the
  measurement entirely.
- Required of us: a service reached by gRPC, which this provides. The service driven by a message
  broker is still not provided.

### Related artifacts

The `.proto` defining these three RPCs, once written, and the generated clients in each calling
service. Any diagram or table of collaborations now marks two protocols.

### Related principles

- *Explainability is required, not optional* — the justification and the per-criterion evidence
  travel on this boundary, and a contract that can lose a field quietly is a contract that can lose
  an explanation quietly.
- *Easily reversible* — the three operations are domain-shaped, not model-shaped and not
  protocol-shaped. Putting REST back, or a façade in front, changes the transport and leaves the
  interface intact.

---

## Notes

This narrows a decision taken nine days earlier, and that deserves an answer rather than a
footnote. The earlier record did not claim REST everywhere was permanent; it argued that boundaries
are expensive to move and protocols are not, so boundaries should be placed first and protocol
variety bought afterwards, and it named this call as the first candidate. What has changed is that
the boundaries are now settled. We are converting on the cross-language and contract-fragility
argument rather than waiting to be bitten by drift in production, which the earlier record
described as the trigger. Acting before the failure rather than after it is the intended use of a
deferral, not a reversal of it.

The honest tension is the requirement. A gRPC service is expected of us and none existed, so this
record is convenient as well as correct. What makes it defensible is that the boundary was not
chosen to satisfy the requirement: it is the one the earlier record already identified, on
properties — volume, contract fragility, language exposure — that would hold if the requirement did
not exist. Had the requirement pointed at a different boundary, this record would still point here.

The message-broker half of that obligation remains open, and should not be closed the same way. The
place it would earn its keep is already identified — the pipeline events a service currently pushes
synchronously into the write path of another, where a dropped call leaves a permanently wrong
number and nothing to reconcile against. That is a real problem looking for a broker, and it
deserves its own record when it is taken.
