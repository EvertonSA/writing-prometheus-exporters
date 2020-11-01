from prometheus_client import (
    CollectorRegistry,
    Gauge,
    Counter,
)
from pyramid.config import Configurator
from pyramid.response import Response
from prometheus_client import (
    generate_latest,
    CONTENT_TYPE_LATEST,
)
import time
import socket


def synthetic(service):
    before = time.perf_counter()
    sock = socket.socket()
    sock.settimeout(1)
    sock.connect(service)
    sock.recv(4096)
    sock.close()
    return time.perf_counter() - before


def update(request):
    latency = synthetic(
        request.registry["service"]
    )
    request.registry["synthetic"].set(latency)
    request.registry["hits"].inc()


def metrics_web(request):
    update(request)
    registry = request.registry[
        "prometheus_registry"
    ]
    return Response(
        generate_latest(registry),
        content_type=CONTENT_TYPE_LATEST,
    )


def configure_metrics(mapping):
    registry = CollectorRegistry()
    mapping["prometheus_registry"] = registry
    mapping["synthetic"] = Gauge(
        "synthetic",
        "Synthetic query latency",
        registry=registry,
    )
    mapping["hits"] = Counter(
        "hits",
        "Hits to endpoint",
        registry=registry,
    )


with Configurator() as config:
    config.registry["service"] = (
        "localhost",
        1113,
    )
    configure_metrics(config.registry)
    config.add_route("metrics", "/metrics")
    config.add_view(
        metrics_web, route_name="metrics"
    )
    application = config.make_wsgi_app()
