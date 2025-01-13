"""This module collects metrics for kubectl get pods command from a Kubernetes cluster."""

import time
from prometheus_client import push_to_gateway, CollectorRegistry, Histogram
from kubernetes import client, config


def latency(cluster: str, namespace: str, gateway: str, sleep: int = 60, count: int = 1) -> None:
    """Collects metrics for kubectl get pods command from a Kubernetes cluster.

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
        name="perfpulse_k8s_kubectl_duration_seconds",
        documentation="duration to execute kubectl commands",
        labelnames=["cluster", "namespace", "kind"],
        registry=registry,
        unit="seconds",
    )
    try:
        config.load_kube_config()  # type: ignore
    except config.ConfigException as error:
        print(f"Failed to load kube config: {error}")
        print("Trying to load in-cluster config")
        try:
            config.load_incluster_config()  # type: ignore
        except Exception as err:
            print(f"Failed to load in-cluster config: {err}")
            raise err

    while count != 0:
        v1 = client.CoreV1Api()
        start: float = time.time()
        v1.list_namespaced_pod(namespace=namespace)  # type: ignore
        histogram.labels(cluster=cluster, namespace=namespace, kind="get_pods").observe(time.time() - start)
        print(f"kubectl get pods command latency: {time.time() - start}")
        push_to_gateway(
            gateway=gateway,
            job="perfpulse",
            registry=registry,
        )
        print(f"Pushed metrics to {gateway}")
        count -= 1
        if count != 0:
            print(f"Sleeping for {sleep} seconds")
            time.sleep(sleep)
