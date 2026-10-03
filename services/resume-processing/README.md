# Resume Processing Service (REST CRUD)

Owns candidate profiles for HireAssist.

- Exposes **REST**: per ADR-007, only the AI Service speaks gRPC.
- Stores data in **MongoDB**: per ADR-003, a candidate profile is an AI-derived document whose shape changes with the prompt.
- Stack: Node.js 18+, Express, Mongoose.

## Owners

| Role | Name |
|---|---|
| Primary | T |
| Secondary | _to be named by the team_ |

ADR-005 asks every service to name a primary and a secondary owner, and the secondary must be able to build, run and deploy it.

## Files

| File | Purpose |
|---|---|
| `server.js` | The service: REST endpoints backed by MongoDB |
| `openapi.yaml` | The REST contract for this service (ADR-005) |
| `client.js` | Demo script that walks through CRUD, pausing after each step |
| `Dockerfile` | Container image (ADR-005) |
| `k8s/resume-processing.yaml` | Kubernetes Deployment and ClusterIP Service (ADR-001) |

## Endpoints

| Method | Path | Action |
|---|---|---|
| POST | `/candidates` | Create |
| GET | `/candidates/:id` | Read one |
| GET | `/candidates?jobOpeningId=job-001` | Read list |
| PUT | `/candidates/:id` | Update (only the fields sent) |
| DELETE | `/candidates/:id` | Delete |
| GET | `/healthz` | Liveness: the process is up |
| GET | `/readyz` | Readiness: `200` once MongoDB is connected, `503` before |

Candidate ids are short and readable: `cand-001`, `cand-002`, … (the next number after the highest existing id), so they are easy to tell apart from job opening ids such as `job-001`. This keeps the demo easy to follow; it assumes one writer at a time.

Every response carries an `X-Correlation-Id` header. Send one to reuse it; otherwise the service generates one. Logs are one JSON object per line with `time`, `level`, `service`, `msg`, and for requests `correlation_id`, `method`, `path`, `status`, `duration_ms`.

## Run locally

1. `npm install`
2. Point it at MongoDB. For Atlas: `export MONGO_URL='mongodb+srv://<user>:<password>@<cluster>/'`. Without `MONGO_URL` it connects to `mongodb://127.0.0.1:27017`. `PORT` (default `3000`) and `MONGO_DB` (default `hireassist_resume_processing`) are optional.
3. `npm start`, then wait for the `Resume Processing Service running` and `Connected to MongoDB` log lines.
4. In a second terminal, either run `npm run client`, or call the API with curl:

```bash
# Create
curl -X POST http://localhost:3000/candidates -H "Content-Type: application/json" \
  -d '{"workspace_id":"ws-demo","job_opening_id":"job-001","full_name":"Thanabul Parodom","email":"thanabul.p@example.com","skills":["Java","Spring Boot","PostgreSQL"],"resume_text":"4 years as a backend developer at a fintech startup in Bangkok"}'

# Read one / read list
curl http://localhost:3000/candidates/cand-001
curl "http://localhost:3000/candidates?jobOpeningId=job-001"

# Update
curl -X PUT http://localhost:3000/candidates/cand-001 -H "Content-Type: application/json" \
  -d '{"skills":["Java","Spring Boot","PostgreSQL","Docker"],"resume_text":"5 years as a backend developer at a fintech startup in Bangkok"}'

# Delete
curl -X DELETE http://localhost:3000/candidates/cand-001
```

## Run in Docker / Kubernetes

```bash
docker build -t hireassist/resume-processing:1.0.0 .
docker run -p 3000:3000 -e MONGO_URL='mongodb+srv://...' hireassist/resume-processing:1.0.0
```

For Kubernetes, create the `resume-processing-mongo` Secret described at the top of `k8s/resume-processing.yaml`, then `kubectl apply -f k8s/resume-processing.yaml`. Inside the cluster the service is reached at `http://resume-processing.hireassist.svc`.

## Known gaps

- **Workspace enforcement (ADR-001).** ADR-001 requires every service to enforce the caller's workspace, not just receive it. This service stores `workspace_id` but does not yet check it on reads, updates or deletes. To be added once the team fixes how workspace identity travels on internal calls (header name).
- **Shared contract location (ADR-005).** ADR-005 wants all schemas in one place; where that is has not been decided, so `openapi.yaml` lives in this folder for now.
- **AI Service not called yet** (agreed in the group as demo scope).
- **Candidate identity in MongoDB.** ADR-003 puts candidate identity and retention dates in PostgreSQL; the demo keeps everything in MongoDB.
- **OpenTelemetry tracing.** The correlation id is propagated and logged, but traces are not exported yet.
