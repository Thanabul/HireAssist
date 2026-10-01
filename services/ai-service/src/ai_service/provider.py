"""The boundary between this service's domain logic and a model vendor.

Everything above this line speaks criteria, scores and questions. Everything
below it speaks tokens and HTTP. Swapping vendors is implementing this
protocol; nothing in service.py changes.
"""

from dataclasses import dataclass
from typing import Any, Protocol


class ProviderError(Exception):
    """The provider could not be reached, or refused, or returned nothing usable.

    Raised instead of letting a vendor exception escape: a vendor type in a
    handler's except clause is the boundary leaking.
    """


@dataclass(frozen=True)
class ProviderAnswer:
    """One structured answer from a model."""

    data: dict[str, Any]
    #: The model the provider actually served, which may be more specific than
    #: the one requested. Attribution records this, not the configured name.
    model: str
    #: What the call consumed. ADR-004 puts a token budget on a deployment,
    #: and a budget nobody counts against is a sentence in a document.
    input_tokens: int = 0
    output_tokens: int = 0


class Provider(Protocol):
    """Returns an answer conforming to a JSON schema, or raises ProviderError."""

    def json_answer(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any],
        schema_name: str,
        schema_description: str,
    ) -> ProviderAnswer: ...
