#!/bin/bash
SSH="ssh -i /root/.ssh/k8s_cluster_ed25519 -o StrictHostKeyChecking=no -o ConnectTimeout=10"
ALL="10.10.10.10 10.10.10.11 10.10.10.12 10.10.10.13 10.10.10.14"
for node in $ALL; do
    host=$($SSH root@$node hostname 2>/dev/null)
    mem_total=$($SSH root@$node "awk '/MemTotal/{print \$2}' /proc/meminfo" 2>/dev/null)
    mem_avail=$($SSH root@$node "awk '/MemAvailable/{print \$2}' /proc/meminfo" 2>/dev/null)
    mem_used=$(( (mem_total - mem_avail) / 1024 ))
    mem_total_mb=$(( mem_total / 1024 ))
    load=$($SSH root@$node "awk '{print \$1}' /proc/loadavg" 2>/dev/null)
    procs=$($SSH root@$node "ps aux --no-headers | wc -l" 2>/dev/null)
    echo "NODE|${host}|${node}|${mem_used}|${mem_total_mb}|${load}|${procs}"
done
pods_total=$(kubectl get pods -A --no-headers 2>/dev/null | wc -l)
pods_run=$(kubectl get pods -A --no-headers 2>/dev/null | grep -c Running)
ns=$(kubectl get ns --no-headers 2>/dev/null | wc -l)
np=$(kubectl get networkpolicies -A --no-headers 2>/dev/null | wc -l)
sec=$(kubectl get secrets -A --no-headers 2>/dev/null | wc -l)
kp=$(kubectl get clusterpolicies --no-headers 2>/dev/null | wc -l)
audit=$(du -sh /var/log/kubernetes/audit.log 2>/dev/null | cut -f1)
ipt=$(iptables -L 2>/dev/null | wc -l)
echo "CLUSTER|${pods_total}|${pods_run}|${ns}|${np}|${sec}|${kp}|${audit}|${ipt}"
