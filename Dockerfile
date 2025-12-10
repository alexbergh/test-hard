# Multi-stage build for unified test-hard package
FROM debian:12-slim AS base

# Install common dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    python3 \
    python3-pip \
    docker.io \
    bash \
    git \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Install Lynis
FROM base AS lynis-stage
RUN apt-get update && \
    apt-get install -y --no-install-recommends lynis && \
    rm -rf /var/lib/apt/lists/*

# Stage 3: Install OpenSCAP (from Fedora for better SCAP support)
FROM registry.fedoraproject.org/fedora:40 AS openscap-stage
RUN dnf -y update && \
    dnf -y install openscap-scanner scap-security-guide && \
    dnf clean all && \
    rm -rf /var/cache/dnf

# Final stage: Combine everything
FROM base

# Copy Lynis from lynis-stage
COPY --from=lynis-stage /usr/sbin/lynis /usr/sbin/lynis
COPY --from=lynis-stage /usr/share/lynis /usr/share/lynis

# Copy OpenSCAP from openscap-stage
COPY --from=openscap-stage /usr/bin/oscap /usr/bin/oscap
COPY --from=openscap-stage /usr/share/xml/scap /usr/share/xml/scap
COPY --from=openscap-stage /usr/share/openscap /usr/share/openscap
COPY --from=openscap-stage /usr/lib64/libopenscap* /usr/lib/x86_64-linux-gnu/

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Copy all scripts
COPY scripts/ /opt/test-hard/scripts/
COPY atomic-red-team/ /opt/test-hard/atomic-red-team/

# Create necessary directories
RUN mkdir -p /var/lib/hardening/results \
    /var/lib/hardening/art-storage \
    /opt/test-hard/reports \
    && chmod -R 755 /opt/test-hard

# Set working directory
WORKDIR /opt/test-hard

# Add entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Labels
LABEL org.opencontainers.image.title="test-hard" \
      org.opencontainers.image.description="Security hardening and monitoring platform" \
      org.opencontainers.image.source="https://github.com/alexbergh/test-hard" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="1.0.0"

ENTRYPOINT ["/entrypoint.sh"]
CMD ["help"]
