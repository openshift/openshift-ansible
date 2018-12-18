resource "libvirt_volume" "coreos_base" {
  name   = "${var.cluster_name}-base"
  source = "${var.image}"
}
