#!/bin/bash
# Fix: Trivy daily scan cron job
if crontab -l 2>/dev/null | grep -q trivy; then
    echo "SKIP trivy cron already exists"
    crontab -l | grep trivy
    exit 0
fi

(crontab -l 2>/dev/null; \
 echo "0 2 * * * /usr/local/bin/trivy k8s --report=summary cluster >> /var/log/trivy-scan.log 2>&1") \
 | crontab -

echo "DONE trivy cron added"
crontab -l | grep trivy
echo "TRIVY_CRON_DONE"
