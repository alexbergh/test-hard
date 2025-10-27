FROM registry.fedoraproject.org/fedora:40

RUN dnf -y update && \
    dnf -y install openscap-scanner scap-security-guide docker python3 && \
    dnf clean all && \
    rm -rf /var/cache/dnf

COPY entrypoint.py /usr/local/bin/openscap_entrypoint.py
RUN chmod +x /usr/local/bin/openscap_entrypoint.py

ENTRYPOINT ["/usr/bin/env", "python3", "/usr/local/bin/openscap_entrypoint.py"]
