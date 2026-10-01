"""The contract's own guarantees: it generates, the server binds, and a call
that cannot be answered fails loudly rather than returning an empty answer.
"""

import grpc
import pytest

from ai_service.config import Settings


def test_the_four_operations_are_exposed():
    from ai_service.gen.hireassist.ai.v1 import ai_service_pb2 as pb

    descriptor = pb.DESCRIPTOR.services_by_name["AiService"]
    assert {m.name for m in descriptor.methods} == {
        "DeriveCriteriaFromDescription",
        "ExtractProfileFromText",
        "ScoreAgainstCriteria",
        "GenerateInterviewQuestions",
    }


def test_scoring_without_criteria_is_rejected(make_stub):
    from ai_service.gen.hireassist.ai.v1 import ai_service_pb2 as pb

    stub, _ = make_stub(answers={})
    request = pb.ScoreAgainstCriteriaRequest(profile=pb.CandidateProfile(candidate_id="c-1"))
    with pytest.raises(grpc.RpcError) as exc:
        stub.ScoreAgainstCriteria(request)
    assert exc.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_without_a_credential_the_service_serves_and_refuses(make_stub):
    """No key is a configuration fault, not an outage: the service comes up and
    says so, rather than failing to boot or answering with an empty score."""
    from ai_service.gen.hireassist.ai.v1 import ai_service_pb2 as pb

    stub, _ = make_stub(provider=None)
    request = pb.ScoreAgainstCriteriaRequest(
        profile=pb.CandidateProfile(candidate_id="c-1", skills=["Go"]),
        criteria=[pb.Criterion(id="cr-1", text="Production Go", must_have=True)],
    )
    with pytest.raises(grpc.RpcError) as exc:
        stub.ScoreAgainstCriteria(request)
    assert exc.value.code() == grpc.StatusCode.FAILED_PRECONDITION


def test_attribution_records_the_model():
    from ai_service.attribution import attribution_for
    from ai_service.prompts import PROMPT_VERSION

    attribution = attribution_for(Settings(model="claude-haiku-4-5-20251001"))
    assert attribution.model == "claude-haiku-4-5-20251001"
    assert attribution.provider == "anthropic"
    assert attribution.prompt_version == PROMPT_VERSION


def test_attribution_prefers_the_model_that_actually_answered():
    from ai_service.attribution import attribution_for

    # An alias resolving to a dated build is the case this exists for: what
    # answered is recorded, not what was asked for.
    attribution = attribution_for(
        Settings(model="claude-haiku-4-5"), model="claude-haiku-4-5-20251001"
    )
    assert attribution.model == "claude-haiku-4-5-20251001"
