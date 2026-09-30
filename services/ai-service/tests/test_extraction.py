"""Profile extraction: what reaches the prompt, and what the handler refuses.

Extraction is the only operation that receives unstructured resume text, so it
is the only one where the attributes excluded from scoring can appear at all.
"""

import grpc
import pytest

PROFILE_TOOL = "candidate_profile"

RESUME = """Somchai Jaidee
somchai@example.com · 081-234-5678 · Age 29 · Thai · Male

EXPERIENCE
Backend Engineer, Acme Payments, Mar 2021 - Present
  Built payment services in Go on PostgreSQL.

EDUCATION
BSc Computer Science, Chulalongkorn University, 2019
"""

GOOD_ANSWER = {
    "work_history": [
        {
            "title": "Backend Engineer",
            "organisation": "Acme Payments",
            "start": "Mar 2021",
            "end": "",
            "summary": "Built payment services in Go on PostgreSQL.",
        }
    ],
    "skills": ["Go", "PostgreSQL"],
    "education": [
        {
            "qualification": "BSc Computer Science",
            "institution": "Chulalongkorn University",
            "completed": "2019",
        }
    ],
    "additional_text": "",
}


def request(text=RESUME, candidate_id="cand-1"):
    from ai_service.gen.hireassist.ai.v1 import ai_service_pb2 as pb

    return pb.ExtractProfileFromTextRequest(
        candidate_id=candidate_id, resume_text=text, language=pb.LANGUAGE_ENGLISH
    )


def test_a_good_answer_becomes_a_profile(make_stub):
    stub, provider = make_stub(answers={PROFILE_TOOL: GOOD_ANSWER})
    response = stub.ExtractProfileFromText(request())

    assert response.profile.candidate_id == "cand-1"
    assert response.profile.work_history[0].organisation == "Acme Payments"
    assert response.profile.work_history[0].end == ""  # current role stays empty
    assert list(response.profile.skills) == ["Go", "PostgreSQL"]
    assert response.attribution.model == "fake-model-1"

    # The whole resume reaches the prompt — this is the one operation that
    # gets unstructured text.
    assert "Somchai" in provider.calls[0]["user"]


def test_the_caller_owns_candidate_identity(make_stub):
    """The id is echoed from the request, never invented, and never taken from
    whatever the model thought the candidate was called."""
    stub, _ = make_stub(answers={PROFILE_TOOL: GOOD_ANSWER})
    assert stub.ExtractProfileFromText(request(candidate_id="cand-999")).profile.candidate_id == (
        "cand-999"
    )


def test_extraction_without_a_candidate_id_is_rejected(make_stub):
    stub, provider = make_stub(answers={PROFILE_TOOL: GOOD_ANSWER})
    with pytest.raises(grpc.RpcError) as exc:
        stub.ExtractProfileFromText(request(candidate_id="  "))
    assert exc.value.code() == grpc.StatusCode.INVALID_ARGUMENT
    assert provider.calls == []


def test_empty_resume_text_is_rejected_before_the_model(make_stub):
    stub, provider = make_stub(answers={PROFILE_TOOL: GOOD_ANSWER})
    with pytest.raises(grpc.RpcError) as exc:
        stub.ExtractProfileFromText(request(text="   \n  "))
    assert exc.value.code() == grpc.StatusCode.INVALID_ARGUMENT
    assert provider.calls == []


def test_an_entirely_empty_extraction_is_a_failure_not_a_profile(make_stub):
    """Empty in every field at once means extraction failed. Returning it would
    hand scoring a candidate with no evidence for anything, which ranks last
    for the wrong reason — the resume needs manual review instead."""
    stub, _ = make_stub(
        answers={
            PROFILE_TOOL: {
                "work_history": [],
                "skills": [],
                "education": [],
                "additional_text": "  ",
            }
        }
    )
    with pytest.raises(grpc.RpcError) as exc:
        stub.ExtractProfileFromText(request())
    assert exc.value.code() == grpc.StatusCode.INTERNAL


def test_a_sparse_profile_is_accepted(make_stub):
    """A new graduate with education and nothing else is an ordinary resume,
    not a failed extraction."""
    stub, _ = make_stub(
        answers={
            PROFILE_TOOL: {
                "work_history": [],
                "skills": [],
                "education": [
                    {
                        "qualification": "BSc Computer Science",
                        "institution": "Chulalongkorn University",
                        "completed": "2025",
                    }
                ],
                "additional_text": "",
            }
        }
    )
    response = stub.ExtractProfileFromText(request())
    assert len(response.profile.education) == 1
    assert not response.profile.work_history


def test_the_profile_has_nowhere_to_put_excluded_attributes():
    """NFR-14 is enforced at extraction by instruction, and here by the shape
    of the message: there is no field for any of these, so a well-formed
    profile cannot carry one in a structured slot."""
    from ai_service.gen.hireassist.ai.v1 import ai_service_pb2 as pb

    fields = {f.name for f in pb.CandidateProfile.DESCRIPTOR.fields}
    for barred in (
        "name",
        "email",
        "phone",
        "gender",
        "age",
        "date_of_birth",
        "nationality",
        "photo",
        "marital_status",
        "religion",
    ):
        assert barred not in fields


def test_the_prompt_bars_the_excluded_attributes():
    """The one guarantee that is instructed rather than structural, so it is
    asserted rather than assumed (ADR-008)."""
    from ai_service.prompts import EXTRACTION_SYSTEM

    lowered = EXTRACTION_SYSTEM.lower()
    for barred in (
        "name",
        "photograph",
        "contact",
        "gender",
        "age",
        "marital",
        "religion",
        "nationality",
    ):
        assert barred in lowered
    assert "additional_text" in lowered


def test_thai_resumes_keep_their_language_and_get_the_era_rule():
    from ai_service.gen.hireassist.ai.v1 import ai_service_pb2 as pb
    from ai_service.prompts import EXTRACTION_SYSTEM, extraction_user

    assert "in Thai" in extraction_user("...", pb.LANGUAGE_THAI)
    # 2567 BE is 2024 CE; missing this gives every Thai candidate 543 extra years.
    assert "543" in EXTRACTION_SYSTEM
