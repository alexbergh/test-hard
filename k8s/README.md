# Kubernetes Deployment

Kubernetes manifests for deploying test-hard monitoring stack.

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- kustomize (or kubectl with kustomize support)
- Storage class for PersistentVolumeClaims

## Quick Start

### Deploy to Development

```bash
# Apply development overlay
kubectl apply -k overlays/dev/

# Check status
kubectl get pods -n monitoring-dev

# Port forward to access services
kubectl port-forward -n monitoring-dev svc/grafana 3000:3000
kubectl port-forward -n monitoring-dev svc/prometheus 9090:9090
```

### Deploy to Staging

```bash
kubectl apply -k overlays/staging/
```

### Deploy to Production

```bash
# Review production configuration
kubectl kustomize overlays/prod/

# Apply (requires proper secrets configured)
kubectl apply -k overlays/prod/
```

## Configuration

### Secrets Management

Production secrets should be managed separately:

```bash
# Create Grafana admin password secret
kubectl create secret generic grafana-credentials \
  --from-literal=admin-user=admin \
  --from-literal=admin-password=$(openssl rand -base64 32) \
  -n monitoring

# Or use sealed-secrets
kubeseal -f grafana-secret.yaml -w grafana-secret-sealed.yaml
```

### Storage

Default storage class is `standard`. Override in overlays:

```yaml
# In overlay kustomization.yaml
patches:
  - patch: |-
      apiVersion: v1
      kind: PersistentVolumeClaim
      metadata:
        name: prometheus-data
      spec:
        storageClassName: fast-ssd
```

### Resource Limits

Adjust in overlays based on your cluster capacity:

```yaml
# prometheus-patch.yaml
resources:
  requests:
    cpu: 1000m
    memory: 2Gi
  limits:
    cpu: 2000m
    memory: 4Gi
```

## Ingress Configuration

Update ingress hosts in overlays:

```yaml
# grafana-ingress-patch.yaml
spec:
  tls:
  - hosts:
    - grafana.your-domain.com
    secretName: grafana-tls
  rules:
  - host: grafana.your-domain.com
```

### Certificate Management

Using cert-manager:

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Monitoring

### Health Checks

```bash
# Check pod status
kubectl get pods -n monitoring -w

# Check pod logs
kubectl logs -n monitoring -l app=prometheus
kubectl logs -n monitoring -l app=grafana

# Describe pod for issues
kubectl describe pod -n monitoring prometheus-xxxxx
```

### Metrics

Access Prometheus from within cluster:

```bash
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://prometheus.monitoring:9090/api/v1/targets
```

## Upgrading

### Rolling Update

```bash
# Update image version in kustomization.yaml
images:
  - name: prom/prometheus
    newTag: v2.53.0

# Apply changes
kubectl apply -k overlays/prod/

# Watch rollout
kubectl rollout status deployment/prometheus -n monitoring
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/prometheus -n monitoring

# Check rollout history
kubectl rollout history deployment/prometheus -n monitoring
```

## Backup and Restore

### Backup Prometheus Data

```bash
# Create backup job
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: prometheus-backup
  namespace: monitoring
spec:
  template:
    spec:
      containers:
      - name: backup
        image: alpine:3.18
        command:
        - sh
        - -c
        - |
          tar czf /backup/prometheus-$(date +%Y%m%d-%H%M%S).tar.gz /prometheus
        volumeMounts:
        - name: prometheus-data
          mountPath: /prometheus
        - name: backup-storage
          mountPath: /backup
      volumes:
      - name: prometheus-data
        persistentVolumeClaim:
          claimName: prometheus-data
      - name: backup-storage
        # Configure your backup storage here
        emptyDir: {}
      restartPolicy: OnFailure
EOF
```

## Troubleshooting

### Pod Not Starting

```bash
# Check events
kubectl get events -n monitoring --sort-by='.lastTimestamp'

# Check pod details
kubectl describe pod -n monitoring <pod-name>

# Check logs
kubectl logs -n monitoring <pod-name> --previous
```

### PVC Binding Issues

```bash
# Check PVC status
kubectl get pvc -n monitoring

# Check storage classes
kubectl get storageclass

# Describe PVC
kubectl describe pvc -n monitoring prometheus-data
```

### Network Issues

```bash
# Test service connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  wget -O- http://prometheus.monitoring:9090/-/healthy

# Check service endpoints
kubectl get endpoints -n monitoring
```

## Scaling

### Horizontal Pod Autoscaling

```bash
# Create HPA for Telegraf
kubectl autoscale deployment telegraf \
  --cpu-percent=80 \
  --min=1 \
  --max=5 \
  -n monitoring
```

### Vertical Scaling

Update resource limits in patches and reapply.

## Cleanup

```bash
# Delete deployment
kubectl delete -k overlays/dev/

# Delete PVCs (careful - this deletes data!)
kubectl delete pvc -n monitoring-dev --all

# Delete namespace
kubectl delete namespace monitoring-dev
```

## Advanced

### Service Mesh Integration

For Istio/Linkerd integration, add annotations in overlays:

```yaml
# In pod template
metadata:
  annotations:
    sidecar.istio.io/inject: "true"
```

### External Secrets

Using external-secrets operator:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: monitoring
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
```

## References

- [Kustomize Documentation](https://kustomize.io/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Prometheus Operator](https://prometheus-operator.dev/)
