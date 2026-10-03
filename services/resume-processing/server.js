// Resume Processing Service (REST)
// ADR-007: only the AI Service speaks gRPC; every other service exposes REST.
// ADR-003: candidate profiles are AI-derived documents, so they live in MongoDB.
// ADR-005: structured JSON logs, a correlation id on every call, health and
//          readiness endpoints, configuration from the environment.

const crypto = require("crypto");
const express = require("express");
const mongoose = require("mongoose");

const SERVICE = "resume-processing";

// ---------- 0. Structured JSON logs (ADR-005) ----------
function log(level, msg, fields = {}) {
  console.log(JSON.stringify({ time: new Date().toISOString(), level, service: SERVICE, msg, ...fields }));
}

// ---------- 1. Connect to MongoDB ----------
// Configuration comes from the environment (ADR-005).
// Set MONGO_URL for MongoDB Atlas; without it, connect to a local MongoDB.
const MONGO_URL = process.env.MONGO_URL || "mongodb://127.0.0.1:27017";
const DB_NAME = process.env.MONGO_DB || "hireassist_resume_processing";

mongoose
  .connect(MONGO_URL, { dbName: DB_NAME })
  .then(() => log("info", "Connected to MongoDB", { database: DB_NAME }))
  .catch((err) => {
    log("error", "MongoDB connection failed", { error: err.message });
    process.exit(1);
  });

// ---------- 2. Candidate profile model ----------
const candidateProfileSchema = new mongoose.Schema({
  _id: { type: String }, // short readable id: "cand-001", "cand-002", ...
  workspaceId: { type: String, required: true },
  jobOpeningId: { type: String, required: true },
  fullName: { type: String, required: true },
  email: { type: String, required: true },
  skills: { type: [String], default: [] },
  resumeText: { type: String, default: "" },
  createdAt: { type: Date, default: Date.now },
});

const CandidateProfile = mongoose.model("CandidateProfile", candidateProfileSchema);

// Next short id: highest existing "cand-NNN" + 1, starting at "cand-001".
// Simplified for the demo: fine for one recruiter at a time, not for concurrent writes.
async function nextId() {
  const last = await CandidateProfile.findOne({ _id: { $regex: /^cand-\d{3}$/ } }).sort({ _id: -1 });
  const n = last ? parseInt(last._id.slice(5), 10) + 1 : 1;
  return "cand-" + String(n).padStart(3, "0");
}

// Stored document -> API response
function toOutput(doc) {
  return {
    id: doc._id,
    workspace_id: doc.workspaceId,
    job_opening_id: doc.jobOpeningId,
    full_name: doc.fullName,
    email: doc.email,
    skills: doc.skills,
    resume_text: doc.resumeText,
    created_at: doc.createdAt.toISOString(),
  };
}

// ---------- 3. App, correlation id and request log ----------
const app = express();
app.use(express.json());

// Every call carries a correlation id (ADR-005): reuse the caller's, or start one.
app.use((req, res, next) => {
  const correlationId = req.get("X-Correlation-Id") || crypto.randomUUID();
  res.set("X-Correlation-Id", correlationId);
  const started = Date.now();
  res.on("finish", () => {
    if (req.path === "/healthz" || req.path === "/readyz") return; // keep probe noise out of the logs
    log("info", "request", {
      correlation_id: correlationId,
      method: req.method,
      path: req.originalUrl,
      status: res.statusCode,
      duration_ms: Date.now() - started,
    });
  });
  next();
});

// ---------- 4. Health and readiness (ADR-001, ADR-005) ----------
// Liveness: the process is up.
app.get("/healthz", (req, res) => res.json({ status: "ok" }));

// Readiness: only take traffic once MongoDB is connected (Kubernetes readiness probe).
app.get("/readyz", (req, res) => {
  const ready = mongoose.connection.readyState === 1;
  res.status(ready ? 200 : 503).json({ status: ready ? "ready" : "not ready" });
});

// ---------- 5. REST endpoints (contract: openapi.yaml) ----------
//   POST   /candidates                        Create
//   GET    /candidates/:id                    Read one
//   GET    /candidates?jobOpeningId=job-001   Read list
//   PUT    /candidates/:id                    Update
//   DELETE /candidates/:id                    Delete
const NOT_FOUND = { error: "Candidate profile not found" };

// Shared error handling: a malformed id is treated as not found
const handle = (fn) => async (req, res) => {
  try {
    await fn(req, res);
  } catch (err) {
    if (err.name === "CastError") return res.status(404).json(NOT_FOUND);
    if (err.name === "ValidationError") return res.status(400).json({ error: err.message });
    log("error", "request failed", { path: req.originalUrl, error: err.message });
    res.status(500).json({ error: err.message });
  }
};

// Create
app.post("/candidates", handle(async (req, res) => {
  const { workspace_id, job_opening_id, full_name, email, skills, resume_text } = req.body;
  const doc = await CandidateProfile.create({
    _id: await nextId(),
    workspaceId: workspace_id,
    jobOpeningId: job_opening_id,
    fullName: full_name,
    email,
    skills,
    resumeText: resume_text,
  });
  res.status(201).json(toOutput(doc));
}));

// Read one
app.get("/candidates/:id", handle(async (req, res) => {
  const doc = await CandidateProfile.findById(req.params.id);
  if (!doc) return res.status(404).json(NOT_FOUND);
  res.json(toOutput(doc));
}));

// Read list, optionally filtered by job opening
app.get("/candidates", handle(async (req, res) => {
  const filter = req.query.jobOpeningId ? { jobOpeningId: req.query.jobOpeningId } : {};
  const docs = await CandidateProfile.find(filter).sort({ createdAt: -1 });
  res.json({ profiles: docs.map(toOutput) });
}));

// Update: only the fields that are sent are changed
app.put("/candidates/:id", handle(async (req, res) => {
  const { full_name, email, skills, resume_text } = req.body;
  const changes = {};
  if (full_name !== undefined) changes.fullName = full_name;
  if (email !== undefined) changes.email = email;
  if (skills !== undefined) changes.skills = skills;
  if (resume_text !== undefined) changes.resumeText = resume_text;

  const doc = await CandidateProfile.findByIdAndUpdate(req.params.id, changes, { new: true });
  if (!doc) return res.status(404).json(NOT_FOUND);
  res.json(toOutput(doc));
}));

// Delete
app.delete("/candidates/:id", handle(async (req, res) => {
  const doc = await CandidateProfile.findByIdAndDelete(req.params.id);
  if (!doc) return res.status(404).json(NOT_FOUND);
  res.json({ success: true });
}));

// ---------- 6. Start ----------
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  log("info", "Resume Processing Service running", { url: `http://localhost:${PORT}/candidates` });
});
