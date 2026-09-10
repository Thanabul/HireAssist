# Architecture Decision Records

Each significant architectural decision is recorded here using
[TEMPLATE.md](TEMPLATE.md) — format: **Context · Decision · Status · Consequences**.

The course requires **at least 3 ADRs** as part of the project proposal submission.

---

## Index

| ID | Decision | Status | Date |
|---|---|---|---|
| — | _No ADRs recorded yet._ | — | — |

---

## Candidate decisions

Open decisions identified but not yet written up. Tracked in detail in
[../CONTEXT.md](../CONTEXT.md).

- Resume ingestion channel — batch upload only, or an automated email/webhook adapter
- LLM provider and placement, cost bounding, and behaviour when the model is unavailable
- Service decomposition, and which boundary uses REST vs. gRPC vs. the message broker
- Datastore split — which RDBMS, which NoSQL, and what belongs in each
- Async processing model for UC-2 screening batches — queue topology, retry, partial failure
- Scheduler design shared by UC-4 (staleness checks) and UC-5 (retention enforcement)
- Which software quality attribute the project demonstrates for the course requirement

---

## Conventions

- File name: `ADR-NNN-short-slug.md`, numbered sequentially from `001`.
- Numbers are never reused, even if an ADR is superseded or withdrawn.
- Superseding an ADR does not edit the original — set its status to
  *Superseded by ADR-NNN* and write a new one.
- Add a row to the index in the same commit that adds the ADR.
