FROM telegraf:1.30

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 curl \
    && rm -rf /var/lib/apt/lists/*

RUN install -d -o telegraf -g telegraf /opt/hardening/scripts

COPY telegraf/telegraf.conf /etc/telegraf/telegraf.conf
COPY scripts/parse_atomic_red_team_result.py /opt/hardening/scripts/parse_atomic_red_team_result.py

RUN chown telegraf:telegraf \
        /etc/telegraf/telegraf.conf \
        /opt/hardening/scripts/parse_atomic_red_team_result.py

# USER telegraf  # Запускаем от root для доступа к файлам

# Health check для проверки доступности метрик
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9091/metrics || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["telegraf"]
