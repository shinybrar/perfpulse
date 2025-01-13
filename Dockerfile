FROM ubuntu:24.04

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV SHELL=/bin/bash
ENV DEBIAN_FRONTEND=noninteractive

COPY . /perfpulse

RUN apt update --yes --quiet \
    && apt install --yes --quiet --no-install-recommends \
    source-extractor \
    swarp \
    time \
    tzdata \
    curl \
    wget \
    ca-certificates \
    && apt clean --yes \
    && apt autoremove --purge --quiet --yes \
    && rm -rf /var/lib/apt/lists/* /var/tmp/*

RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh
RUN uv venv /venv && source /venv/bin/activate && uv pip install /perfpulse
