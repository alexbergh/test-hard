#!/bin/bash
# Fix: kube-proxy metricsBindAddress = 127.0.0.1:10249
CURRENT=$(kubectl -n kube-system get configmap kube-proxy \
  -o jsonpath='{.data.config\.conf}' 2>/dev/null | grep metricsBindAddress)
echo "Current metricsBindAddress: $CURRENT"

if echo "$CURRENT" | grep -q '127.0.0.1'; then
    echo "SKIP already set to 127.0.0.1"
    exit 0
fi

kubectl -n kube-system get configmap kube-proxy -o json 2>/dev/null | \
python3 -c "
import json, sys, re

d = json.load(sys.stdin)
conf = d['data'].get('config.conf', '')

if 'metricsBindAddress' in conf:
    conf = re.sub(r'metricsBindAddress:\s*\S*', 'metricsBindAddress: \"127.0.0.1:10249\"', conf)
else:
    conf = conf.rstrip() + '\nmetricsBindAddress: \"127.0.0.1:10249\"\n'

d['data']['config.conf'] = conf
print(json.dumps(d))
" | kubectl apply -f - 2>&1

kubectl -n kube-system rollout restart daemonset kube-proxy 2>&1
kubectl -n kube-system rollout status daemonset kube-proxy --timeout=60s 2>&1
echo "KUBE_PROXY_FIX_DONE"
