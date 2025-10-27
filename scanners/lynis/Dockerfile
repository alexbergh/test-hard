FROM debian:12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends docker.io ca-certificates lynis && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
