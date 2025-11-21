# syntax=docker/dockerfile:1.4

# ============================================================
# Stage 1: Builder - установка Python зависимостей
# ============================================================
FROM quay.io/centos/centos:stream9 AS builder

RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked \
    dnf install -y python3 python3-pip

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install \
        atomic-operator \
        attrs \
        click \
        pyyaml

# ============================================================
# Stage 2: Runtime - финальный минимальный образ
# ============================================================
FROM quay.io/centos/centos:stream9

ENV PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONUNBUFFERED=1 \
    HARDENING_RESULTS_DIR=/var/lib/hardening/results \
    HARDENING_ART_STORAGE=/var/lib/hardening/art-storage

# Установка только runtime зависимостей (без git, python3-pip)
RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked \
    dnf install -y epel-release \
    && crb enable \
    && dnf install -y --allowerasing \
        sudo \
        python3 \
        curl \
        wget \
        ca-certificates \
        openscap-scanner \
        scap-security-guide \
        lynis

RUN useradd --create-home --shell /bin/bash agent \
    && echo "agent ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/agent \
    && chmod 440 /etc/sudoers.d/agent \
    && mkdir -p /opt/hardening /var/lib/hardening/results /var/lib/hardening/art-storage

# Копируем установленные Python пакеты из builder
COPY --from=builder /usr/local/lib/python3.9 /usr/local/lib/python3.9
COPY --from=builder /usr/local/lib64/python3.9 /usr/local/lib64/python3.9
COPY --from=builder /usr/local/bin /usr/local/bin

COPY docker/common/hardening-entrypoint.sh /usr/local/bin/hardening-entrypoint.sh

USER agent
WORKDIR /home/agent
ENTRYPOINT ["/usr/local/bin/hardening-entrypoint.sh"]
CMD []
