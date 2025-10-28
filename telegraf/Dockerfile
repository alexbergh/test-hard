FROM telegraf:1.30

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 \
    && rm -rf /var/lib/apt/lists/*

RUN install -d -o telegraf -g telegraf /opt/hardening/scripts

COPY telegraf/telegraf.conf /etc/telegraf/telegraf.conf
COPY scripts/parse_atomic_red_team_result.py /opt/hardening/scripts/parse_atomic_red_team_result.py

RUN chown telegraf:telegraf \
        /etc/telegraf/telegraf.conf \
        /opt/hardening/scripts/parse_atomic_red_team_result.py

# USER telegraf  # Запускаем от root для доступа к файлам

ENTRYPOINT ["/entrypoint.sh"]
CMD ["telegraf"]
