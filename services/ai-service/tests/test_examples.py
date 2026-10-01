"""The example requests must stay loadable against the current contract.

They are pasted into Postman and grpcui by hand, so nothing else would notice
a renamed field — the examples would simply start failing in front of whoever
is demonstrating the service.
"""

import pathlib

import pytest
from google.protobuf import json_format

REQUESTS = sorted((pathlib.Path(__file__).parent.parent / "demo" / "requests").glob("*.json"))


def rpc_of(path):
    """The operation an example is for.

    A file may carry a suffix after a hyphen to hold a second example of the
    same call — `ScoreAgainstCriteria-derived.json` scores against criteria a
    real model proposed. Only the part before the hyphen names the RPC.
    """
    return path.stem.split("-", 1)[0]


def test_every_operation_has_at_least_one_example():
    from ai_service.gen.hireassist.ai.v1 import ai_service_pb2 as pb

    operations = {m.name for m in pb.DESCRIPTOR.services_by_name["AiService"].methods}
    assert operations - {rpc_of(p) for p in REQUESTS} == set()


def test_no_example_names_an_operation_that_does_not_exist():
    from ai_service.gen.hireassist.ai.v1 import ai_service_pb2 as pb

    operations = {m.name for m in pb.DESCRIPTOR.services_by_name["AiService"].methods}
    assert {rpc_of(p) for p in REQUESTS} - operations == set()


@pytest.mark.parametrize("path", REQUESTS, ids=lambda p: p.stem)
def test_example_parses_into_its_request_message(path):
    from ai_service.gen.hireassist.ai.v1 import ai_service_pb2 as pb

    message = getattr(pb, f"{rpc_of(path)}Request")()
    json_format.Parse(path.read_text(), message)


def test_the_scoring_example_is_actually_answerable():
    """A pasted example the handler rejects is worse than no example."""
    from ai_service.gen.hireassist.ai.v1 import ai_service_pb2 as pb

    example = next(p for p in REQUESTS if p.stem == "ScoreAgainstCriteria")
    message = pb.ScoreAgainstCriteriaRequest()
    json_format.Parse(example.read_text(), message)
    assert message.criteria, "scoring with no criteria is rejected by the handler"
    assert message.profile.candidate_id
