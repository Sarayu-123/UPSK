from prometheus_client import (
    Counter,
    Histogram,
    Gauge
)

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds"
)

urls_total = Gauge(
    "urls_total",
    "Total number of shortened URLs"
)

process_memory_bytes = Gauge(
    "process_memory_bytes",
    "Resident memory usage of the API process in bytes"
)