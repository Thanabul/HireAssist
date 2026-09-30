"""Model attribution attached to every answer this service returns."""

from ai_service.config import Settings
from ai_service.prompts import PROMPT_VERSION


def attribution_for(settings: Settings, model: str | None = None):
    """Build the ModelAttribution message for an answer.

    ``model`` is the model the provider actually served, which can be more
    specific than the configured name — an alias resolving to a dated build,
    say. Recording what answered rather than what was asked for is the point:
    attribution exists so a justification shown months ago can be accounted
    for (ADR-004).

    Imported lazily so the generated stubs are only required at call time,
    which keeps `import ai_service` working before `make proto` has been run.
    """
    from ai_service.gen.hireassist.ai.v1 import ai_service_pb2 as pb

    return pb.ModelAttribution(
        provider=settings.provider,
        model=model or settings.model,
        prompt_version=settings.prompt_version or PROMPT_VERSION,
    )
