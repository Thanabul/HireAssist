"""Runtime configuration, read from the environment at startup."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AI_SERVICE_", env_file=".env", extra="ignore")

    port: int = 50051
    max_workers: int = 10

    # Recorded with every answer so an old justification can be accounted for.
    provider: str = "anthropic"
    model: str = "claude-haiku-4-5-20251001"
    # Overrides the built-in prompts.PROMPT_VERSION. Set it only when running
    # prompts that did not ship with this build; otherwise attribution lies.
    prompt_version: str | None = None

    # Enough for the longest of the three answers — a full per-criterion
    # assessment set with evidence quoted from the resume.
    max_tokens: int = 4096

    # The credential is the whole reason this service exists as a boundary:
    # it lives here and nowhere else.
    api_key: str | None = None

    # Reflection lets grpcurl and a caller's tooling discover the contract
    # without the .proto to hand. The service is internal and never exposed
    # through the gateway (ADR-007), which is what makes that acceptable.
    enable_reflection: bool = True

    # How long an in-flight scoring call has to finish after a stop signal.
    shutdown_grace_s: int = 30

    # One scoring attempt may not outlive this. The caller retries with
    # backoff; waiting longer inside the service only hides the outage.
    request_timeout_s: int = 60


settings = Settings()
