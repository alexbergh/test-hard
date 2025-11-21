# syntax=docker/dockerfile:1.4

# ============================================================
# Stage 1: Builder - установка Python зависимостей
# ============================================================
# Astra Linux Common Edition 1.7 base image (requires access to the Astra registry)
FROM registry.astralinux.ru/astra/ce:1.7 AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    VIRTUAL_ENV=/opt/venv

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv

RUN python3 -m venv "${VIRTUAL_ENV}"

RUN --mount=type=cache,target=/root/.cache/pip \
    "${VIRTUAL_ENV}/bin/pip" install --upgrade pip \
    && "${VIRTUAL_ENV}/bin/pip" install \
        atomic-operator \
        attrs \
        click \
        pyyaml

# ============================================================
# Stage 2: Runtime - финальный минимальный образ
# ============================================================
FROM registry.astralinux.ru/astra/ce:1.7

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONUNBUFFERED=1 \
    HARDENING_RESULTS_DIR=/var/lib/hardening/results \
    HARDENING_ART_STORAGE=/var/lib/hardening/art-storage \
    VIRTUAL_ENV=/opt/venv \
    PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Установка только runtime зависимостей (без python3-pip, python3-venv, git)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && apt-get install -y --no-install-recommends \
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

# Копируем готовый venv из builder stage
COPY --from=builder /opt/venv /opt/venv

COPY docker/common/hardening-entrypoint.sh /usr/local/bin/hardening-entrypoint.sh

USER agent
WORKDIR /home/agent
ENTRYPOINT ["/usr/local/bin/hardening-entrypoint.sh"]
CMD []
