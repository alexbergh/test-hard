# Multi-stage build for unified test-hard package
FROM debian:13-slim AS base

# Install common dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    gnupg \
    lsb-release \
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

# Stage 3: Install OpenSCAP from Debian (compatible with base)
FROM base AS openscap-stage
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libopenscap25 \
    openscap-utils \
    ssg-base \
    ssg-debian \
    ssg-debderived \
    && rm -rf /var/lib/apt/lists/*

# Stage 4: Install Telegraf
FROM base AS telegraf-stage
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN wget -qO- https://repos.influxdata.com/influxdata-archive_compat.key | gpg --dearmor > /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg && \
    echo "deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] https://repos.influxdata.com/debian stable main" > /etc/apt/sources.list.d/influxdata.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends telegraf && \
    rm -rf /var/lib/apt/lists/*

# Final stage: Combine everything
FROM base

# Install runtime dependencies for OpenSCAP
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libopenscap25 \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Lynis from lynis-stage
COPY --from=lynis-stage /usr/sbin/lynis /usr/sbin/lynis
COPY --from=lynis-stage /usr/share/lynis /usr/share/lynis

# Make Lynis usable when run inside the unified image:
# - provide an /etc/lynis config location (some Lynis versions expect it)
# - ensure a default profile is present so `lynis audit` doesn't fail
RUN rm -rf /etc/lynis && \
    mkdir -p /etc/lynis && \
    cp -a /usr/share/lynis/* /etc/lynis/ || true && \
    if [ ! -f /etc/lynis/default.prf ]; then cp /usr/share/lynis/include/profiles /etc/lynis/default.prf || true; fi && \
    # Ensure plugin directories exist so Lynis can run non-interactively
    mkdir -p /etc/lynis/plugins /usr/share/lynis/plugins && \
    chown -R root:root /etc/lynis /usr/share/lynis && \
    chmod -R u=rwX,go=rX /etc/lynis /usr/share/lynis

# Copy OpenSCAP from openscap-stage
COPY --from=openscap-stage /usr/bin/oscap /usr/bin/oscap
COPY --from=openscap-stage /usr/share/openscap /usr/share/openscap
COPY --from=openscap-stage /usr/share/xml/scap /usr/share/xml/scap

# Copy Telegraf from telegraf-stage
COPY --from=telegraf-stage /usr/bin/telegraf /usr/bin/telegraf
COPY --from=telegraf-stage /etc/telegraf /etc/telegraf

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Copy all scripts
COPY scripts/ /opt/test-hard/scripts/
COPY atomic-red-team/ /opt/test-hard/atomic-red-team/

# Copy custom Telegraf configuration
COPY telegraf/telegraf.conf /etc/telegraf/telegraf.conf

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
