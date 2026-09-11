# Architecture Decision Records

Each significant architectural decision is recorded here using
[TEMPLATE.md](TEMPLATE.md), which follows the **Jeff Tyree & Art Akerman** decision record
template from the course slides — grouped as *Summary · Details · Related · Notes*, with
optional fields marked in the template.

The course requires **at least 3 ADRs** as part of the project proposal submission.

---

## Index

| ID | Decision | Status | Date |
|---|---|---|---|
| — | _No ADRs recorded yet._ | — | — |

---

## Candidate decisions

Identified from the architecturally significant requirements in
[../NON-FUNCTIONAL-REQUIREMENTS.md](../NON-FUNCTIONAL-REQUIREMENTS.md) and from open questions in
[../CONTEXT.md](../CONTEXT.md).

| Decision | Forced by |
|---|---|
| Tiered screening pipeline — deterministic filter before the model? | NFR-02, NFR-06, NFR-08 |
| Third-party model provider vs. self-hosted model | NFR-13, NFR-14 |
| Queue topology, worker scaling and delivery guarantee for batch screening | NFR-07, NFR-10 |
| Where the scorer boundary is drawn, and how per-criterion evidence is persisted | NFR-15, NFR-17 |
| Erasure cascade — orchestration or choreography | FR-5.5, FR-5.11 |
| Service discovery mechanism | Course requirement |
| Datastore split — which RDBMS, which NoSQL, what belongs in each | Course requirement |
| Resume ingestion channel — upload only, or an automated adapter | Open question |

---

## Conventions

- File name: `ADR-NNN-short-slug.md`, numbered sequentially from `001`.
- Numbers are never reused, even if an ADR is superseded or withdrawn.
- Superseding an ADR does not edit the original — set its status to
  *Superseded by ADR-NNN* and write a new one.
- Add a row to the index in the same commit that adds the ADR.
