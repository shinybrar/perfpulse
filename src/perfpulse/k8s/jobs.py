"""Module for collecting metrics for Kubernetes Jobs."""

import time
from datetime import datetime, timezone
from prometheus_client import push_to_gateway, CollectorRegistry, Histogram, Gauge
from kubernetes import client, config


def terminating(cluster: str, namespace: str, gateway: str, sleep: int = 60, count: int = 1) -> None:
    """Collects metrics for jobs in terminating state from a Kubernetes cluster.

    Args:
        cluster (str): Name of the K8s cluster.
        namespace (str): K8s namespace.
        gateway (str): Prometheus Pushgateway address.
        sleep (int, optional): Time to sleep between pushes. Defaults to 60.
        count (int, optional): Number of times to push metrics. Defaults to 1.
            Set to -1 to push metrics indefinitely.
    """
    registry: CollectorRegistry = CollectorRegistry()
    histogram = Histogram(
        name="perfpulse_k8s_job_avg_duration_seconds",
        documentation="Average duration of jobs in terminating state",
        labelnames=["cluster", "namespace", "kind"],
        registry=registry,
        unit="seconds",
    )
    gauge = Gauge(
        name="perfpulse_k8s_jobs_count_total",
        documentation="Total number of jobs in terminating state",
        labelnames=["cluster", "namespace", "kind"],
        registry=registry,
        unit="count",
    )
    # Load kube config and create a client
    try:
        config.load_kube_config()  # type: ignore
    except config.ConfigException:
        config.load_incluster_config()  # type: ignore
    except Exception as err:
        raise err

    v1 = client.CoreV1Api()
    while count != 0:
        pods = v1.list_namespaced_pod(namespace=namespace)  # type: ignore
        detections: int = 0
        total_duration: float = 0
        if pods.items:
            for pod in pods.items:
                if pod.metadata.deletion_timestamp:
                    detections += 1
                    duration = datetime.now(timezone.utc) - pod.metadata.deletion_timestamp
                    total_duration += float(duration.total_seconds())

        print(f"Total number of jobs in terminating state: {detections}")
        print(f"Average duration of jobs in terminating state: {total_duration / detections}")
        histogram.labels(cluster=cluster, namespace=namespace, kind="terminating").observe(total_duration / detections)
        gauge.labels(cluster=cluster, namespace=namespace, kind="terminating").set(detections)
        push_to_gateway(gateway=gateway, job="perfpulse", registry=registry)
        print(f"Pushed metrics to {gateway}")
        count -= 1
        if count != 0:
            print(f"Sleeping for {sleep} seconds")
            time.sleep(sleep)
