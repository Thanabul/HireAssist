# ADR-NNN: <short noun phrase naming the decision>

Copy this file to `ADR-NNN-short-slug.md`, fill it in, and add a row to [INDEX.md](INDEX.md).

---

## Context

What forces are at play, and why a decision is needed *now*. State the problem, the
constraints acting on it (course requirements, PDPA, cost, team skill, time), and the
alternatives considered — including the ones rejected. A reader who knows nothing about the
project should understand why this was a genuine choice rather than an obvious default.

## Decision

The choice made, stated as a single architectural commitment in the present tense —
*"We use X"*, not *"We will investigate X"*. Say why this option beat the alternatives named
above, referring to the forces in Context.

## Status

One of: **Proposed** · **Accepted** · **Superseded by ADR-NNN** · **Deprecated**.

## Consequences

What becomes true because of this decision — good and bad, and both are required. Cover what
becomes easier, what becomes harder, what new risks or obligations this creates, and what it
forecloses. Consequences that are only positive are a sign the trade-off has not been thought
through.

---

## Writing guidance

Drawn from the two samples in [`../reference/`](../reference/).

**A good ADR** (see `adr-sample-good.pdf`)
- Names the real alternatives and says why each was rejected.
- Records a decision about *architecture* — structure, technology, protocol, boundary.
- States honest negative consequences (learning curve, integration risk) alongside the benefits.

**A poor ADR** (see `adr-sample-bad.pdf`) — avoid these:
- The Decision lists **activities**, not a decision: *"We will interview people"*, *"We will
  learn about microservice architecture"*. Those are tasks on a plan. An ADR records a choice
  between options that changes the shape of the system.
- **No alternatives** appear, so nothing was actually decided — there was only one path.
- Consequences describe **project events** ("we made an appointment for a future meeting")
  rather than the architectural implications of the choice.
- The Context states a product question ("can we build a reviews hub?"), which is a scoping
  question, not an architectural force.

**Rules of thumb**
- If you cannot name a rejected alternative, it is probably not an ADR.
- If the decision could be reversed with no structural change to the system, it is probably
  not an ADR.
- Write it when the decision is made, not retroactively before submission — the reasoning is
  the point, and it does not survive being reconstructed later.
- One decision per ADR. If the title needs an "and", split it.
