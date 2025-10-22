# Тестовые виртуальные машины для hardening

Пакет `tests/vms` описывает построение контрольных виртуальных машин на базе 
дистрибутивов, указанных в требованиях (РедОС 7.3, РедОС 8, Astra Linux 1.7,
Альт 8, CentOS 7). Цель — обеспечить одинаковый профиль проверки в тестовой и
продовой среде, а также подготовить артефакты, подтверждающие выполнение
сценариев hardening и сбор метрик через связку osquery + Telegraf.

## Состав

- `packer/linux.pkr.hcl` — универсальный шаблон Packer с параметром `distro`
  для сборки образов любой из пяти ОС. Значения ISO и контрольных сумм 
  передаются через переменные или `-var-file`. По умолчанию используются
  локальные пути `file:///isos/<distro>.iso` и фиктивные checksum, чтобы
  подчеркнуть необходимость подстановки реальных артефактов.
- `packer/http/` — kickstart/preseed-конфигурации и postinstall-скрипты,
  которые подготавливают пользователя `secops`, отключают root-вход по SSH и
  подключают Ansible для дальнейших сценариев hardening.
- `ansible/playbooks/hardening.yml` — единый плейбук, который применяет базовые
  роли (`common_baseline`, `linux_cis`, `secaudit_profiles`) к новой ВМ.
- `run.sh` — управляющий скрипт. При наличии Packer и переменной
  `HARDENING_VM_MODE=packer` запускает сборку образов. В остальных случаях
  включает оффлайн-симуляцию, которая формирует доказательную базу в
  `tests/vms/artifacts`.
- `simulate.py` — модель запуска, считывающая описания сценариев из
  `hardening-scenarios/secaudit/profiles` и генерирующая отчёты/метрики,
  идентичные тем, что поступают в Grafana/KUMA от osquery/Telegraf.

## Подготовка ISO

Для реального прогона необходимо вручную скачать дистрибутивы и передать Packer
пути к ISO и контрольным суммам. Пример `vars.auto.pkrvars.hcl`:

```hcl
images = {
  "redos-7.3" = {
    iso_url      = "file:///var/lib/libvirt/images/RELEASE/redos-7.3.iso"
    iso_checksum = "sha256:..."
  }
  "astralinux-1.7" = {
    iso_url      = "file:///var/lib/libvirt/images/astralinux-smolensk-1.7.iso"
    iso_checksum = "sha256:..."
  }
}
```

Packer запускается так:

```bash
export HARDENING_VM_MODE=packer
./tests/vms/run.sh test            # соберёт все тестовые образы
./tests/vms/run.sh prod            # соберёт все продуктивные образы
```

Убедитесь, что переменная `HARDENING_VM_IMAGE_VARS` указывает на файл с
переменными, если он не лежит в текущем каталоге:

```bash
export HARDENING_VM_IMAGE_VARS=$PWD/vars.auto.pkrvars.hcl
```

## Оффлайн-симуляция

В CI и на рабочих станциях без гипервизора скрипт автоматически переключается в
симуляцию:

```bash
./tests/vms/run.sh            # создаёт артефакты для test/prod
./tests/vms/run.sh test       # только тестовый контур
./tests/vms/run.sh prod       # только продуктивный контур
```

Результаты записываются в `tests/vms/artifacts/<environment>/` и включают:

- план виртуализации и журнал условного билда для каждой ОС;
- отчёт соответствия контролям из `secaudit-core` (см. каталог
  `hardening-scenarios/secaudit/profiles`);
- агрегированные события telemetry (`telemetry/events.jsonl`) и визуализации
  (Markdown-панель, экспорт Grafana, payload для KUMA), которые демонстрируют
  сбор метрик hardening.

## Интеграция с остальными стендами

- Созданные образы подключаются к Ansible-инвентарю из
  `hardening-scenarios/ansible/inventory.ini` через группы `vm_test` и
  `vm_prod`.
- После применения плейбука `ansible/playbooks/hardening.yml` метрики автоматически
  подхватываются osquery/Telegraf и визуализируются совместно с данными из
  Docker/kind симуляций.

