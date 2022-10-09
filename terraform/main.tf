terraform {
  required_providers {
    proxmox = {
      source = "telmate/proxmox"
      version = "2.7.4"
    }
  }
}

provider "proxmox" {
  pm_api_url = "https://192.168.3.1:8006/api2/json"
  pm_api_token_id = "terraform@pam!token20220405"
  pm_api_token_secret = "dbde1f14-be7b-46b2-a77a-68a002bdb9aa"
  pm_tls_insecure = true

  pm_log_enable = true
  pm_log_file = "terraform-plugin-proxmox.log"
  pm_log_levels = {
    _default = "debug"
    _capturelog = ""
  }
}


##########
## Server 00 
##########

resource "proxmox_vm_qemu" "k3-server-lafiel" {
  count = var.k3_server_count
  name = "${format("k3-server-%02s", count.index + var.k3_server00_offset)}"
  target_node = var.k3_server00_host 
  clone = var.template_name
  agent = 1
  os_type = "cloud-init"
  cores = 3
  sockets = 1
  cpu = "host"
  memory = 15872
  scsihw = "virtio-scsi-pci"
  bootdisk = "scsi0"
  disk {
    slot = 0
    size = var.k3_server_disksize 
    type = "scsi"
    storage = "local-zfs"
    iothread = 1
  }
  network {
    model = "virtio"
    bridge = "vmbr0"
  }

  lifecycle {
    ignore_changes = [
      network,
    ]
  }
  ipconfig0 = "${format("ip=192.168.2.%02s/22,gw=192.168.0.1", count.index + var.k3_server00_offset + var.k3_server_base_offset)}"
  sshkeys = <<EOF
  ${var.ssh_key_terraform}
  EOF
}


##########
## Agent 00 
##########

resource "proxmox_vm_qemu" "k3-agent-lafiel" {
  count = var.k3_agent_count
  name = "${format("k3-agent-%02s", count.index + var.k3_agent00_offset)}"
  target_node = var.k3_agent00_host
  clone = var.template_name
  agent = 1
  os_type = "cloud-init"
  cores = 3
  sockets = 1
  cpu = "host"
  memory = var.k3_agent00_mem
  scsihw = "virtio-scsi-pci"
  bootdisk = "scsi0"
  disk {
    slot = 0
    size = var.k3_agent00_disksize
    type = "scsi"
    storage = "local-zfs"
    iothread = 1
  }
  network {
    model = "virtio"
    bridge = "vmbr0"
  }

  lifecycle {
    ignore_changes = [
      network,
    ]
  }
  ipconfig0 = "${format("ip=192.168.2.%02s/22,gw=192.168.0.1", count.index + var.k3_agent00_offset + var.k3_agent_base_offset)}"
  sshkeys = <<EOF
  ${var.ssh_key_terraform}
  EOF
}



##########
## Server 01
##########

resource "proxmox_vm_qemu" "k3-server-yurika" {
  count = 0
  #count = var.k3_server_count
  name = "${format("k3-server-%02s", count.index + var.k3_server01_offset)}"
  target_node = var.k3_server01_host
  clone = var.template_name
  agent = 1
  os_type = "cloud-init"
  cores = 1
  sockets = 1
  cpu = "host"
  memory = 4096
  scsihw = "virtio-scsi-pci"
  bootdisk = "scsi0"
  disk {
    slot = 0
    size = var.k3_server_disksize 
    type = "scsi"
    storage = "local-zfs"
    iothread = 1
  }
  network {
    model = "virtio"
    bridge = "vmbr0"
  }

  lifecycle {
    ignore_changes = [
      network,
    ]
  }
  ipconfig0 = "${format("ip=192.168.2.%02s/22,gw=192.168.0.1", count.index + var.k3_server01_offset + var.k3_server_base_offset)}"
  sshkeys = <<EOF
  ${var.ssh_key_terraform}
  EOF
}

##########
## Agent 01
##########

resource "proxmox_vm_qemu" "k3-agent-yurika" {
  count = var.k3_agent_count
  name = "${format("k3-agent-%02s", count.index + var.k3_agent01_offset)}"
  target_node = var.k3_agent01_host
  clone = var.template_name
  agent = 1
  os_type = "cloud-init"
  cores = 8
  sockets = 1
  cpu = "host"
  memory = var.k3_agent01_mem
  scsihw = "virtio-scsi-pci"
  bootdisk = "scsi0"
  disk {
    slot = 0
    size = var.k3_agent01_disksize
    type = "scsi"
    storage = "local-zfs"
    iothread = 1
  }
  network {
    model = "virtio"
    bridge = "vmbr0"
  }

  lifecycle {
    ignore_changes = [
      network,
    ]
  }
  ipconfig0 = "${format("ip=192.168.2.%02s/22,gw=192.168.0.1", count.index + var.k3_agent01_offset + var.k3_agent_base_offset)}"
  sshkeys = <<EOF
  ${var.ssh_key_terraform}
  EOF
}



##########
## Server 02
##########

resource "proxmox_vm_qemu" "k3-server-melfina" {
  count = 0
  #count = var.k3_server_count
  name = "${format("k3-server-%02s", count.index + var.k3_server02_offset)}"
  target_node = var.k3_server02_host
  clone = var.template_name
  agent = 1
  os_type = "cloud-init"
  cores = 2
  sockets = 1
  cpu = "host"
  memory = 4096
  scsihw = "virtio-scsi-pci"
  bootdisk = "scsi0"
  disk {
    slot = 0
    size = var.k3_server_disksize 
    type = "scsi"
    storage = "local-zfs"
    iothread = 1
  }
  network {
    model = "virtio"
    bridge = "vmbr0"
  }

  lifecycle {
    ignore_changes = [
      network,
    ]
  }
  ipconfig0 = "${format("ip=192.168.2.%02s/22,gw=192.168.0.1", count.index + var.k3_server02_offset + var.k3_server_base_offset)}"
  sshkeys = <<EOF
  ${var.ssh_key_terraform}
  EOF
}

##########
## Agent 02
##########

resource "proxmox_vm_qemu" "k3-agent-melfina" {
  count = var.k3_agent_count
  name = "${format("k3-agent-%02s", count.index + var.k3_agent02_offset)}"
  target_node = var.k3_agent02_host
  clone = var.template_name
  agent = 1
  os_type = "cloud-init"
  cores = 4
  sockets = 1
  cpu = "host"
  memory = var.k3_agent02_mem
  scsihw = "virtio-scsi-pci"
  bootdisk = "scsi0"
  disk {
    slot = 0
    size = var.k3_agent02_disksize
    type = "scsi"
    storage = "local-zfs"
    iothread = 1
  }
  network {
    model = "virtio"
    bridge = "vmbr0"
  }

  lifecycle {
    ignore_changes = [
      network,
    ]
  }
  ipconfig0 = "${format("ip=192.168.2.%02s/22,gw=192.168.0.1", count.index + var.k3_agent02_offset + var.k3_agent_base_offset)}"
  sshkeys = <<EOF
  ${var.ssh_key_terraform}
  EOF
}



##########
## Dev Server 00 
##########

resource "proxmox_vm_qemu" "k3-dev-server-00" {
  count = 1
  name = "${format("k3-dev-server-%02s", count.index + var.k3_dev_server00_offset)}"
  target_node = var.k3_dev_server00_host 
  clone = var.template_name
  agent = 1
  os_type = "cloud-init"
  cores = var.k3_dev_server00_cores
  sockets = 1
  cpu = "host"
  memory = var.k3_dev_server00_mem
  scsihw = "virtio-scsi-pci"
  bootdisk = "scsi0"
  disk {
    slot = 0
    size = var.k3_server_disksize 
    type = "scsi"
    storage = "local-zfs"
    iothread = 1
  }
  network {
    model = "virtio"
    bridge = "vmbr0"
  }

  lifecycle {
    ignore_changes = [
      network,
    ]
  }
  ipconfig0 = "${format("ip=192.168.2.%s/22,gw=192.168.0.1", count.index + var.k3_dev_server00_offset + var.k3_dev_offset)}"
  sshkeys = <<EOF
  ${var.ssh_key_terraform}
  EOF
}


##########
## Dev Agent 00 
##########

resource "proxmox_vm_qemu" "k3-dev-agent-00" {
  count = 1
  name = "${format("k3-dev-agent-%02s", count.index + var.k3_dev_agent00_offset)}"
  target_node = var.k3_dev_agent00_host
  clone = var.template_name
  agent = 1
  os_type = "cloud-init"
  cores = var.k3_dev_agent00_cores 
  sockets = 1
  cpu = "host"
  memory = var.k3_dev_agent00_mem
  scsihw = "virtio-scsi-pci"
  bootdisk = "scsi0"
  disk {
    slot = 0
    size = var.k3_dev_agent00_disksize
    type = "scsi"
    storage = "local-zfs"
    iothread = 1
  }
  network {
    model = "virtio"
    bridge = "vmbr0"
  }

  lifecycle {
    ignore_changes = [
      network,
    ]
  }
  ipconfig0 = "${format("ip=192.168.2.%s/22,gw=192.168.0.1", count.index + var.k3_dev_offset + var.k3_dev_agent00_offset)}"
  sshkeys = <<EOF
  ${var.ssh_key_terraform}
  EOF
}


##########
## Docker Host
##########

resource "proxmox_vm_qemu" "docker" {
  count = 1
  name = "docker"
  target_node = "ifurita"
  clone = var.template_name
  agent = 1
  os_type = "cloud-init"
  cores = 4
  sockets = 1
  cpu = "host"
  memory = "2048"
  scsihw = "virtio-scsi-pci"
  bootdisk = "scsi0"
  disk {
    slot = 0
    size = "20G"
    type = "scsi"
    storage = "local-zfs"
    iothread = 1
  }
  network {
    model = "virtio"
    bridge = "vmbr0"
  }

  lifecycle {
    ignore_changes = [
      network,
    ]
  }
  ipconfig0 = "ip=192.168.3.120/22,gw=192.168.0.1"
  sshkeys = <<EOF
  ${var.ssh_key_terraform}
  EOF
}

