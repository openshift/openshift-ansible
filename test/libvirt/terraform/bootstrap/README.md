# Bootstrap Module

This [Terraform][] [module][] manages [libvirt][] resources only needed during cluster bootstrapping.
It uses [implicit provider inheritance][implicit-provider-inheritance] to access the [libvirt provider][libvirt-provider].

## Example

Set up a `main.tf` with:

```hcl
provider "libvirt" {
  uri = "qemu:///system"
}

resource "libvirt_network" "example" {
  name   = "example"
  mode   = "none"
  domain = "example.com"
  addresses = ["192.168.0.0/24"]
}

resource "libvirt_volume" "example" {
  name   = "example"
  source = "file:///path/to/example.qcow2"
}

module "bootstrap" {
  source = "github.com/openshift/installer//data/data/libvirt/bootstrap"

  addresses      = ["192.168.0.1"]
  base_volume_id = "${libvirt_volume.example.id}"
  cluster_name   = "my-cluster"
  ignition       = "{\"ignition\": {\"version\": \"2.2.0\"}}",
  network_id     = "${libvirt_network.example.id}"
}
```

Then run:

```console
$ terraform init
$ terraform plan
```

[libvirt]: https://libvirt.org/
[libvirt-provider]: https://github.com/dmacvicar/terraform-provider-libvirt
[implicit-provider-inheritance]: https://www.terraform.io/docs/modules/usage.html#implicit-provider-inheritance
[module]: https://www.terraform.io/docs/modules/
[Terraform]: https://www.terraform.io/
