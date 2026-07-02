"""Prometheus metrics."""

from prometheus_client import Counter, Histogram, start_http_server

from ugra.config.settings import Settings

AGENT_INVOCATIONS = Counter(
    "ugra_agent_invocations_total",
    "Total agent invocations",
    ["agent_name", "status"],
)

JOB_SEARCH_REQUESTS = Counter(
    "ugra_job_search_requests_total",
    "Total job search requests",
    ["source", "status"],
)

LLM_LATENCY = Histogram(
    "ugra_llm_request_duration_seconds",
    "LLM request latency",
    ["provider", "model"],
)


def setup_metrics(settings: Settings) -> None:
    start_http_server(settings.prometheus_port)
