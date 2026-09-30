"""gRPC server wiring: the servicer, the health check, and shutdown."""

import logging
import signal
import threading
from concurrent import futures

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from ai_service.config import Settings, settings
from ai_service.provider import Provider
from ai_service.providers import provider_for
from ai_service.service import AiService

log = logging.getLogger(__name__)

SERVICE_NAME = "hireassist.ai.v1.AiService"


def build_server(
    config: Settings | None = None, provider: Provider | None = None
) -> tuple[grpc.Server, int]:
    """Create the server and bind it. Returns the server and the bound port.

    ``provider`` overrides the one the configuration would build, which is how
    the suite runs the real handlers against a scripted provider.
    """
    config = config or settings
    if provider is None:
        provider = provider_for(config)

    from ai_service.gen.hireassist.ai.v1 import ai_service_pb2, ai_service_pb2_grpc

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=config.max_workers))
    ai_service_pb2_grpc.add_AiServiceServicer_to_server(AiService(config, provider), server)

    # Health reports whether this instance can do its job, not merely whether
    # the port answers. Without a credential it is reachable but useless, so
    # it reports NOT_SERVING and an orchestrator can keep traffic away rather
    # than sending every resume to a FAILED_PRECONDITION.
    health_servicer = health.HealthServicer()
    status = (
        health_pb2.HealthCheckResponse.SERVING
        if provider is not None
        else health_pb2.HealthCheckResponse.NOT_SERVING
    )
    health_servicer.set(SERVICE_NAME, status)
    health_servicer.set("", status)
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

    if config.enable_reflection:
        from grpc_reflection.v1alpha import reflection

        reflection.enable_server_reflection(
            (
                ai_service_pb2.DESCRIPTOR.services_by_name["AiService"].full_name,
                health_pb2.DESCRIPTOR.services_by_name["Health"].full_name,
                reflection.SERVICE_NAME,
            ),
            server,
        )

    port = server.add_insecure_port(f"[::]:{config.port}")
    if port == 0:
        raise RuntimeError(f"could not bind port {config.port}")
    return server, port


def serve(config: Settings | None = None) -> None:
    config = config or settings
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    provider = provider_for(config)
    if provider is None:
        log.warning(
            "AI_SERVICE_API_KEY is unset — the service will start, report NOT_SERVING, "
            "and fail every call with FAILED_PRECONDITION"
        )
    elif config.provider == "canned":
        log.warning(
            "AI_SERVICE_PROVIDER=canned — answers are scripted and labelled as such. "
            "No language model will be called."
        )

    server, port = build_server(config, provider=provider)
    server.start()
    log.info(
        "AI Service listening on :%d (model=%s, reflection=%s)",
        port,
        config.model,
        "on" if config.enable_reflection else "off",
    )

    stopping = threading.Event()

    def shut_down(signum, _frame):
        # A scoring call in flight has already been paid for and its resume is
        # claimed by a work row; killing it mid-answer wastes both and sends
        # the row round the retry loop for nothing. Stop accepting new calls,
        # let the ones running finish, then exit.
        log.info("signal %s received — draining for up to %ds", signum, config.shutdown_grace_s)
        server.stop(config.shutdown_grace_s)
        stopping.set()

    signal.signal(signal.SIGTERM, shut_down)
    signal.signal(signal.SIGINT, shut_down)

    stopping.wait()
    server.wait_for_termination()
    log.info("AI Service stopped")
