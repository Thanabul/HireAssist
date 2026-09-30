"""Anthropic adapter.

The only file in the system that imports a model vendor's SDK. Structured
output is obtained by forcing a tool call rather than by asking for JSON in
the prompt: the schema is enforced by the API, so a malformed answer is the
rare case rather than the thing every handler must defend against.
"""

import logging
from typing import Any

from ai_service.config import Settings
from ai_service.provider import ProviderAnswer, ProviderError

log = logging.getLogger(__name__)


class AnthropicProvider:
    def __init__(self, settings: Settings) -> None:
        import anthropic

        if not settings.api_key:
            raise ProviderError("no API key configured")
        self._client = anthropic.Anthropic(
            api_key=settings.api_key,
            timeout=settings.request_timeout_s,
            max_retries=0,  # the caller retries with backoff (ADR-002); not twice.
        )
        self._model = settings.model
        self._max_tokens = settings.max_tokens

    def json_answer(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any],
        schema_name: str,
        schema_description: str,
    ) -> ProviderAnswer:
        import anthropic

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                tools=[
                    {
                        "name": schema_name,
                        "description": schema_description,
                        "input_schema": schema,
                    }
                ],
                tool_choice={"type": "tool", "name": schema_name},
            )
        except anthropic.APIError as exc:
            # Wrapped deliberately: an anthropic type in a handler's except
            # clause would make every caller depend on the vendor.
            raise ProviderError(f"{type(exc).__name__}: {exc}") from exc
        except Exception as exc:
            raise ProviderError(f"provider call failed: {exc}") from exc

        for block in response.content:
            if block.type == "tool_use" and block.name == schema_name:
                return ProviderAnswer(
                    data=dict(block.input),
                    model=response.model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )

        raise ProviderError(
            f"provider returned no {schema_name} answer (stop_reason={response.stop_reason})"
        )
