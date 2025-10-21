variable "distro" {
  type    = string
  default = "redos-7.3"
  description = "Идентификатор дистрибутива (redos-7.3, redos-8, astralinux-1.7, altlinux-8, centos-7)"
}

variable "environment" {
  type    = string
  default = "test"
  description = "Целевой контур (test или prod)"
}

variable "images" {
  description = "Пути к ISO и контрольным суммам для каждой ОС"
  type = map(object({
    iso_url      = string
    iso_checksum = string
  }))
  default = {}
}

variable "output_directory" {
  type    = string
  default = "output"
  description = "Каталог для готовых qcow2 образов"
}

variable "ssh_password" {
  type    = string
  default = "ChangeMe!"
  description = "Пароль учетной записи secops, создаваемой при установке"
}

locals {
  systems = {
    "redos-7.3" = {
      family        = "redhat7"
      name          = "РедОС 7.3"
      http_dir      = "redos"
      disk_size     = 30720
      memory        = 4096
      cpus          = 2
      ssh_username  = "secops"
      boot_command  = [
        "<wait5>",
        "linux inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/redos-ks.cfg",
        " inst.lang=ru_RU inst.text net.ifnames=0 biosdevname=0",
        " console=ttyS0",
        "<enter>"
      ]
    }
    "redos-8" = {
      family        = "redhat8"
      name          = "РедОС 8"
      http_dir      = "redos"
      disk_size     = 40960
      memory        = 4096
      cpus          = 2
      ssh_username  = "secops"
      boot_command  = [
        "<wait5>",
        "linux inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/redos8-ks.cfg",
        " inst.lang=ru_RU inst.text ip=dhcp",
        " console=ttyS0",
        "<enter>"
      ]
    }
    "astralinux-1.7" = {
      family        = "debian"
      name          = "Astra Linux 1.7 (Смоленск)"
      http_dir      = "astra"
      disk_size     = 40960
      memory        = 4096
      cpus          = 2
      ssh_username  = "secops"
      boot_command  = [
        "<wait10>",
        "/install.amd/vmlinuz auto console-keymaps-at/keymap=ru console-setup/layoutcode=ru",
        " file=http://{{ .HTTPIP }}:{{ .HTTPPort }}/astra-preseed.cfg",
        " initrd=/install.amd/initrd.gz priority=critical locale=ru_RU",
        "<enter>"
      ]
    }
    "altlinux-8" = {
      family        = "alt"
      name          = "Альт Сервер 8"
      http_dir      = "alt"
      disk_size     = 40960
      memory        = 4096
      cpus          = 2
      ssh_username  = "secops"
      boot_command  = [
        "<wait5>",
        "linux auto inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/alt-auto.cfg",
        " lang=ru_RU.UTF-8 kbd=ru",
        "<enter>"
      ]
    }
    "centos-7" = {
      family        = "centos7"
      name          = "CentOS 7"
      http_dir      = "centos"
      disk_size     = 30720
      memory        = 4096
      cpus          = 2
      ssh_username  = "secops"
      boot_command  = [
        "<wait5>",
        "linux inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/centos-ks.cfg",
        " inst.text inst.lang=en_US net.ifnames=0 biosdevname=0",
        " console=ttyS0",
        "<enter>"
      ]
    }
  }
  distro_settings = lookup(local.systems, var.distro, null)
  iso_defaults = {
    iso_url      = "file:///isos/${var.distro}.iso"
    iso_checksum = "sha256:CHANGE-ME"
  }
  iso_config = merge(local.iso_defaults, lookup(var.images, var.distro, {}))
}

locals {
  accel = "kvm"
}

source "qemu" "linux" {
  iso_url      = local.iso_config.iso_url
  iso_checksum = local.iso_config.iso_checksum
  output_directory = "${var.output_directory}/${var.distro}-${var.environment}"
  vm_name      = "${var.distro}-${var.environment}"
  accelerator  = local.accel
  disk_size    = local.distro_settings.disk_size
  format       = "qcow2"
  headless     = true
  http_directory = "${path.root}/http/${local.distro_settings.http_dir}"
  ssh_username = local.distro_settings.ssh_username
  ssh_password = var.ssh_password
  ssh_timeout  = "30m"
  shutdown_command = "sudo /sbin/shutdown -h now"
  cpus         = local.distro_settings.cpus
  memory       = local.distro_settings.memory
  qemuargs = [["-display", "none"], ["-serial", "stdio"]]
  boot_wait   = "10s"
  boot_command = local.distro_settings.boot_command
}

build {
  name    = "${var.distro}-${var.environment}"
  sources = ["source.qemu.linux"]

  provisioner "shell" {
    inline = [
      "echo '--- preparing base image for ${var.environment} ---'",
      "echo 'ensuring cloud-init directories exist'",
      "sudo mkdir -p /etc/cloud && sudo touch /etc/cloud/cloud-init.disabled",
      "sudo usermod -aG wheel ${local.distro_settings.ssh_username} || true",
      "echo 'profile ${var.environment} applied'"
    ]
  }

  provisioner "ansible" {
    playbook_file = "${path.root}/../ansible/playbooks/hardening.yml"
    extra_arguments = [
      "-e", "target_environment=${var.environment}",
      "-e", "secaudit_profile_id=${var.distro}",
      "-e", "ansible_user=${local.distro_settings.ssh_username}",
      "-e", "ansible_password=${var.ssh_password}"
    ]
    ansible_env_vars = [
      "ANSIBLE_ROLES_PATH=${path.root}/../../../hardening-scenarios/ansible/roles"
    ]
  }

  post-processor "manifest" {
    output = "${path.root}/../artifacts/${var.distro}-${var.environment}-manifest.json"
  }
}
