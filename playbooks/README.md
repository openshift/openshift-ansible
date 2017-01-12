# openshift-ansible playbooks

In summary:

- [`byo`](byo) (_Bring Your Own_ hosts) has the most actively maintained
  playbooks for installing, upgrading and performing others tasks on OpenShift
  clusters.
- [`common`](common) has a set of playbooks that are included by playbooks in
  `byo` and others.

And:

- [`adhoc`](adhoc) is a generic home for playbooks and tasks that are community
  supported and not officially maintained.
- [`aws`](aws), [`gce`](gce), [`libvirt`](libvirt) and [`openstack`](openstack)
  are related to the [`bin/cluster`](../bin) tool and its usage is deprecated.

Refer to the `README.md` file in each playbook directory for more information
about them.
