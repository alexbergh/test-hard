FROM quay.io/centos/centos:stream9

ENV PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONUNBUFFERED=1 \
    HARDENING_RESULTS_DIR=/var/lib/hardening/results \
    HARDENING_ART_STORAGE=/var/lib/hardening/art-storage

RUN dnf install -y epel-release \
    && crb enable \
    && dnf install -y --allowerasing sudo python3 python3-pip git curl wget ca-certificates \
        openscap-scanner scap-security-guide lynis \
    && dnf clean all \
    && pip install --no-cache-dir atomic-operator attrs click pyyaml \
    && useradd --create-home --shell /bin/bash agent \
    && echo "agent ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/agent \
    && chmod 440 /etc/sudoers.d/agent \
    && mkdir -p /opt/hardening /var/lib/hardening/results /var/lib/hardening/art-storage

COPY docker/common/hardening-entrypoint.sh /usr/local/bin/hardening-entrypoint.sh

USER agent
WORKDIR /home/agent
ENTRYPOINT ["/usr/local/bin/hardening-entrypoint.sh"]
CMD []
