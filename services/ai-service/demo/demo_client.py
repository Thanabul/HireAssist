"""A walkthrough of the AI Service over gRPC, for demonstrating it live.

Runs the three operations against a server that is already up, printing what
crosses the wire at each step. Five things it is meant to show, in order:

  1. the service describes itself over reflection — the contract is the .proto
  2. health reports whether it can work, not merely whether the port answers
  3. UC-1, UC-2, UC-3 answered as domain operations
  4. the contract refuses a call it cannot answer defensibly
  5. no prompt, provider or token count ever reaches the caller

Usage:  uv run python demo/demo_client.py [host:port]
"""

import sys

import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc

from ai_service.gen.hireassist.ai.v1 import ai_service_pb2 as pb
from ai_service.gen.hireassist.ai.v1 import ai_service_pb2_grpc as pb_grpc

TARGET = sys.argv[1] if len(sys.argv) > 1 else "localhost:50051"
RULE = "─" * 78


def step(number, title):
    print(f"\n{RULE}\n  {number}. {title}\n{RULE}")


def field(label, value):
    print(f"   {label:<22} {value}")


EXPLAIN = {
    "FAILED_PRECONDITION": "No model credential is configured. Put one in .env as "
    "AI_SERVICE_API_KEY, or run the offline demo with "
    "AI_SERVICE_PROVIDER=canned.",
    "UNAUTHENTICATED": "The provider rejected the credential.",
    "UNAVAILABLE": "The provider could not be reached or refused the call. If this says "
    "401, the API key in .env is being read but is not valid.",
    "INTERNAL": "The model answered, but not in a form the contract accepts.",
    "INVALID_ARGUMENT": "The request itself is unusable.",
}


def fatal(exc):
    """A traceback in front of a room is a lost demo. Print what went wrong,
    what it means, and stop."""
    code = exc.code().name
    print(f"\n{'!' * 78}")
    print(f"  CALL FAILED — {code}")
    print(f"  {exc.details()}")
    if code in EXPLAIN:
        print(f"\n  {EXPLAIN[code]}")
    print(f"{'!' * 78}\n")
    return 1


def canned_banner(where="below"):
    """Said once at each end, loudly, rather than stamped into every field of
    every answer — which is what an earlier version did, and it buried the
    shape of the response the demo exists to show."""
    print(f"\n{'!' * 78}")
    print("  CANNED ANSWERS — no language model is being called.")
    print(f"  The server is running with AI_SERVICE_PROVIDER=canned, so every answer {where}")
    print("  is scripted. Set AI_SERVICE_API_KEY and drop that variable for real output.")
    print(f"{'!' * 78}")


RESUME_TEXT = """Somchai Jaidee
somchai.j@example.com | 081-234-5678 | Bangkok | Age 29 | Thai

EXPERIENCE

Backend Engineer - Acme Payments Co., Ltd.        Mar 2021 - Present
  Built and operated payment services in Go on PostgreSQL.
  Designed the partitioned ledger schema and led the migration to it.

Software Engineer - Bangkok Digital               Jun 2019 - Feb 2021
  Internal tooling in Python. Some Kubernetes for deployment.

EDUCATION
BSc Computer Science, Chulalongkorn University, 2019

SKILLS
Go, Python, PostgreSQL, Kubernetes, gRPC
"""

# The resume, already parsed. The AI Service never sees a file, and nothing in
# CandidateProfile carries a name or contact details.
PROFILE = pb.CandidateProfile(
    candidate_id="cand-7781",
    work_history=[
        pb.WorkExperience(
            title="Backend Engineer",
            organisation="Acme Payments",
            start="2021-03",
            end="",
            summary="Built and operated payment services in Go on PostgreSQL; "
            "led the migration to partitioned ledgers.",
        ),
        pb.WorkExperience(
            title="Software Engineer",
            organisation="Bangkok Digital",
            start="2019-06",
            end="2021-02",
            summary="Internal tooling in Python; some Kubernetes.",
        ),
    ],
    skills=["Go", "Python", "PostgreSQL", "Kubernetes", "gRPC"],
    education=[
        pb.Education(
            qualification="BSc Computer Science",
            institution="Chulalongkorn University",
            completed="2019",
        )
    ],
    additional_text="Maintains an open-source CLI with 400 stars.",
)

CRITERIA = [
    pb.Criterion(
        id="cr-1",
        text="3+ years production backend experience",
        must_have=True,
        category="experience",
    ),
    pb.Criterion(
        id="cr-2", text="Strong SQL and relational data modelling", weight=40, category="skills"
    ),
    pb.Criterion(
        id="cr-3", text="Experience operating distributed systems", weight=60, category="skills"
    ),
]


def main():
    print(f"\n  HireAssist AI Service — gRPC demo\n  target: {TARGET}")
    channel = grpc.insecure_channel(TARGET)
    try:
        grpc.channel_ready_future(channel).result(timeout=5)
    except grpc.FutureTimeoutError:
        print(f"\n  ! nothing is listening on {TARGET}. Start it with `make run` first.\n")
        return 1
    stub = pb_grpc.AiServiceStub(channel)

    # 1 ── the contract, discovered from the running server ──────────────────
    step(1, "The service describes itself (gRPC reflection)")
    reflect = reflection_pb2_grpc.ServerReflectionStub(channel)
    responses = reflect.ServerReflectionInfo(
        iter([reflection_pb2.ServerReflectionRequest(list_services="")])
    )
    for response in responses:
        for service in response.list_services_response.service:
            field("service", service.name)
    print()
    descriptor = pb.DESCRIPTOR.services_by_name["AiService"]
    for method in descriptor.methods:
        field(method.name, f"({method.input_type.name}) → {method.output_type.name}")
    print("\n   Nothing here was typed by the client: the schema is the .proto, and both")
    print("   sides generate from the same file. A renamed field breaks the build,")
    print("   not the shortlist.")

    # 2 ── health ────────────────────────────────────────────────────────────
    step(2, "Health — can it work, not just is it up")
    health = health_pb2_grpc.HealthStub(channel)
    status = health.Check(health_pb2.HealthCheckRequest()).status
    field("status", health_pb2.HealthCheckResponse.ServingStatus.Name(status))
    if status != health_pb2.HealthCheckResponse.SERVING:
        print("\n   NOT_SERVING means no model credential is configured. The port answers;")
        print("   the service cannot do its job, and says so. Set AI_SERVICE_API_KEY, or")
        print("   run the offline demo with AI_SERVICE_PROVIDER=canned.\n")
        return 1

    # 3 ── UC-1 ──────────────────────────────────────────────────────────────
    step(3, "UC-1 — free-text role description → screening criteria")
    derived = stub.DeriveCriteriaFromDescription(
        pb.DeriveCriteriaFromDescriptionRequest(
            description=(
                "We need a backend engineer with at least 3 years of production "
                "experience. Must be strong with SQL. Distributed systems experience "
                "is a big plus. Should be a team player."
            ),
            language=pb.LANGUAGE_ENGLISH,
        )
    )
    # Which provider answered is read off the first real answer rather than
    # probed for: against a live model a probe is a billed call and a ten
    # second pause, spent learning something the response already carries.
    canned = derived.attribution.provider == "canned"
    if canned:
        canned_banner()
    field("proposed title", derived.proposed_title)
    for criterion in derived.criteria:
        kind = "MUST HAVE" if criterion.must_have else f"weight {criterion.weight}"
        field(f"  {criterion.id}", f"[{kind}] {criterion.text}")
    for text in derived.uninterpreted:
        field("  uninterpreted", text)
    print("\n   'Should be a team player' is not testable against a resume, so it comes")
    print("   back uninterpreted for the Recruiter rather than being invented into a")
    print("   criterion. Ids are assigned by the caller — Hiring owns criterion identity.")

    # 4 ── UC-2, extraction ──────────────────────────────────────────────────
    step(4, "UC-2 — resume text → a structured candidate profile")
    extracted = stub.ExtractProfileFromText(
        pb.ExtractProfileFromTextRequest(
            candidate_id="cand-7781",
            resume_text=RESUME_TEXT,
            language=pb.LANGUAGE_ENGLISH,
        )
    )
    profile = extracted.profile
    for job in profile.work_history:
        field(f"  {job.title}", f"{job.organisation}  ({job.start} – {job.end or 'present'})")
    field("  skills", ", ".join(profile.skills))
    for item in profile.education:
        field("  education", f"{item.qualification}, {item.institution} {item.completed}")
    if profile.additional_text:
        field("  additional", profile.additional_text[:60])
    print("\n   The name, email, phone and age in that resume are absent from the profile:")
    print("   they may not be used to assess anyone, so extraction is instructed to drop")
    print("   them, and the message has no field that could carry them (ADR-008). This is")
    print("   also the only call that receives unstructured resume text — no model sees a")
    print("   file, and the profile is extracted once per resume, then reused.")

    # 5 ── UC-2, scoring ─────────────────────────────────────────────────────
    step(5, "UC-2 — score that candidate against the criteria")
    scored = stub.ScoreAgainstCriteria(
        pb.ScoreAgainstCriteriaRequest(
            profile=profile, criteria=CRITERIA, language=pb.LANGUAGE_ENGLISH
        )
    )
    field("score", f"{scored.score}/100")
    field("meets must-haves", scored.meets_must_haves)
    if scored.unmet_must_have_ids:
        field("unmet must-haves", ", ".join(scored.unmet_must_have_ids))
    print()
    for assessment in scored.assessments:
        mark = "met " if assessment.met else "MISS"
        field(
            f"  {assessment.criterion_id} [{mark}]",
            f"{assessment.score:>3}  {assessment.evidence[:60]}",
        )
    print()
    field("justification", scored.justification[:70])
    print()
    field(
        "attribution",
        f"{scored.attribution.provider} / {scored.attribution.model} "
        f"/ prompt {scored.attribution.prompt_version}",
    )
    print("\n   The 0-100 total is computed by the service from the per-criterion scores,")
    print("   not asked of the model — a weighted average has a right answer. Must-haves")
    print("   gate the candidate instead of carrying weight.")

    # 5 ── UC-3 ──────────────────────────────────────────────────────────────
    step(6, "UC-3 — interview questions grounded in this resume and this role")
    guide = stub.GenerateInterviewQuestions(
        pb.GenerateInterviewQuestionsRequest(
            profile=PROFILE,
            criteria=CRITERIA,
            emphasis="more system design",
            language=pb.LANGUAGE_ENGLISH,
        )
    )
    for question in guide.questions:
        kind = pb.QuestionKind.Name(question.kind).replace("QUESTION_KIND_", "")
        field(f"  [{kind}]", question.text[:66])
        field("     tests", question.criterion_id)
    print("\n   Every question names the criterion it tests, so an interviewer can say why")
    print("   they are asking it.")

    # 6 ── the contract refusing ─────────────────────────────────────────────
    step(7, "What it refuses — a score with nothing to defend it")
    try:
        stub.ScoreAgainstCriteria(pb.ScoreAgainstCriteriaRequest(profile=profile))
        print("   ! expected this to be rejected")
    except grpc.RpcError as exc:
        field("code", exc.code().name)
        field("detail", exc.details())
    print("\n   It refuses rather than returning an empty score. A zero would rank this")
    print("   candidate last — the exact failure the product exists to prevent.")

    if canned:
        canned_banner("above")
    print(f"\n{RULE}")
    print("  The caller was told criteria, a score and questions. It was never told the")
    print("  prompt, the provider or the token count — that boundary is why this is a")
    print("  service and not a library.")
    print(f"{RULE}\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except grpc.RpcError as error:
        sys.exit(fatal(error))
    except KeyboardInterrupt:
        sys.exit(130)
