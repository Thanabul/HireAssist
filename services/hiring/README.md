# Hiring Service

The recruiter-facing hiring record. This first slice covers **job openings** (UC-1): the
operations `createJobOpening()`, `getJobOpening()`, listing, `reviseScreeningCriteria()`,
`pauseOpening()`, `resumeOpening()` and `closeOpening()` from the SOC table. Storage is in memory,
so data is lost on restart. Go 1.25; the one dependency is `kin-openapi`, used only by the
contract test.

```sh
go test -race ./...          # the whole suite
PORT=8080 go run ./cmd/hiring
```

## Layout: clean architecture, dependencies point inward

```
api/openapi.yaml       the REST contract — authoritative (ADR-005 rule 1); location provisional
cmd/hiring/            main: reads PORT, starts and gracefully stops the server
internal/app/          composition root — the only place concrete adapters are chosen and injected
internal/adapter/
  httpapi/             REST adapter: HTTP ⇄ use case, business errors ⇄ status codes
  memory/              in-memory JobOpeningRepository (stand-in for PostgreSQL)
  system/              wall Clock (UTC) and random, unguessable ids
internal/usecase/      application operations, and the ports they need (repository, clock, ids)
internal/domain/       JobOpening, Criterion and their rules — no dependencies
```

The use case depends only on interfaces it declares itself. Replacing the in-memory store with
PostgreSQL means writing one adapter and changing one line in `internal/app`.

## HTTP API

The contract is [`api/openapi.yaml`](api/openapi.yaml). With the service running, browse and try
it in Swagger UI at **`/docs`**; the raw spec is served at `/openapi.yaml`.

**Change the spec first.** `TestHandlerMatchesOpenAPIContract` sends a request to every
operation through the real handler and validates each request and response against the spec. An
undocumented status code, a field the spec does not declare, or a spec operation the server does
not serve all fail it.

| Operation | Request | Success |
|---|---|---|
| `createJobOpening()` | `POST /job-openings` | 201 + `Location` |
| `getJobOpening()` | `GET /job-openings/{id}` | 200 |
| list | `GET /job-openings` | 200, array |
| `reviseScreeningCriteria()` | `PUT /job-openings/{id}/criteria` (array of criteria) | 200 |
| `pauseOpening()` / `resumeOpening()` | `POST /job-openings/{id}/pause` · `/resume` | 200 |
| `closeOpening()` | `POST /job-openings/{id}/close` `{"outcome": "filled" \| "cancelled"}` | 200 |
| health | `GET /healthz` | 200 |

```json
{
  "title": "Backend Engineer",
  "description": "Backend engineer, 3+ years, Go or Python, must have shipped with Kafka.",
  "criteria": [{"name": "3+ years of Go or Python", "classification": "must-have", "weight": 5}],
  "expected_time_to_fill_days": 45
}
```

Errors are `{"error": "..."}`. 400 means a malformed body, 404 an unknown id, 422 a broken
business rule (no criteria, bad weight, unknown outcome), 409 an action the opening's status
forbids (FR-1.9: a closed opening is final), and 500 anything unexpected, with no detail returned.

## Not built yet

- **`proposeJobOpening()`** — the AI proposal step. It becomes a `CriteriaDeriver` port with a
  gRPC adapter to the AI Service (ADR-007).
- **`recordPipelineEvent()`** — reporting openings to the dashboard. The docs say this push needs
  an ADR before it is built.
- **Role enforcement** (FR-0.4) and the **PostgreSQL** adapter (ADR-003).
- Clients generated from the spec — there is no consumer yet.
