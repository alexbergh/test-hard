FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONUNBUFFERED=1 \
    HARDENING_RESULTS_DIR=/var/lib/hardening/results \
    HARDENING_ART_STORAGE=/var/lib/hardening/art-storage

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        sudo python3 python3-pip python3-venv git curl wget ca-certificates \
        openscap-scanner lynis \
    && pip install --no-cache-dir atomic-operator attrs click pyyaml \
    && useradd --create-home --shell /bin/bash agent \
    && echo "agent ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/agent \
    && chmod 440 /etc/sudoers.d/agent \
    && mkdir -p /opt/hardening /var/lib/hardening/results /var/lib/hardening/art-storage \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY docker/common/hardening-entrypoint.sh /usr/local/bin/hardening-entrypoint.sh

USER agent
WORKDIR /home/agent
ENTRYPOINT ["/usr/local/bin/hardening-entrypoint.sh"]
CMD []
