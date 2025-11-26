# Установка без Docker (нативная установка)

## Обзор

Данное руководство описывает установку платформы test-hard на физических серверах или виртуальных машинах без использования Docker. Подходит для:

* Production серверов, где Docker запрещен политиками безопасности
* BSD систем (FreeBSD, OpenBSD)
* Минимальных установок Linux
* Встроенных систем и appliance

---

## Поддерживаемые платформы

### Linux

* Debian 11, 12
* Ubuntu 20.04, 22.04, 24.04
* Fedora 39, 40
* CentOS Stream 9
* ALT Linux c10f2, latest
* RHEL 8, 9
* Rocky Linux 8, 9

### BSD

* FreeBSD 13.x, 14.x
* OpenBSD 7.x

---

## Архитектура нативной установки

```
┌─────────────────────────────────────────────────┐
│              Целевой сервер                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────┐      ┌──────────────┐        │
│  │   Lynis     │      │  OpenSCAP    │        │
│  └──────┬──────┘      └──────┬───────┘        │
│         │                    │                 │
│         ├────────────────────┤                 │
│         ▼                    ▼                 │
│  ┌──────────────────────────────┐             │
│  │   Локальные отчеты           │             │
│  │   /var/lib/hardening/        │             │
│  └──────────┬───────────────────┘             │
│             │                                  │
│             ▼                                  │
│  ┌──────────────────────────────┐             │
│  │   Telegraf Agent             │             │
│  │   (сбор метрик)              │             │
│  └──────────┬───────────────────┘             │
│             │                                  │
└─────────────┼──────────────────────────────────┘
              │ HTTP/HTTPS
              ▼
┌─────────────────────────────────────────────────┐
│         Сервер мониторинга                      │
├─────────────────────────────────────────────────┤
│  ┌─────────────┐      ┌──────────────┐        │
│  │ Prometheus  │◄─────┤  Telegraf    │        │
│  └──────┬──────┘      └──────────────┘        │
│         │                                      │
│         ▼                                      │
│  ┌─────────────┐                              │
│  │  Grafana    │                              │
│  └─────────────┘                              │
└─────────────────────────────────────────────────┘
```

---

## Установка на целевых серверах

### Debian/Ubuntu

```bash
#!/bin/bash
# Установка на Debian/Ubuntu

# 1. Обновить систему
sudo apt-get update && sudo apt-get upgrade -y

# 2. Установить Lynis
sudo apt-get install -y lynis

# 3. Установить OpenSCAP (если нужен)
sudo apt-get install -y libopenscap8 openscap-utils

# 4. Установить Telegraf
wget -q https://repos.influxdata.com/influxdata-archive_compat.key
echo '393e8779c89ac8d958f81f942f9ad7fb82a25e133faddaf92e15b16e6ac9ce4c influxdata-archive_compat.key' | sha256sum -c && cat influxdata-archive_compat.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null
echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list
sudo apt-get update && sudo apt-get install -y telegraf

# 5. Создать директории
sudo mkdir -p /var/lib/hardening/{results,scripts}
sudo mkdir -p /var/lib/hardening/results/{lynis,openscap}

# 6. Установить Python для скриптов парсинга
sudo apt-get install -y python3 python3-pip
```

### Fedora/RHEL/CentOS/Rocky/ALT Linux

```bash
#!/bin/bash
# Установка на Fedora/RHEL/CentOS/Rocky Linux

# 1. Обновить систему
sudo dnf update -y

# 2. Установить EPEL репозиторий (для RHEL/CentOS)
sudo dnf install -y epel-release

# 3. Установить Lynis
sudo dnf install -y lynis

# 4. Установить OpenSCAP
sudo dnf install -y openscap openscap-scanner scap-security-guide

# 5. Установить Telegraf
cat <<EOF | sudo tee /etc/yum.repos.d/influxdata.repo
[influxdata]
name = InfluxData Repository
baseurl = https://repos.influxdata.com/rhel/\$releasever/\$basearch/stable
enabled = 1
gpgcheck = 1
gpgkey = https://repos.influxdata.com/influxdata-archive_compat.key
EOF

sudo dnf install -y telegraf

# 6. Создать директории
sudo mkdir -p /var/lib/hardening/{results,scripts}
sudo mkdir -p /var/lib/hardening/results/{lynis,openscap}

# 7. Установить Python
sudo dnf install -y python3 python3-pip
```

### ALT Linux (специфичная установка)

```bash
#!/bin/bash
# Установка на ALT Linux

# 1. Обновить систему
sudo apt-get update && sudo apt-get dist-upgrade -y

# 2. Установить Lynis
sudo apt-get install -y lynis

# 3. Установить OpenSCAP (если доступен)
sudo apt-get install -y openscap || echo "OpenSCAP недоступен для ALT Linux"

# 4. Установить Telegraf (собрать из исходников или использовать бинарник)
wget https://dl.influxdata.com/telegraf/releases/telegraf-1.28.5_linux_amd64.tar.gz
tar xf telegraf-1.28.5_linux_amd64.tar.gz
sudo cp telegraf-1.28.5/usr/bin/telegraf /usr/local/bin/
sudo mkdir -p /etc/telegraf

# 5. Создать директории
sudo mkdir -p /var/lib/hardening/{results,scripts}
sudo mkdir -p /var/lib/hardening/results/{lynis,openscap}

# 6. Установить Python
sudo apt-get install -y python3 python3-pip
```

### FreeBSD

```bash
#!/bin/sh
# Установка на FreeBSD

# 1. Обновить систему
sudo pkg update && sudo pkg upgrade -y

# 2. Установить Lynis
sudo pkg install -y security/lynis

# 3. Установить Telegraf
sudo pkg install -y net-mgmt/telegraf

# 4. Создать директории
sudo mkdir -p /var/lib/hardening/{results,scripts}
sudo mkdir -p /var/lib/hardening/results/lynis

# 5. Установить Python
sudo pkg install -y python3 py39-pip

# 6. Включить службы
sudo sysrc telegraf_enable="YES"
```

### OpenBSD

```bash
#!/bin/sh
# Установка на OpenBSD

# 1. Обновить систему
doas pkg_add -u

# 2. Установить Lynis
doas pkg_add lynis

# 3. Установить Telegraf
doas pkg_add telegraf

# 4. Создать директории
doas mkdir -p /var/lib/hardening/{results,scripts}
doas mkdir -p /var/lib/hardening/results/lynis

# 5. Установить Python
doas pkg_add python3

# 6. Включить службы
doas rcctl enable telegraf
```

---

## Установка скриптов парсинга

```bash
# Клонировать репозиторий (или скопировать скрипты)
git clone https://github.com/alexbergh/test-hard.git /tmp/test-hard

# Скопировать скрипты
sudo cp /tmp/test-hard/scripts/parse_lynis_report.py /var/lib/hardening/scripts/
sudo cp /tmp/test-hard/scripts/parse_openscap_report.py /var/lib/hardening/scripts/
sudo cp /tmp/test-hard/scripts/run_lynis.sh /var/lib/hardening/scripts/
sudo cp /tmp/test-hard/scripts/run_openscap.sh /var/lib/hardening/scripts/

# Сделать исполняемыми
sudo chmod +x /var/lib/hardening/scripts/*.sh
```

---

## Настройка сканирования

### Создание systemd сервиса для Lynis (Linux)

```bash
# Создать сервис
sudo tee /etc/systemd/system/hardening-lynis.service << 'EOF'
[Unit]
Description=Lynis Security Audit
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/var/lib/hardening
ExecStart=/usr/bin/lynis audit system --quick --quiet
ExecStartPost=/usr/bin/python3 /var/lib/hardening/scripts/parse_lynis_report.py /var/log/lynis.log > /var/lib/hardening/results/lynis/metrics.prom
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Создать таймер для ежедневного запуска
sudo tee /etc/systemd/system/hardening-lynis.timer << 'EOF'
[Unit]
Description=Daily Lynis Security Audit
Requires=hardening-lynis.service

[Timer]
OnCalendar=daily
OnBootSec=15min
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Включить и запустить
sudo systemctl daemon-reload
sudo systemctl enable --now hardening-lynis.timer
```

### Создание cron задачи для Lynis (BSD)

```bash
# Для FreeBSD/OpenBSD
sudo tee /usr/local/bin/hardening-scan.sh << 'EOF'
#!/bin/sh
# Lynis scan
/usr/local/bin/lynis audit system --quick --quiet
python3 /var/lib/hardening/scripts/parse_lynis_report.py /var/log/lynis.log > /var/lib/hardening/results/lynis/metrics.prom
EOF

sudo chmod +x /usr/local/bin/hardening-scan.sh

# Добавить в crontab
echo "0 2 * * * /usr/local/bin/hardening-scan.sh" | sudo crontab -
```

---

## Настройка Telegraf

### Конфигурация Telegraf

```bash
sudo tee /etc/telegraf/telegraf.conf << 'EOF'
[agent]
  interval = "60s"
  round_interval = true
  metric_batch_size = 1000
  metric_buffer_limit = 10000
  collection_jitter = "0s"
  flush_interval = "10s"
  flush_jitter = "0s"
  precision = ""
  hostname = ""
  omit_hostname = false

# Отправка в Prometheus
[[outputs.prometheus_client]]
  listen = ":9091"
  metric_version = 2
  path = "/metrics"

# Чтение метрик Lynis
[[inputs.file]]
  files = ["/var/lib/hardening/results/lynis/metrics.prom"]
  data_format = "prometheus"
  name_override = "security_scanners"

# Чтение метрик OpenSCAP (если есть)
[[inputs.file]]
  files = ["/var/lib/hardening/results/openscap/metrics.prom"]
  data_format = "prometheus"
  name_override = "security_scanners"

# Системные метрики
[[inputs.cpu]]
  percpu = true
  totalcpu = true
  collect_cpu_time = false
  report_active = false

[[inputs.disk]]
  ignore_fs = ["tmpfs", "devtmpfs", "devfs", "iso9660", "overlay", "aufs", "squashfs"]

[[inputs.mem]]

[[inputs.system]]
EOF

# Перезапустить Telegraf
sudo systemctl restart telegraf  # Linux
# или
sudo service telegraf restart    # FreeBSD
# или
doas rcctl restart telegraf      # OpenBSD
```

---

## Установка сервера мониторинга

Сервер мониторинга можно установить на отдельной машине.

### Prometheus

**Debian/Ubuntu:**

```bash
sudo apt-get install -y prometheus

# Или установить последнюю версию вручную
wget https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.linux-amd64.tar.gz
tar xf prometheus-2.47.0.linux-amd64.tar.gz
sudo mv prometheus-2.47.0.linux-amd64 /opt/prometheus
sudo useradd --no-create-home --shell /bin/false prometheus
sudo chown -R prometheus:prometheus /opt/prometheus
```

**FreeBSD:**

```bash
sudo pkg install -y net-mgmt/prometheus2
sudo sysrc prometheus_enable="YES"
```

### Конфигурация Prometheus

```bash
sudo tee /etc/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 60s
  evaluation_interval: 60s

scrape_configs:
  - job_name: 'telegraf'
    static_configs:
      - targets: 
        - 'server1.example.com:9091'
        - 'server2.example.com:9091'
        - 'server3.example.com:9091'
        labels:
          environment: 'production'
EOF

sudo systemctl restart prometheus  # Linux
# или
sudo service prometheus restart    # FreeBSD
```

### Grafana

**Debian/Ubuntu:**

```bash
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install -y grafana

sudo systemctl enable --now grafana-server
```

**Fedora/RHEL:**

```bash
sudo tee /etc/yum.repos.d/grafana.repo << 'EOF'
[grafana]
name=grafana
baseurl=https://packages.grafana.com/oss/rpm
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://packages.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF

sudo dnf install -y grafana
sudo systemctl enable --now grafana-server
```

**FreeBSD:**

```bash
sudo pkg install -y grafana9
sudo sysrc grafana_enable="YES"
sudo service grafana start
```

---

## Проверка установки

### Проверить Lynis

```bash
# Запустить вручную
sudo lynis audit system --quick

# Проверить отчет
cat /var/log/lynis.log

# Проверить метрики
cat /var/lib/hardening/results/lynis/metrics.prom
```

### Проверить Telegraf

```bash
# Проверить статус
sudo systemctl status telegraf  # Linux
sudo service telegraf status    # FreeBSD
doas rcctl check telegraf       # OpenBSD

# Проверить метрики
curl http://localhost:9091/metrics
```

### Проверить Prometheus

```bash
# Проверить статус
sudo systemctl status prometheus  # Linux
sudo service prometheus status    # FreeBSD

# Открыть веб-интерфейс
curl http://localhost:9090
```

### Проверить Grafana

```bash
# Открыть веб-интерфейс
curl http://localhost:3000

# Login: admin
# Password: admin (изменить при первом входе!)
```

---

## Автоматизация с Ansible

### Playbook для установки на множество серверов

```yaml
# playbook-install-hardening.yml
---
- name: Install test-hard on bare metal
  hosts: all
  become: yes
  
  tasks:
    - name: Install Lynis (Debian/Ubuntu)
      apt:
        name: lynis
        state: present
      when: ansible_os_family == "Debian"
    
    - name: Install Lynis (RedHat/Fedora)
      dnf:
        name: lynis
        state: present
      when: ansible_os_family == "RedHat"
    
    - name: Install Telegraf (Debian/Ubuntu)
      apt:
        name: telegraf
        state: present
        update_cache: yes
      when: ansible_os_family == "Debian"
    
    - name: Create directories
      file:
        path: "{{ item }}"
        state: directory
        mode: '0755'
      loop:
        - /var/lib/hardening
        - /var/lib/hardening/results
        - /var/lib/hardening/results/lynis
        - /var/lib/hardening/scripts
    
    - name: Copy parsing scripts
      copy:
        src: "{{ item }}"
        dest: /var/lib/hardening/scripts/
        mode: '0755'
      loop:
        - scripts/parse_lynis_report.py
        - scripts/run_lynis.sh
    
    - name: Setup systemd timer
      template:
        src: hardening-lynis.{{ item }}.j2
        dest: /etc/systemd/system/hardening-lynis.{{ item }}
      loop:
        - service
        - timer
      notify: reload systemd
    
    - name: Enable hardening timer
      systemd:
        name: hardening-lynis.timer
        enabled: yes
        state: started
  
  handlers:
    - name: reload systemd
      systemd:
        daemon_reload: yes
```

**Запуск:**

```bash
ansible-playbook -i inventory.ini playbook-install-hardening.yml
```

---

## Troubleshooting

### Lynis не запускается

```bash
# Проверить версию
lynis show version

# Проверить права
ls -la /usr/share/lynis/

# Запустить в debug режиме
sudo lynis audit system --debug
```

### Telegraf не собирает метрики

```bash
# Проверить конфигурацию
telegraf --config /etc/telegraf/telegraf.conf --test

# Проверить логи
sudo journalctl -u telegraf -f  # Linux
tail -f /var/log/telegraf.log   # BSD

# Проверить файлы метрик
ls -la /var/lib/hardening/results/lynis/
cat /var/lib/hardening/results/lynis/metrics.prom
```

### Prometheus не видит targets

```bash
# Проверить доступность Telegraf
curl http://<server-ip>:9091/metrics

# Проверить firewall
sudo ufw allow 9091/tcp  # Ubuntu/Debian
sudo firewall-cmd --add-port=9091/tcp --permanent  # RHEL/Fedora
sudo firewall-cmd --reload
```

---

## Безопасность нативной установки

### Firewall правила

**Linux (ufw):**

```bash
# Разрешить только с monitoring сервера
sudo ufw allow from <monitoring-server-ip> to any port 9091 proto tcp
```

**Linux (firewalld):**

```bash
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="<monitoring-server-ip>" port port="9091" protocol="tcp" accept'
sudo firewall-cmd --reload
```

**FreeBSD (pf):**

```bash
# /etc/pf.conf
pass in on em0 proto tcp from <monitoring-server-ip> to any port 9091
```

### SSL/TLS для Telegraf

```bash
# Генерировать сертификаты
openssl req -x509 -newkey rsa:4096 -keyout /etc/telegraf/key.pem -out /etc/telegraf/cert.pem -days 365 -nodes

# Обновить конфигурацию Telegraf
[[outputs.prometheus_client]]
  listen = ":9091"
  tls_cert = "/etc/telegraf/cert.pem"
  tls_key = "/etc/telegraf/key.pem"
```

---

## Сравнение: Docker vs Native

| Аспект | Docker | Native |
|--------|--------|--------|
| **Установка** | Проще (docker-compose up) | Сложнее (много шагов) |
| **Обслуживание** | Проще обновление образов | Обновление пакетов вручную |
| **Ресурсы** | Больше overhead | Меньше overhead |
| **Безопасность** | Изоляция контейнеров | Прямой доступ к системе |
| **Совместимость** | Одинаково на всех ОС | Зависит от дистрибутива |
| **Production** | Не везде разрешен | Всегда доступен |
| **BSD** | Ограниченная поддержка | Полная поддержка |

---

## Дополнительные ресурсы

* **Lynis**: <https://cisofy.com/lynis/>
* **OpenSCAP**: <https://www.open-scap.org/>
* **Telegraf**: <https://docs.influxdata.com/telegraf/>
* **Prometheus**: <https://prometheus.io/docs/>
* **Grafana**: <https://grafana.com/docs/>

---

**Статус**: Production Ready  
**Последнее обновление**: Ноябрь 2025
