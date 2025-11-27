"""OpenTelemetry tracing configuration."""

import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def setup_tracing(app) -> None:
    """Configure OpenTelemetry tracing for the application."""
    if not settings.tracing_enabled:
        logger.info("Tracing is disabled")
        return

    try:
        # Create resource with service info
        resource = Resource.create(
            {
                "service.name": "test-hard-dashboard",
                "service.version": settings.app_version,
                "deployment.environment": settings.environment,
            }
        )

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Configure OTLP exporter for Tempo
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otlp_endpoint,
            insecure=True,  # Use TLS in production
        )

        # Add batch processor for better performance
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)

        logger.info(f"Tracing configured with endpoint: {settings.otlp_endpoint}")

    except Exception as e:
        logger.warning(f"Failed to configure tracing: {e}")


def get_tracer(name: str = __name__) -> trace.Tracer:
    """Get a tracer instance for manual instrumentation."""
    return trace.get_tracer(name)
