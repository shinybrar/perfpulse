"""perfPulse: Performance Pulse for Science Platform."""

import fire
from perfpulse.k8s import jobs, kubectl


def cli():
    """PerfPulse Command Line Interface."""
    fire.Fire(
        {
            "k8s-kubectl-latency": kubectl.latency,
            "k8s-jobs-terminating": jobs.terminating,
        }
    )
