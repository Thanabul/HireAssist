# Hiring Service

The recruiter-facing hiring record. This first slice covers **job openings** (UC-1): the
operations `createJobOpening()`, `getJobOpening()`, listing, `reviseScreeningCriteria()`,
`pauseOpening()`, `resumeOpening()` and `closeOpening()` from the SOC table. Job openings are
stored in PostgreSQL (ADR-003). Go 1.25; dependencies are `pgx` (the PostgreSQL driver) and
`kin-openapi`, used only by the contract test.

## Running

From the repository root, `docker compose up --build` starts PostgreSQL and the service on
`localhost:8080`. If port 5432 is already taken on your machine, set `POSTGRES_PORT` to another
port, for example `POSTGRES_PORT=55432 docker compose up --build`.

| Variable | Meaning |
|---|---|
| `PORT` | HTTP port, default `8080` |
| `DATABASE_URL` | PostgreSQL connection URL. **Unset means in-memory storage**, lost on restart: fine for a quick `go run`, never for anything you want to keep |

On startup, the service connects and applies `internal/adapter/postgres/schema.sql`. If the
database cannot be reached, startup fails rather than the first request. Every statement in the
schema is idempotent (`CREATE … IF NOT EXISTS`). That is a deliberate stop-gap. Its first
incompatible change needs a real migration tool, which has not been chosen yet.

## Testing

```sh
go test -race ./...          # unit + contract tests; PostgreSQL tests are skipped

# with the compose database running, include the PostgreSQL tests:
HIRING_TEST_DATABASE_URL='postgres://hireassist:hireassist@localhost:5432/hiring_test?sslmode=disable' \
  go test -race ./...
```

The PostgreSQL tests truncate their tables. That is why they use `hiring_test`, a separate
database that compose creates beside `hiring`, and never the one the running service uses.

## Layout: clean architecture, dependencies point inward

```
api/openapi.yaml       the REST contract — authoritative (ADR-005 rule 1); location provisional
cmd/hiring/            main: reads PORT, starts and gracefully stops the server
internal/app/          composition root — the only place concrete adapters are chosen and injected
internal/adapter/
  httpapi/             REST adapter: HTTP ⇄ use case, business errors ⇄ status codes
  postgres/            PostgreSQL JobOpeningRepository + schema.sql — the system of record
  memory/              in-memory JobOpeningRepository, used when DATABASE_URL is unset
  system/              wall Clock (UTC, microseconds — what PostgreSQL stores) and random ids
internal/usecase/      application operations, and the ports they need (repository, clock, ids)
internal/domain/       JobOpening, Criterion and their rules — no dependencies
```

The use case depends only on interfaces it declares itself. `internal/app` picks PostgreSQL or
memory from `DATABASE_URL`, and nothing else knows which one it got. A job opening is one row in
`job_openings`, and each of its criteria is one row in `job_opening_criteria`, kept in order.
`Save` replaces the opening and its criteria in one transaction.

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
- **Role enforcement** (FR-0.4).
- **A readiness endpoint** that checks the database (ADR-005 rule 4 asks for one; only `/healthz`
  exists).
- **A migration tool.** The schema is applied idempotently at startup until the first change that
  cannot be expressed that way.
- Clients generated from the spec — there is no consumer yet.
