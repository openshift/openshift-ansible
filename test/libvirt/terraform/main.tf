provider "libvirt" {
  uri = "${var.libvirt_uri}"
}

module "volume" {
  source = "./volume"

  cluster_name = "${var.cluster_name}"
  image        = "${var.os_image}"
}

module "bootstrap" {
  source = "./bootstrap"

  addresses      = ["${var.libvirt_bootstrap_ip}"]
  base_volume_id = "${module.volume.coreos_base_volume_id}"
  cluster_name   = "${var.cluster_name}"
  network_id     = "${libvirt_network.net.id}"
  ssh_key        = "${var.ssh_key}"
}

resource "libvirt_volume" "master" {
  count          = "${var.master_count}"
  name           = "${var.cluster_name}-master-${count.index}"
  base_volume_id = "${module.volume.coreos_base_volume_id}"
}

resource "libvirt_volume" "worker" {
  count          = "${var.worker_count}"
  name           = "${var.cluster_name}-worker-${count.index}"
  base_volume_id = "${module.volume.coreos_base_volume_id}"
}

resource "libvirt_network" "net" {
  name = "${var.cluster_name}"

  mode   = "nat"
  bridge = "${var.libvirt_network_if}"

  domain = "${var.base_domain}"

  addresses = [
    "${var.libvirt_ip_range}",
  ]

  dns = [{
    local_only = true

    srvs = ["${flatten(list(
      data.libvirt_network_dns_srv_template.etcd_cluster.*.rendered,
    ))}"]

    hosts = ["${flatten(list(
      data.libvirt_network_dns_host_template.bootstrap.*.rendered,
      data.libvirt_network_dns_host_template.masters.*.rendered,
      data.libvirt_network_dns_host_template.etcds.*.rendered,
    ))}"]
  }]

  autostart = true
}

data "template_file" "user_data" {
  template = "${file("${path.module}/user-data.tpl")}"
  vars {
    ssh_authorized_keys = "${var.ssh_key}"
  }
}

resource "libvirt_cloudinit_disk" "commoninit" {
  name           = "${var.cluster_name}-master-init.iso"
  user_data      = "${data.template_file.user_data.rendered}"
}

resource "libvirt_domain" "master" {
  count = "${var.master_count}"

  name = "${var.cluster_name}-master-${count.index}"

  memory = "${var.libvirt_master_memory}"
  vcpu   = "${var.libvirt_master_vcpu}"

  cloudinit = "${libvirt_cloudinit_disk.commoninit.id}"
  disk {
    volume_id = "${element(libvirt_volume.master.*.id, count.index)}"
  }

  console {
    type        = "pty"
    target_port = 0
  }

  network_interface {
    network_id = "${libvirt_network.net.id}"
    hostname   = "${var.cluster_name}-master-${count.index}"
    addresses  = ["${var.libvirt_master_ips[count.index]}"]
  }
}

resource "libvirt_domain" "worker" {
  count = "${var.worker_count}"

  name = "${var.cluster_name}-worker-${count.index}"

  memory = "${var.libvirt_worker_memory}"
  vcpu   = "${var.libvirt_worker_vcpu}"

  cloudinit = "${libvirt_cloudinit_disk.commoninit.id}"
  disk {
    volume_id = "${element(libvirt_volume.worker.*.id, count.index)}"
  }

  console {
    type        = "pty"
    target_port = 0
  }

  network_interface {
    network_id = "${libvirt_network.net.id}"
    hostname   = "${var.cluster_name}-worker-${count.index}"
    addresses  = ["${var.libvirt_worker_ips[count.index]}"]
  }
}

data "libvirt_network_dns_host_template" "bootstrap" {
  count    = "${var.bootstrap_dns ? 1 : 0}"
  ip       = "${var.libvirt_bootstrap_ip}"
  hostname = "${var.cluster_name}-api"
}

data "libvirt_network_dns_host_template" "masters" {
  count    = "${var.master_count}"
  ip       = "${var.libvirt_master_ips[count.index]}"
  hostname = "${var.cluster_name}-api"
}

data "libvirt_network_dns_host_template" "etcds" {
  count    = "${var.master_count}"
  ip       = "${var.libvirt_master_ips[count.index]}"
  hostname = "${var.cluster_name}-etcd-${count.index}"
}

data "libvirt_network_dns_srv_template" "etcd_cluster" {
  count    = "${var.master_count}"
  service  = "etcd-server-ssl"
  protocol = "tcp"
  domain   = "${var.cluster_name}.${var.base_domain}"
  port     = 2380
  weight   = 10
  target   = "${var.cluster_name}-etcd-${count.index}.${var.base_domain}"
}
