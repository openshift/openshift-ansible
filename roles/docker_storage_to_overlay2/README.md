Docker Storage to Overlay2
==========================

Changes the Docker storage driver to overlay2.

## WARNING

This makes no attempt to migrate existing containers/images.  It
momentarily stops docker.service and uses `atomic storage reset`
to wipe all local Docker storage.

## NOTE

If the existing storage configuration includes a `dm.basesize` option,
it will be replaced with an `overlay2.size` option with the same value.

The `overlay2.size` option, however, requires overlay2 storage driver
features beyond Docker 1.12.  See:

   https://github.com/moby/moby/pull/24771

   and

   https://github.com/moby/moby/pull/32977

These features have been backported to RHEL and package version checks
will be made before adding the `overlay2.size` option.

Requirements
------------

* Ansible 2.3
* RHEL 7.4 host
* `atomic` >= 1.19.1-3
* `docker` (>= 1.12.6-58 if using `overlay2.size`)
* `container-storage-setup` (>= 0.7.0 if using `overlay2.size`)

Role Variables
--------------

`docker_storage_to_overlay2_lvname` (default: `"docker-root-lv"`)

* Container storage logical volume name

`docker_storage_to_overlay2_lvsize` (default: `"100%FREE"`)

* Container storage logical volume size

`docker_storage_to_overlay2_reboot` (default: `True`)

* Reboot host after changing Docker storage to overlay2.  This will
  verify that `docker-storage-setup.service` can successfully mount
  the reconfigured logical volume during boot. 

Dependencies
------------

* `setup` (for `ansible_distribution` fact)
* `lib_utils` (for `repoquery` module)

Example Playbook
----------------

```
- hosts: nodes
  gather_facts: yes
  roles:
  - role: docker_storage_to_overlay2
```

See Also
--------

`docker_storage_driver` role

* Sets `docker_storage_driver` fact, which could be useful in writing an
  idempotent playbook around this role.

License
-------

Apache License, Version 2.0

Author Information
------------------

Matthew Barnes <mbarnes@redhat.com>
