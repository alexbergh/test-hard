# ROADMAP — План развития test-hard

**Версия:** 1.0.0  
**Статус:** Production Ready (9.0/10)  
**Test Coverage:** 80%+  
**Последнее обновление:** Февраль 2026

---

## Текущее состояние проекта

### Реализовано

| Компонент | Статус | Описание |
|-----------|--------|----------|
| **Security Scanning** | Ready | OpenSCAP, Lynis для контейнеров |
| **Monitoring Stack** | Ready | Prometheus + Grafana + Alertmanager |
| **Centralized Logging** | Ready | Loki + Promtail |
| **Atomic Red Team** | Ready | MITRE ATT&CK тесты (dry-run) |
| **GitOps Deployment** | Ready | ArgoCD интеграция |
| **Container Registry** | Ready | GitHub Container Registry + Cosign |
| **Multi-Environment** | Ready | dev/staging/prod через Docker Compose |
| **CI/CD Pipeline** | Ready | GitHub Actions (8 workflows) |
| **Kubernetes Support** | Ready | Kustomize overlays (dev/staging/prod) |
| **Multi-Distribution** | Ready | Debian, Ubuntu, Fedora, CentOS, ALT Linux |
| **Metrics Collection** | Ready | Telegraf → Prometheus |
| **Docker Security** | Ready | Docker Socket Proxy |
| **Test Suite** | Ready | Unit + Integration + E2E + Shell |
| **Documentation** | Ready | 13 документов в docs/ |
| **Runtime Security** | Ready | Falco + Falcosidekick + автоматические реакции |
| **Container Image Scanning** | Ready | Trivy + SBOM + OPA/Gatekeeper |
| **Grafana Dashboards** | Ready | 7 дашбордов (security, compliance, resources, Falco, images) |

---

## Q4 2025 — Web UI & Automation [COMPLETED]

### Приоритет: Высокий

#### 1. Web Dashboard для управления сканированиями [DONE]

- [x] **Backend API** (FastAPI)
  - REST API для запуска/остановки сканов
  - JWT аутентификация
  - RBAC (viewer, operator, admin)
  - SQLAlchemy + async SQLite
- [x] **Frontend** (React + TailwindCSS)
  - Dashboard с обзором всех хостов
  - Визуализация результатов сканирования
  - Управление расписанием сканов
  - Zustand для state management
- [x] **Интеграция с существующим стеком**
  - Prometheus/Grafana интеграция
  - Docker API через proxy

#### 2. Scheduled Scanning [DONE]

- [x] APScheduler для автоматических сканов
- [x] Cron expressions для расписаний
- [x] Поддержка различных расписаний для разных хостов
- [x] Notification settings (готово к интеграции)

#### 3. Distributed Tracing [DONE]

- [x] Grafana Tempo конфигурация
- [x] OpenTelemetry instrumentation в FastAPI
- [x] Tempo datasource для Grafana
- [x] docker-compose.tracing.yml overlay

---

## Q1 2026 — Runtime Security & Image Scanning [COMPLETED]

### Приоритет: Высокий

#### 4. Runtime Security с Falco [DONE]

- [x] Falco deployment (Docker + Kubernetes)
- [x] Custom rules для hardening detection (30+ правил, 7 категорий)
- [x] Интеграция с Alertmanager (через Falcosidekick)
- [x] Grafana дашборд для Falco events
- [x] Automated response actions (falco-responder: kill, stop, isolate, pause)
- [x] Falco-exporter для Prometheus метрик
- [x] 10 Prometheus alert rules для Falco

#### 5. Container Image Scanning [DONE]

- [x] Trivy интеграция для vulnerability scanning
- [x] SBOM (Software Bill of Materials) генерация (CycloneDX + SPDX)
- [x] Policy enforcement (OPA/Gatekeeper — 7 политик)
- [x] CI/CD блокировка уязвимых образов (GitHub Actions workflow)
- [x] Trivy-сервер в docker-compose для локального сканирования
- [x] Grafana дашборд для результатов сканирования
- [x] Скрипт scan-images.sh для локального сканирования

#### 6. Network Security Monitoring [DONE]

- [x] Network policy enforcement (Kubernetes) — 11 NetworkPolicy для всех сервисов
- [x] Traffic analysis и anomaly detection — Prometheus alerts, Telegraf netstat, Grafana дашборд
- [x] Service mesh интеграция (Istio/Linkerd) — PeerAuthentication, AuthorizationPolicy, DestinationRule, Server, ServerAuthorization

#### 6a. CIS Benchmarks Compliance [DONE]

- [x] OPA Gatekeeper — 14 CIS-политик (CIS K8s v1.12.0: 5.2.x, 5.3.x, 5.5.x, 5.7.x)
- [x] Pod Security Admission — restricted/baseline/privileged per namespace (K8s 1.25+)
- [x] kube-bench config — 60 проверок (Control Plane, API Server, Controller Manager, Scheduler, ETCD, TLS, Kubelet)
- [x] Capabilities management — risk matrix, namespace rules, blocked/approved lists
- [x] CIS-compliant deployment template (5.2.1-5.2.8, 5.7.2)
- [x] Kyverno — Cosign image verification, AlwaysPullImages, automountServiceAccountToken control
- [x] RBAC hardening — dedicated ServiceAccounts, least privilege roles, cluster-admin restriction (CIS 5.1.x)
- [x] EncryptionConfiguration template — Secrets at rest encryption (CIS 1.2.12, AES-CBC)
- [x] TLS hardening — tls-min-version, cipher-suites, etcd IP restrictions (CIS 1.2.22/1.2.29)
- [x] Kubelet hardening — protect-kernel-defaults, rotate-certificates, event-qps (CIS 4.2.x)

---

## Q2 2026 — Compliance & Intelligence

### Приоритет: Средний

#### 7. Compliance as Code

- [ ] **InSpec profiles**
  - CIS Benchmarks
  - PCI-DSS
  - HIPAA
  - SOC 2
- [ ] **OPA (Open Policy Agent)**
  - Policy-as-code для Kubernetes
  - Admission controller
  - Audit logging
- [ ] **Compliance reporting**
  - Автоматическая генерация отчётов
  - Gap analysis
  - Remediation recommendations

#### 8. ML-based Anomaly Detection

- [ ] Baseline behavior profiling
- [ ] Anomaly detection models (isolation forest, autoencoders)
- [ ] Integration с Prometheus/Loki
- [ ] Alert correlation и noise reduction
- [ ] Threat intelligence feeds

#### 9. Multi-tenancy Support

- [ ] Namespace isolation
- [ ] Per-tenant dashboards
- [ ] Resource quotas
- [ ] Billing/usage tracking

---

## Q3 2026 — Enterprise & Multi-Cloud

### Приоритет: Средний

#### 10. Multi-Cloud Support

- [ ] **AWS**
  - EC2 instance scanning
  - EKS integration
  - AWS Security Hub export
  - IAM policy analysis
- [ ] **Azure**
  - Azure VM scanning
  - AKS integration
  - Azure Defender integration
- [ ] **GCP**
  - GCE instance scanning
  - GKE integration
  - Security Command Center

#### 11. Advanced Reporting & Analytics

- [ ] Executive dashboards
- [ ] Trend analysis
- [ ] Risk scoring
- [ ] Benchmark comparisons
- [ ] Custom report builder

#### 12. Integration Marketplace

- [ ] Plugin architecture
- [ ] Third-party scanner integrations
- [ ] SIEM connectors (Splunk, Elastic, QRadar)
- [ ] Ticketing systems (Jira, ServiceNow)
- [ ] ChatOps (Slack, Teams, Discord)

---

## Q4 2026 - 2027+ — Long-term Vision

### Исследование и разработка

#### 13. AI-Powered Security

- [ ] LLM-based remediation suggestions
- [ ] Natural language queries для логов
- [ ] Automated incident response playbooks
- [ ] Predictive security analytics

#### 14. Zero Trust Architecture

- [ ] Identity-aware proxy
- [ ] Continuous verification
- [ ] Micro-segmentation
- [ ] Device trust scoring

#### 15. Edge Security

- [ ] IoT device scanning
- [ ] Edge Kubernetes (K3s, MicroK8s)
- [ ] Lightweight agents
- [ ] Offline operation mode

---

## Технический долг

### Требует внимания

| Задача | Приоритет | Сложность |
|--------|-----------|-----------|
| Миграция на Python 3.12+ | Средний | Низкая |
| Обновление зависимостей | Высокий | Низкая |
| Рефакторинг entrypoint скриптов | Низкий | Средняя |
| Улучшение error handling | Средний | Средняя |
| Добавление E2E тестов для K8s | Средний | Высокая |
| Helm chart создание | Высокий | Средняя |
| OpenAPI спецификация | Средний | Низкая |
| Performance benchmarks | Низкий | Средняя |

---

## Метрики успеха

### KPIs для отслеживания

| Метрика | Текущее | Цель Q2 2026 | Цель Q4 2026 |
|---------|---------|--------------|--------------|
| Test Coverage | 80% | 85% | 90% |
| Documentation Coverage | 90% | 95% | 98% |
| Mean Time to Scan | ~5 min | ~3 min | ~2 min |
| Supported Distributions | 5 | 8 | 12 |
| Active Integrations | 5 | 10 | 20 |
| Community Contributors | 1 | 5 | 15 |

---

## Как внести вклад

1. Выберите задачу из roadmap
2. Создайте issue с описанием реализации
3. Fork репозитория
4. Реализуйте функционал
5. Создайте Pull Request

См. [CONTRIBUTING.md](CONTRIBUTING.md) для подробностей.

---

## Changelog

### v1.0.0 (Ноябрь 2025)

- Initial production release
- Full monitoring stack
- Multi-distribution support
- Kubernetes deployment
- 80%+ test coverage

---

*Roadmap обновляется ежеквартально. Приоритеты могут меняться в зависимости от обратной связи.*
