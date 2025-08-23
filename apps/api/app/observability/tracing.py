from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from ..utils.logging import request_id_ctx_var

if TYPE_CHECKING:
    from opentelemetry.sdk.trace.export import SpanExporter


def setup_tracing(
    service_name: str,
    exporter: SpanExporter | None = None,
) -> None:
    """Configure OpenTelemetry if available."""
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            SimpleSpanProcessor,
        )

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        span_exporter = exporter or OTLPSpanExporter()
        processor = (
            BatchSpanProcessor(span_exporter)
            if exporter is None
            else SimpleSpanProcessor(span_exporter)
        )
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
    except Exception as exc:  # pragma: no cover - best effort
        logger.debug("tracing_setup_skipped", error=str(exc))


def add_request_id_to_current_span() -> None:
    """Attach the request ID context variable to the active span."""
    try:
        from opentelemetry import trace

        request_id = request_id_ctx_var.get()
        if not request_id:
            return
        span = trace.get_current_span()
        if span and span.is_recording():
            span.set_attribute("request_id", request_id)
    except Exception as exc:  # pragma: no cover - best effort
        logger.debug("span_attribute_skipped", error=str(exc))