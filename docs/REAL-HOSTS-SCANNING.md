# Сканирование реальных хостов, VM и Docker контейнеров

## Обзор

Платформа поддерживает **3 режима сканирования**:

1. **Тестовые контейнеры** (по умолчанию) - для демонстрации
2. **Реальные хосты и VM** - через SSH
3. **Production Docker контейнеры** - через Docker API

---

## 🎯 Режим 1: Тестовые контейнеры (текущий)

**Использование:** Демонстрация, тестирование, разработка

```bash
# Запуск с тестовыми контейнерами
make up

# Сканирование
make scan
```

**Ограничения:**
- Только для демонстрации
- Не отражает реальную безопасность
- Контейнеры изолированы

---

## 🔧 Режим 2: Реальные хосты и VM через SSH

### Архитектура

```
┌─────────────────┐
│  test-hard      │
│  (мониторинг)   │
└────────┬────────┘
         │ SSH
         ├──────────► Host 1 (Ubuntu Server)
         ├──────────► Host 2 (CentOS VM)
         ├──────────► Host 3 (Debian VM)
         └──────────► Host N
```

### Подготовка

#### 1. Настройка SSH доступа

На **каждом целевом хосте**:

```bash
# Создать пользователя для сканирования
sudo useradd -m -s /bin/bash scanner
sudo usermod -aG sudo scanner

# Настроить SSH ключи
sudo mkdir -p /home/scanner/.ssh
sudo chmod 700 /home/scanner/.ssh
```

На **сервере мониторинга**:

```bash
# Генерировать SSH ключ
ssh-keygen -t ed25519 -f ~/.ssh/scanner_key -N ""

# Скопировать на целевые хосты
ssh-copy-id -i ~/.ssh/scanner_key.pub scanner@target-host-1
ssh-copy-id -i ~/.ssh/scanner_key.pub scanner@target-host-2
```

#### 2. Создать inventory файл

```bash
# hosts.ini
cat > hosts.ini << 'EOF'
[production_servers]
web-server-1 ansible_host=192.168.1.10 ansible_user=scanner
web-server-2 ansible_host=192.168.1.11 ansible_user=scanner
db-server-1 ansible_host=192.168.1.20 ansible_user=scanner

[staging_servers]
staging-web ansible_host=192.168.2.10 ansible_user=scanner

[all:vars]
ansible_ssh_private_key_file=~/.ssh/scanner_key
ansible_python_interpreter=/usr/bin/python3
EOF
```

### Запуск сканирования

#### Вариант A: Ansible Playbook (рекомендуется)

Создайте `playbooks/scan-hosts.yml`:

```yaml
---
- name: Security scanning of real hosts
  hosts: all
  become: yes
  gather_facts: yes
  
  tasks:
    - name: Install Lynis
      package:
        name: lynis
        state: present
      when: ansible_os_family in ['Debian', 'RedHat']
    
    - name: Run Lynis audit
      command: lynis audit system --quick --quiet
      register: lynis_output
      changed_when: false
    
    - name: Fetch Lynis report
      fetch:
        src: /var/log/lynis-report.dat
        dest: "./reports/lynis/{{ inventory_hostname }}.dat"
        flat: yes
    
    - name: Fetch Lynis log
      fetch:
        src: /var/log/lynis.log
        dest: "./reports/lynis/{{ inventory_hostname }}.log"
        flat: yes
    
    - name: Parse metrics
      local_action:
        module: shell
        cmd: "python3 scripts/parse_lynis_report.py ./reports/lynis/{{ inventory_hostname }}.log > ./reports/lynis/{{ inventory_hostname }}_metrics.prom"
```

Запуск:

```bash
# Установить Ansible
pip install ansible

# Запустить сканирование
ansible-playbook -i hosts.ini playbooks/scan-hosts.yml

# Проверить результаты
ls -lh reports/lynis/
```

#### Вариант B: SSH скрипт (простой)

Создайте `scripts/scan-remote-host.sh`:

```bash
#!/bin/bash
set -euo pipefail

HOST=$1
USER=${2:-scanner}
SSH_KEY=${3:-~/.ssh/scanner_key}

echo "Scanning $HOST..."

# Установить Lynis если нужно
ssh -i "$SSH_KEY" "$USER@$HOST" "sudo apt-get update && sudo apt-get install -y lynis || sudo dnf install -y lynis"

# Запустить сканирование
ssh -i "$SSH_KEY" "$USER@$HOST" "sudo lynis audit system --quick --quiet"

# Скачать отчеты
scp -i "$SSH_KEY" "$USER@$HOST:/var/log/lynis.log" "./reports/lynis/${HOST}.log"
scp -i "$SSH_KEY" "$USER@$HOST:/var/log/lynis-report.dat" "./reports/lynis/${HOST}.dat"

# Парсить метрики
python3 scripts/parse_lynis_report.py "./reports/lynis/${HOST}.log" > "./reports/lynis/${HOST}_metrics.prom"

echo "✅ Scan complete for $HOST"
```

Использование:

```bash
chmod +x scripts/scan-remote-host.sh

# Сканировать один хост
./scripts/scan-remote-host.sh 192.168.1.10

# Сканировать несколько
for host in 192.168.1.10 192.168.1.11 192.168.1.20; do
  ./scripts/scan-remote-host.sh $host
done
```

---

## 🐳 Режим 3: Production Docker контейнеры

### Архитектура

```
┌─────────────────┐
│  test-hard      │
│  (мониторинг)   │
└────────┬────────┘
         │ Docker API
         ├──────────► nginx-prod
         ├──────────► app-backend
         ├──────────► redis-cache
         └──────────► postgres-db
```

### Подготовка

#### 1. Настроить Docker API доступ

```bash
# На Docker хосте
# Разрешить TCP доступ (только для доверенных сетей!)
sudo systemctl edit docker.service

# Добавить:
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// -H tcp://0.0.0.0:2375

sudo systemctl daemon-reload
sudo systemctl restart docker
```

**⚠️ ВАЖНО:** Для production используйте TLS:

```bash
# Генерировать сертификаты
./scripts/generate-docker-tls.sh

# Настроить Docker с TLS
sudo systemctl edit docker.service
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// -H tcp://0.0.0.0:2376 --tlsverify --tlscacert=/etc/docker/ca.pem --tlscert=/etc/docker/server-cert.pem --tlskey=/etc/docker/server-key.pem
```

#### 2. Создать список контейнеров

```bash
# production-containers.txt
nginx-prod
app-backend-1
app-backend-2
redis-cache
postgres-db
```

### Запуск сканирования

Создайте `scripts/scan-docker-containers.sh`:

```bash
#!/bin/bash
set -euo pipefail

DOCKER_HOST=${1:-tcp://docker-host:2375}
CONTAINERS_FILE=${2:-production-containers.txt}

export DOCKER_HOST

echo "Scanning containers on $DOCKER_HOST..."

while IFS= read -r container; do
  echo "Scanning $container..."
  
  # Установить Lynis в контейнер
  docker exec "$container" sh -c "apt-get update && apt-get install -y lynis || dnf install -y lynis" 2>/dev/null || true
  
  # Запустить сканирование
  docker exec "$container" lynis audit system --quick --quiet
  
  # Скачать отчеты
  docker cp "${container}:/var/log/lynis.log" "./reports/lynis/${container}.log"
  docker cp "${container}:/var/log/lynis-report.dat" "./reports/lynis/${container}.dat" 2>/dev/null || true
  
  # Парсить метрики
  python3 scripts/parse_lynis_report.py "./reports/lynis/${container}.log" > "./reports/lynis/${container}_metrics.prom"
  
  echo "✅ $container scanned"
done < "$CONTAINERS_FILE"
```

Использование:

```bash
chmod +x scripts/scan-docker-containers.sh

# Сканировать контейнеры
./scripts/scan-docker-containers.sh tcp://192.168.1.50:2375 production-containers.txt
```

---

## 📊 Интеграция с Telegraf

После сканирования метрики автоматически подхватываются Telegraf:

```toml
# telegraf/telegraf.conf уже настроен:
[[inputs.file]]
  files = ["/reports/lynis/*_metrics.prom"]
  data_format = "prometheus"
  name_override = "security_scanners"
```

Метрики появятся в Prometheus и Grafana автоматически!

---

## 🔄 Автоматизация

### Cron (для регулярного сканирования)

```bash
# Добавить в crontab
crontab -e

# Сканировать каждую ночь в 2:00
0 2 * * * /path/to/test-hard/scripts/scan-remote-host.sh 192.168.1.10
0 2 * * * /path/to/test-hard/scripts/scan-remote-host.sh 192.168.1.11
```

### Ansible Cron

```yaml
- name: Schedule daily security scans
  cron:
    name: "Security scan"
    hour: "2"
    minute: "0"
    job: "ansible-playbook /path/to/scan-hosts.yml"
```

### Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: security-scan
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: scanner
            image: test-hard/scanner:latest
            command: ["/scripts/scan-all-hosts.sh"]
          restartPolicy: OnFailure
```

---

## 🎯 Рекомендации

### Для Production

1. **Используйте SSH ключи** вместо паролей
2. **Ограничьте доступ** scanner пользователя (только чтение)
3. **Используйте TLS** для Docker API
4. **Сканируйте в off-peak** часы (ночью)
5. **Храните отчеты** минимум 90 дней
6. **Настройте alerts** на критические находки

### Безопасность

```bash
# Ограничить scanner пользователя
sudo visudo
# Добавить:
scanner ALL=(ALL) NOPASSWD: /usr/bin/lynis, /usr/bin/oscap

# Запретить остальное
Defaults:scanner !authenticate
```

### Мониторинг

```yaml
# prometheus/alert.rules.yml
groups:
  - name: security_scans
    rules:
      - alert: LowSecurityScore
        expr: lynis_score < 70
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low security score on {{ $labels.host }}"
          
      - alert: HighWarningsCount
        expr: lynis_warnings > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High warnings count on {{ $labels.host }}"
```

---

## 📝 Примеры использования

### Сканировать все production серверы

```bash
# С Ansible
ansible-playbook -i production-hosts.ini playbooks/scan-hosts.yml

# Проверить результаты
curl "http://localhost:9090/api/v1/query?query=lynis_score"
```

### Сканировать конкретный хост

```bash
./scripts/scan-remote-host.sh web-server-1.example.com
```

### Сканировать Docker контейнеры

```bash
# Получить список running контейнеров
docker ps --format "{{.Names}}" > running-containers.txt

# Сканировать
./scripts/scan-docker-containers.sh tcp://localhost:2375 running-containers.txt
```

---

## 🔍 Troubleshooting

### SSH connection refused

```bash
# Проверить доступность
ssh -i ~/.ssh/scanner_key scanner@target-host

# Проверить firewall
sudo ufw allow 22/tcp
```

### Docker API недоступен

```bash
# Проверить
curl http://docker-host:2375/version

# Проверить firewall
sudo firewall-cmd --add-port=2375/tcp --permanent
```

### Lynis не установлен

```bash
# Debian/Ubuntu
sudo apt-get install -y lynis

# RHEL/CentOS
sudo dnf install -y epel-release
sudo dnf install -y lynis
```

---

## 📚 Дополнительно

- [Ansible Documentation](https://docs.ansible.com/)
- [Lynis Documentation](https://cisofy.com/documentation/lynis/)
- [Docker API](https://docs.docker.com/engine/api/)
