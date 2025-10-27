FROM registry.fedoraproject.org/fedora:40

RUN dnf -y update && \
    dnf -y install openscap-scanner scap-security-guide docker && \
    dnf clean all && \
    rm -rf /var/cache/dnf

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
