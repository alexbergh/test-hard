FROM registry.fedoraproject.org/fedora:40

RUN dnf -y update && \
    dnf -y install openscap-scanner scap-security-guide docker bash && \
    dnf clean all && \
    rm -rf /var/cache/dnf

COPY entrypoint-new.sh /usr/local/bin/openscap_entrypoint.sh
RUN chmod +x /usr/local/bin/openscap_entrypoint.sh

ENTRYPOINT ["/usr/local/bin/openscap_entrypoint.sh"]
