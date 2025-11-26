# ArgoCD Deployment Configuration

Automated GitOps deployment для test-hard платформы.

## Установка ArgoCD

```bash
# Создать namespace
kubectl create namespace argocd

# Установить ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Получить initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward для доступа к UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Откройте <https://localhost:8080> и войдите с:

* Username: `admin`
* Password: (из команды выше)

## Развертывание приложений

### Development

```bash
kubectl apply -f argocd/application-dev.yaml
```

Автоматическая синхронизация из ветки `develop`.

### Staging

```bash
kubectl apply -f argocd/application-staging.yaml
```

Автоматическая синхронизация из ветки `main`.

### Production

```bash
kubectl apply -f argocd/application-prod.yaml
```

**Важно:** Production требует ручной синхронизации для безопасности.

```bash
# Синхронизировать production вручную
argocd app sync test-hard-prod
```

## Мониторинг deployment

```bash
# Статус приложения
argocd app get test-hard-dev

# Логи синхронизации
argocd app logs test-hard-dev

# История синхронизаций
argocd app history test-hard-dev

# Rollback к предыдущей версии
argocd app rollback test-hard-prod <revision>
```

## Настройка уведомлений

Для production настроены уведомления в Slack при успешной/неуспешной синхронизации.

Настройте ArgoCD Notifications:

```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  service.slack: |
    token: \$slack-token
  template.app-sync-succeeded: |
    message: |
      Application {{.app.metadata.name}} sync succeeded.
      Revision: {{.app.status.sync.revision}}
  template.app-sync-failed: |
    message: |
      Application {{.app.metadata.name}} sync failed.
      Error: {{.app.status.operationState.message}}
  trigger.on-sync-succeeded: |
    - when: app.status.operationState.phase in ['Succeeded']
      send: [app-sync-succeeded]
  trigger.on-sync-failed: |
    - when: app.status.operationState.phase in ['Error', 'Failed']
      send: [app-sync-failed]
EOF

# Создать secret с Slack token
kubectl create secret generic argocd-notifications-secret \
  --from-literal=slack-token=<YOUR_SLACK_TOKEN> \
  -n argocd
```

## CI/CD Integration

GitHub Actions автоматически обновляет образы при push в main/develop.

ArgoCD автоматически синхронизирует изменения:

* **Dev**: Сразу после merge в develop
* **Staging**: Сразу после merge в main
* **Prod**: Требует ручного подтверждения

## Troubleshooting

### Application OutOfSync

```bash
# Проверить diff
argocd app diff test-hard-dev

# Принудительная синхронизация
argocd app sync test-hard-dev --force
```

### Health Check Failed

```bash
# Проверить статус pods
kubectl get pods -n monitoring-dev

# Проверить логи
kubectl logs -n monitoring-dev -l app=prometheus
```

### Rollback

```bash
# Посмотреть историю
argocd app history test-hard-prod

# Rollback
argocd app rollback test-hard-prod <revision-number>
```

## Best Practices

1. **Development** - Автоматическая синхронизация для быстрой итерации
2. **Staging** - Автоматическая синхронизация для тестирования
3. **Production** - Ручная синхронизация для контроля
4. **Мониторинг** - Настройте alerts для failed deployments
5. **Rollback** - Держите минимум 10 ревизий для быстрого отката

## Ссылки

* [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
* [ArgoCD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)
* [GitOps Principles](https://opengitops.dev/)
