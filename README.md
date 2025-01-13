# perfPulse

perfPulse is a collection of tools to monitor and collect performance metrics from Canadian Astronomy and Data Centre (CADC) Platforms.

Its goal is to provide insights into the health, performance, scalability, reliablity and the quality of the user experience when using CADC services by performing spot checks and simulating users and admin operations and emitting metrics.

`perfPulse` designed to send metrics to a Prometheus Pushgateway for further analysis and visualization using Grafana Dashboards.

## Installation

```bash
pip install perfPulse
```

## Usage

```
perfpulse --help
```

## Technical Guide

When creating new metrics, it’s important to ensure they are named and labeled correctly and that the chosen metric type accurately reflects the type of data being collected. This document provides a structured guide to help you create and maintain high-quality metrics for perfpulse.

### Metric Naming Conventions

1. Use Lowercase and Underscores
   - Prometheus best practices dictate snake_case and all-lowercase for metric names.
   - Example: `perfpulse_k8s_job_avg_duration_seconds`

2. Prefix With a Relevant Criteria
    - Prefix your metric with a domain-like name that represents your application or feature. For instance:
      - `perfpulse_k8s_` for metrics related to Kubernetes data collected by perfpulse.
      - `perfpulse_usersim_` for metrics related to a perfpulse user simulation scripts.

3. Indicate the Unit
    - Include the base unit for your metric in the name—using _seconds, _bytes, _count, etc. This helps clarify the intended measurement unit and avoids confusion. Example:
        - `perfpulse_k8s_job_avg_duration_seconds`
	    - `perfpulse_k8s_jobs_count_total`

4. Use Meaningful Suffixes for Counters
	•	For counters, add `_total`, `_count`, `_avg` as a suffix when appropriate.
	•	Example: `perfpulse_k8s_jobs_count_total`

5. Reuse Metric Names With Different Labels
    - If you have multiple “dimensions” or categories for the same metric type, you can reuse the same metric name but differentiate with labels.
    - For example, perfpulse_k8s_kubectl_latency_seconds can track latencies for different commands (get_pods, get_nodes, etc.) via labels like `kind="get_pods"` or `kind="get_nodes"`.

### Label Usage

1. Keep Labels Cardinality Under Control
   - Labels should be used to segment data along meaningful dimensions—like cluster, namespace, or the kind of operation.
   - Avoid using high-cardinality labels (e.g., user IDs, IP addresses) because they can lead to excessive metric series and burden your monitoring system. **Each unique combination of labels creates a new time series, so be mindful of the cardinality of your labels.**

2. Example Labels
    - `cluster`: Name of the Kubernetes cluster (e.g., `keel-dev`, `keel-prod`).
    - `namespace`: Target namespace in Kubernetes (e.g., `default`).
    - kind: Type of metric being measured (e.g., `get_pods`, `vos_pull`).

3. Consistency Is Key
    - Ensure you use the same label names across your metrics wherever they have the same meaning.
    - For example, always call the cluster label `cluster`, not `cluster_name` in one metric and `cluster_id` in another.

## Creating a New Metric

When adding a new metric, it’s best to follow a clear process. Below is an example of creating and publishing a histogram metric that measures the latency of various `kubectl` commands. Each part of the code is annotated to show how everything fits together.

---

### Example: Kubernetes Latency Metric

```python
from prometheus_client import Histogram, CollectorRegistry, push_to_gateway
from kubernetes import client, config
import time

def kubectl_latency_metrics(
    cluster: str,
    namespace: str,
    gateway: str,
    sleep: int = 60,
    count: int = 1
) -> None:
    """
    Collect and push latency metrics for various kubectl commands.

    Args:
        cluster (str): Name of the Kubernetes cluster.
        namespace (str): Target namespace in Kubernetes.
        gateway (str): URL of the Prometheus Pushgateway.
        sleep (int, optional): Time to sleep between metric pushes. Defaults to 60.
        count (int, optional): Number of times to push metrics. Defaults to 1.
            Set to -1 to run indefinitely.
    """

    # 1. Create a new Prometheus registry
    registry = CollectorRegistry()

    # 2. Define the histogram metric
    #    - Name uses "snake_case" and ends with "_seconds" to indicate the unit.
    #    - Labels are used to differentiate dimensions (cluster, namespace, operation).
    kubectl_histogram = Histogram(
        name="perfpulse_k8s_kubectl_latency_seconds",
        documentation="Latency distribution for various kubectl commands",
        labelnames=["cluster", "namespace", "kind"],
        registry=registry,
        # Optional: You can define specific buckets to control granularity
        # buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10)
    )

    # 3. Load Kubernetes config for local or in-cluster usage
    try:
        config.load_kube_config()  # Use ~/.kube/config
    except config.ConfigException:
        config.load_incluster_config()  # Use in-cluster config
    except Exception as err:
        raise err

    # 4. Loop to collect and push metrics repeatedly
    while count != 0:
        # 4a. Measure latency for "get_pods" operation
        start_time = time.time()
        v1_api = client.CoreV1Api()
        v1_api.list_namespaced_pod(namespace=namespace)  # simulates "kubectl get pods"
        duration = time.time() - start_time

        # 4b. Record observation in the histogram
        kubectl_histogram.labels(
            cluster=cluster,
            namespace=namespace,
            kind="get_pods"
        ).observe(duration)

        # 4c. Push to the gateway
        push_to_gateway(
            gateway=gateway,
            job="perfpulse_kubectl_latency",
            registry=registry
        )
        print(f"Pushed 'get_pods' latency metrics to {gateway}: {duration}s")

        count -= 1
        if count != 0:
            time.sleep(sleep)
```
