# %commit is intended to be set by tito custom builders provided
# in the .tito/lib directory. The values in this spec file will not be kept up to date.
%{!?commit:
%global commit c64d09e528ca433832c6b6e6f5c7734a9cc8ee6f
}

Name:           openshift-ansible
Version:        3.0.44
Release:        1%{?dist}
Summary:        Openshift and Atomic Enterprise Ansible
License:        ASL 2.0
URL:            https://github.com/openshift/openshift-ansible
Source0:        https://github.com/openshift/openshift-ansible/archive/%{commit}/%{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:      ansible >= 1.9.4
Requires:      python2

%description
Openshift and Atomic Enterprise Ansible

This repo contains Ansible code and playbooks
for Openshift and Atomic Enterprise.

%prep
%setup -q

%build

# atomic-openshift-utils install
pushd utils
%{__python} setup.py build
popd

%install
# Base openshift-ansible install
mkdir -p %{buildroot}%{_datadir}/%{name}
mkdir -p %{buildroot}%{_datadir}/ansible/%{name}
mkdir -p %{buildroot}%{_datadir}/ansible_plugins

# openshift-ansible-bin install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{python_sitelib}/openshift_ansible
mkdir -p %{buildroot}/etc/bash_completion.d
mkdir -p %{buildroot}/etc/openshift_ansible
cp -p bin/{ossh,oscp,opssh,opscp,ohi} %{buildroot}%{_bindir}
cp -pP bin/openshift_ansible/* %{buildroot}%{python_sitelib}/openshift_ansible
cp -p bin/ossh_bash_completion %{buildroot}/etc/bash_completion.d
cp -p bin/openshift_ansible.conf.example %{buildroot}/etc/openshift_ansible/openshift_ansible.conf
# Fix links
rm -f %{buildroot}%{python_sitelib}/openshift_ansible/multi_inventory.py
rm -f %{buildroot}%{python_sitelib}/openshift_ansible/aws
rm -f %{buildroot}%{python_sitelib}/openshift_ansible/gce
ln -sf %{_datadir}/ansible/inventory/multi_inventory.py %{buildroot}%{python_sitelib}/openshift_ansible/multi_inventory.py
ln -sf %{_datadir}/ansible/inventory/aws %{buildroot}%{python_sitelib}/openshift_ansible/aws
ln -sf %{_datadir}/ansible/inventory/gce %{buildroot}%{python_sitelib}/openshift_ansible/gce

# openshift-ansible-docs install
# -docs are currently just %doc, no install needed

# openshift-ansible-inventory install
mkdir -p %{buildroot}/etc/ansible
mkdir -p %{buildroot}%{_datadir}/ansible/inventory
mkdir -p %{buildroot}%{_datadir}/ansible/inventory/aws
mkdir -p %{buildroot}%{_datadir}/ansible/inventory/gce
cp -p inventory/multi_inventory.py %{buildroot}%{_datadir}/ansible/inventory
cp -p inventory/multi_inventory.yaml.example %{buildroot}/etc/ansible/multi_inventory.yaml
cp -p inventory/aws/hosts/ec2.py %{buildroot}%{_datadir}/ansible/inventory/aws
cp -p inventory/gce/hosts/gce.py %{buildroot}%{_datadir}/ansible/inventory/gce

# openshift-ansible-playbooks install
cp -rp playbooks %{buildroot}%{_datadir}/ansible/%{name}/

# openshift-ansible-roles install
cp -rp roles %{buildroot}%{_datadir}/ansible/%{name}/

# openshift-ansible-filter-plugins install
cp -rp filter_plugins %{buildroot}%{_datadir}/ansible_plugins/

# openshift-ansible-lookup-plugins install
cp -rp lookup_plugins %{buildroot}%{_datadir}/ansible_plugins/

# atomic-openshift-utils install
pushd utils
%{__python} setup.py install --skip-build --root %{buildroot}
# Remove this line once the name change has happened
mv -f %{buildroot}%{_bindir}/oo-install %{buildroot}%{_bindir}/atomic-openshift-installer
mkdir -p %{buildroot}%{_datadir}/atomic-openshift-utils/
cp etc/ansible.cfg %{buildroot}%{_datadir}/atomic-openshift-utils/ansible.cfg
popd

# Base openshift-ansible files
%files
%doc LICENSE.md README*
%dir %{_datadir}/ansible/%{name}

# ----------------------------------------------------------------------------------
# openshift-ansible-bin subpackage
# ----------------------------------------------------------------------------------
%package bin
Summary:       Openshift and Atomic Enterprise Ansible Scripts for working with metadata hosts
Requires:      %{name} = %{version}
Requires:      %{name}-inventory = %{version}
Requires:      %{name}-playbooks = %{version}
BuildRequires: python2-devel
BuildArch:     noarch

%description bin
Scripts to make it nicer when working with hosts that are defined only by metadata.

%files bin
%{_bindir}/*
%exclude %{_bindir}/atomic-openshift-installer
%{python_sitelib}/openshift_ansible/
/etc/bash_completion.d/*
%config(noreplace) /etc/openshift_ansible/


# ----------------------------------------------------------------------------------
# openshift-ansible-docs subpackage
# ----------------------------------------------------------------------------------
%package docs
Summary:       Openshift and Atomic Enterprise Ansible documents
Requires:      %{name} = %{version}
BuildArch:     noarch

%description docs
%{summary}.

%files docs
%doc  docs

# ----------------------------------------------------------------------------------
# openshift-ansible-inventory subpackage
# ----------------------------------------------------------------------------------
%package inventory
Summary:       Openshift and Atomic Enterprise Ansible Inventories
Requires:      %{name} = %{version}
BuildArch:     noarch

%description inventory
Ansible Inventories used with the openshift-ansible scripts and playbooks.

%files inventory
%config(noreplace) /etc/ansible/*
%dir %{_datadir}/ansible/inventory
%{_datadir}/ansible/inventory/multi_inventory.py*

%package inventory-aws
Summary:       Openshift and Atomic Enterprise Ansible Inventories for AWS
Requires:      %{name}-inventory = %{version}
Requires:      python-boto
BuildArch:     noarch

%description inventory-aws
Ansible Inventories for AWS used with the openshift-ansible scripts and playbooks.

%files inventory-aws
%{_datadir}/ansible/inventory/aws/ec2.py*

%package inventory-gce
Summary:       Openshift and Atomic Enterprise Ansible Inventories for GCE
Requires:      %{name}-inventory = %{version}
Requires:      python-libcloud >= 0.13
BuildArch:     noarch

%description inventory-gce
Ansible Inventories for GCE used with the openshift-ansible scripts and playbooks.

%files inventory-gce
%{_datadir}/ansible/inventory/gce/gce.py*


# ----------------------------------------------------------------------------------
# openshift-ansible-playbooks subpackage
# ----------------------------------------------------------------------------------
%package playbooks
Summary:       Openshift and Atomic Enterprise Ansible Playbooks
Requires:      %{name} = %{version}
Requires:      %{name}-roles = %{version}
Requires:      %{name}-lookup-plugins = %{version}
Requires:      %{name}-filter-plugins = %{version}
BuildArch:     noarch

%description playbooks
%{summary}.

%files playbooks
%{_datadir}/ansible/%{name}/playbooks


# ----------------------------------------------------------------------------------
# openshift-ansible-roles subpackage
# ----------------------------------------------------------------------------------
%package roles
Summary:       Openshift and Atomic Enterprise Ansible roles
Requires:      %{name} = %{version}
Requires:      %{name}-lookup-plugins = %{version}
Requires:      %{name}-filter-plugins = %{version}
BuildArch:     noarch

%description roles
%{summary}.

%files roles
%{_datadir}/ansible/%{name}/roles


# ----------------------------------------------------------------------------------
# openshift-ansible-filter-plugins subpackage
# ----------------------------------------------------------------------------------
%package filter-plugins
Summary:       Openshift and Atomic Enterprise Ansible filter plugins
Requires:      %{name} = %{version}
BuildArch:     noarch
Requires:      pyOpenSSL

%description filter-plugins
%{summary}.

%files filter-plugins
%{_datadir}/ansible_plugins/filter_plugins


# ----------------------------------------------------------------------------------
# openshift-ansible-lookup-plugins subpackage
# ----------------------------------------------------------------------------------
%package lookup-plugins
Summary:       Openshift and Atomic Enterprise Ansible lookup plugins
Requires:      %{name} = %{version}
BuildArch:     noarch

%description lookup-plugins
%{summary}.

%files lookup-plugins
%{_datadir}/ansible_plugins/lookup_plugins

# ----------------------------------------------------------------------------------
# atomic-openshift-utils subpackage
# ----------------------------------------------------------------------------------

%package -n atomic-openshift-utils
Summary:       Atomic OpenShift Utilities
BuildRequires: python-setuptools
Requires:      %{name}-playbooks >= %{version}
Requires:      python-click
Requires:      python-setuptools
Requires:      PyYAML
BuildArch:     noarch

%description -n atomic-openshift-utils
Atomic OpenShift Utilities includes
 - atomic-openshift-installer
 - other utilities

%files -n atomic-openshift-utils
%{python_sitelib}/ooinstall*
%{_bindir}/atomic-openshift-installer
%{_datadir}/atomic-openshift-utils/ansible.cfg


%changelog
* Wed Feb 17 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.44-1
- create registry items/triggers under Openshift Node (jdiaz@redhat.com)
- a-o-i: Change method for counting master_lb as installed
  (smunilla@redhat.com)

* Tue Feb 16 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.43-1
- Add default to state param (rharriso@redhat.com)
- Add type to record_type param (rharriso@redhat.com)
- Add types to module params (rharriso@redhat.com)
- Adding examples to the dyn_record module (rharriso@redhat.com)
- add item to track docker-registry pings (jdiaz@redhat.com)
- Handle case where the user already had access to the scc
  (bleanhar@redhat.com)
- Refactoring the add-scc-to-user logic (bleanhar@redhat.com)
- Apply openshift_docker to nodes during scaleup. (abutcher@redhat.com)
- Change etcd deamon name for atomic-host (florian.lambert@enovance.com)

* Tue Feb 16 2016 Joel Diaz <jdiaz@redhat.com> 3.0.42-1
- Add gce softlink for openshift-ansible-bin

* Mon Feb 15 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.41-1
- Bug 1308411 - Fail to install OSE 3.0 for no add-scc-to-user command
  (bleanhar@redhat.com)
- Add openshift_docker_options to append arbitrary options to
  /etc/sysconfig/docker OPTIONS (sdodson@redhat.com)
- oo_filter: added custom fitler to return hosts group info
  (mwoodson@redhat.com)
- add gce softlink for openshift-ansible-bin RPM (jdiaz@redhat.com)
- a-o-i: Count nativeha hosts as "installed" for scaleup (smunilla@redhat.com)
- a-o-i: Add master_routingconfig_subdomain to PERSIST_SETTINGS
  (smunilla@redhat.com)
- Bug 1308412 - Fail to install containerized HA master env on RHEL7
  (bleanhar@redhat.com)
- Bug 1308314 - Failed to continue installation when pressing CTRL-C
  (bleanhar@redhat.com)
- Updating the 3.1.1 router to match the new liveness probe configuration
  (bleanhar@redhat.com)
- Don't automatically give additional permissions to all OAuth users on upgrade
  (jliggitt@redhat.com)
- Fix adhoc boostrap fedora playbook (jdetiber@redhat.com)
- Fix libvirt cluster creation (lhuard@amadeus.com)
- Add missing `type` node labels on OpenStack and libvirt (lhuard@amadeus.com)
- a-o-i: Prompts to allow minor upgrades (smunilla@redhat.com)
- conditionalize loopback config on v >= 3.2/1.2 (jdetiber@redhat.com)
- Fixes pv/pvc creation for latest builds (jdetiber@redhat.com)
- Bug 1302970 - update script does not patch router if name is different from
  default (bleanhar@redhat.com)
- Fix loopback cluster name, context name, and user (jdetiber@redhat.com)
- Changes for new Nuage RPMS (vishal.patil@nuagenetworks.net)
- Make the GCE image_name and the machine_type configurable from the CLI
  (lhuard@amadeus.com)
- Better structure the output of the list playbook (lhuard@amadeus.com)
- Fix issue when there are no infra nodes (lhuard@amadeus.com)
- Remove fluentd_master and fluentd_node roles. (abutcher@redhat.com)
- Remove etcd up checks from fluentd_master. (abutcher@redhat.com)

* Thu Feb 11 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.40-1
- Bug 1306665 - [metrics] update metrics-deployer template to use latest image
  versions (bleanhar@redhat.com)
- Add organizations attribute to github identity provider (jdetiber@redhat.com)
- use correct dict key (jdiaz@redhat.com)
- handle being passed an empty group list (jdiaz@redhat.com)
- fix default value (jdetiber@redhat.com)
- removed notscheduleable trigger, it just makes noise in its current
  incarnation (sten@redhat.com)
- trigger on two successive bad pid counts (jdiaz@redhat.com)
- added nodes not ready and nodes not schedulable triggers (sten@redhat.com)
- Enable selection of kubeproxy mode (vishal.patil@nuagenetworks.net)
- add default storage plugins to 'origin' deployment_type
  (rvanveelen@tremorvideo.com)
- added nodes not ready and nodes not schedulable triggers (sten@redhat.com)
- Don't mask master service on atomic. (abutcher@redhat.com)
- update defaults and examples w/ iscsi plugin (rvanveelen@tremorvideo.com)
- add iscsi storage_plugin dependency (rvanveelen@tremorvideo.com)
- Add gte check for 3.2, update version checks to gte (jdetiber@redhat.com)
- Specify default namespace when creating router (pat2man@gmail.com)
- add missing connection:local (jdetiber@redhat.com)
- consolidate oo_first_master post-config a bit, fix some roles that use
  openshift_facts without declaring a dependency (jdetiber@redhat.com)
- openshift_serviceaccounts updates (jdetiber@redhat.com)
- Fix infra_node deployment (jdetiber@redhat.com)
- changed registry checks to alert based on number of registries with problems
  (sten@redhat.com)
- Fix a bug with existing CNAME records (rharriso@redhat.com)
- Fix HA typo in example AEP/OSE/Origin inventories (adellape@redhat.com)
- Updated the key for app create (kwoodson@redhat.com)
- Add missing atomic- and openshift-enterprise (pep@redhat.com)
- Fix enabling iptables for latest rhel versions (jdetiber@redhat.com)
- Make pod_eviction_timeout configurable from cli (jawed.khelil@amadeus.com)

* Tue Feb 09 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.39-1
- Bug 1304150 - Can't upgrade atomic-openshift to specified version
  (bleanhar@redhat.com)
- Mask master service when using native ha (jdetiber@redhat.com)
- aoi: Safer check for master_routingconfig_subdomain (smunilla@redhat.com)
- Add a DNS server on OpenStack clusters (lhuard@amadeus.com)
- renamed /etc/openshift to /etc/origin (sten@redhat.com)
- gitignore : .tag* (atom editor tag files) (sdodson@redhat.com)
- Add an early check to ensure that node names resolve to an interface on the
  host (sdodson@redhat.com)
- Allow compression option to be set to empty for non compressed QCow images
  Support tgz and gzip compressed images (akram@free.fr)
- Replace status_changed bool (abutcher@redhat.com)
- Improve docs and consistency of setting the ssh_user (jdetiber@redhat.com)
- remove outdated comments (jdetiber@redhat.com)
- add etcd hosts for gce playbooks (jdetiber@redhat.com)
- GCE cloud provider updates (jdetiber@redhat.com)
- Remove extra nfs configuration. (abutcher@redhat.com)
- Do not apply the etcd_certificates role during node playbook.
  (abutcher@redhat.com)
- Add g_new_node_hosts to cluster_hosts. (abutcher@redhat.com)
- Updating examples to use /etc/origin/master/htpasswd (jstuever@redhat.com)
- Refactor registry storage options. (abutcher@redhat.com)
- Additional overrides for cloud provider playbooks (jdetiber@redhat.com)
- Bring first etcd server up before others. (dgoodwin@redhat.com)

* Tue Feb 02 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.38-1
- aoi: Ask for osm_default_subdomain in interactive mode (smunilla@redhat.com)
- add item to hold number of stray OVS rules found/removed (jdiaz@redhat.com)
- changed adhoc playbook to match new host monitoring container
  (mwoodson@redhat.com)
- Multi-master fixes for provider playbooks (jdetiber@redhat.com)
- zabbix: added master local api items and triggers (mwoodson@redhat.com)
- Added docs around oo_nodes_with_label (jdetiber@redhat.com)
- fix for terminate (jdetiber@redhat.com)
- Fix node tags for aws provider (jdetiber@redhat.com)
- use yaml for loading lable info instead of json (jdetiber@redhat.com)
- infra_node fixes (jdetiber@redhat.com)
- removing extraneous comments (rharriso@redhat.com)
- Remove commented lines and fix pylint check (rharriso@redhat.com)
- Cleaning up the dyn ansible module for merging (rharriso@redhat.com)
- Fix missing bool filter (sdodson@redhat.com)
- Sync platest imagestreams (sdodson@redhat.com)
- Fixing last pylint error (rharriso@redhat.com)
- Fix hostname for aws cloud provider (jdetiber@redhat.com)
- Fixing pylint errors (rharriso@redhat.com)
- Give openvswitch container some time to start (jprovazn@redhat.com)
- s3_registry no filter named 'lookup' (florian.lambert@enovance.com)
- WIP adding the lib_dyn role for the dyn_record module (rharriso@redhat.com)

* Fri Jan 29 2016 Kenny Woodson <kwoodson@redhat.com> 3.0.37-1
- Adding ip address option (kwoodson@redhat.com)
- Enable cockpit when not is_atomic. (abutcher@redhat.com)
- Explicitly restart the atomic node service after configuring it for nuage
  (vishal.patil@nuagenetworks.net)
- Fix for bug 1298 (vishal.patil@nuagenetworks.net)
- fixing logic for skipping symlinks (kwoodson@redhat.com)
- Allow to have custom bucket name and region (florian.lambert@enovance.com)
- Add inventory example for logrotate_scripts (abutcher@redhat.com)
- Minor readme cleanup for Bug 1271566 (bleanhar@redhat.com)
- fix template trigger calc (jdiaz@redhat.com)
- Configure logrotate on atomic. (abutcher@redhat.com)
- Comparing zbx_host interfaces and removing duplicate hostgroup_names
  (kwoodson@redhat.com)
- Dockerfile: Require pyOpenSSL (gscrivan@redhat.com)
- replace yum with dnf (spartacus06@gmail.com)
- Install cockpit, logrotate and fluentd unless host is atomic.
  (abutcher@redhat.com)
- zabbix: added the skydns items and triggers (mwoodson@redhat.com)
- fix pkg_version (spinolacastro@gmail.com)
- Expose data_dir (spinolacastro@gmail.com)
- Fix checking for update package availability (nikolai@prokoschenko.de)
- Fix oo_pretty_print_cluster following the renaming of `env` into `clusterid`
  (lhuard@amadeus.com)
- Ensure openssl present for etcd_ca (jdetiber@redhat.com)
- Update Docs and test for testing ansible version (jdetiber@redhat.com)
- Add Nuage support to openshift ansible (vishpat@gmail.com)
- Updating for host monitoring HA masters (kwoodson@redhat.com)
- adhoc s3 registry - add auth part in the registry config sample
  (gael.lambert@enovance.com)
- Move the `is_atomic` check from `update_repos_and_packages.yml` to
  `rhel_subscribe` (lhuard@amadeus.com)
- Increase OpenStack stack creation/deletion timeout (lhuard@amadeus.com)

* Mon Jan 25 2016 Kenny Woodson <kwoodson@redhat.com> 3.0.36-1
- Fixing awsutil to support aliases and v3 (kwoodson@redhat.com)
- Fail when master restart playbook finds no active masters rather than any
  failed masters. (abutcher@redhat.com)
- Skipping any symlinks for the yaml validation check (kwoodson@redhat.com)
- Added template for config loop. (twiest@redhat.com)
- Test validate_pcs_cluster input is basestring instead of str.
  (abutcher@redhat.com)
- Fix error when oo_masters_to_config is empty (jdetiber@redhat.com)
- Update inventory examples for console customization (spinolacastro@gmail.com)
- Expose console config for customization (spinolacastro@gmail.com)
- oso_host_monitoring: added environment as a var to the host monitoring
  systemd script (mwoodson@redhat.com)
- Check master certificates during upgrade. (abutcher@redhat.com)
- Use haproxy frontend port for os_firewall. (abutcher@redhat.com)
- Fix native master api sysconfig. (abutcher@redhat.com)
- Enable kubernetes master config of podEvictionTimeout from ansible
  (jstuever@redhat.com)
- Fix wrapper pathing for non-root user install. (abutcher@redhat.com)
- Remove camel case for bin/cluster addNodes (jdetiber@redhat.com)
- Update cluster_hosts.yml for cloud providers (jdetiber@redhat.com)
- Removing ruby scripts and replacing with python. (kwoodson@redhat.com)
- Fixed a logic bug and yaml load (kwoodson@redhat.com)
- Fixing yaml validation in python.  Inputs behave differently as does glob
  (kwoodson@redhat.com)
- oso_monitoring: add the zabbix libs (mwoodson@redhat.com)
- Removing removing scripts and moving to python. (kwoodson@redhat.com)
- add ability to disable ztriggers and disable new container dns check
  (jdiaz@redhat.com)
- Remove default disable of SDN for GCE (jdetiber@redhat.com)
- Fix hardcoded api_port in openshift_master_cluster (jdetiber@redhat.com)
- Use local address for loopback kubeconfig (jdetiber@redhat.com)
- consolidate steps and cleanup template dir (jdetiber@redhat.com)
- v3_0_to_v3_1_upgrade: Remove is_atomic check for upgrades
  (smunilla@redhat.com)
- v3_0_to_v3_1_upgrade: Copy tasks rather than including from the playbook
  (smunilla@redhat.com)
- v3_0_to_v3_1_upgrade: Install storage packages (smunilla@redhat.com)
- Controllers_port and firewall rules (spinolacastro@gmail.com)
- Fix bind address/port when isn't default (spinolacastro@gmail.com)
- Add ability to disable os_firewall (jdetiber@redhat.com)

* Mon Jan 18 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.35-1
- added the lib_timedate role (mwoodson@redhat.com)
- added chrony (mwoodson@redhat.com)
- added oso_moniotoring tools role (mwoodson@redhat.com)
- Improve pacemaker 'is-active' check. (abutcher@redhat.com)

* Mon Jan 18 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.34-1
- clean up too-many-branches / logic (jdiaz@redhat.com)
- atomic-openshift-installer: add containerized to inventory
  (smunilla@redhat.com)
- Add 'unknown' to possible output for the is-active check.
  (abutcher@redhat.com)
- Fix cluster_method conditional in master restart playbook.
  (abutcher@redhat.com)
- Use IdentityFile instead of PrivateKey (donovan.muller@gmail.com)
- atomic-openshift-installer: Remove containerized install for 3.0
  (smunilla@redhat.com)
- Host group should be OSEv3 not OSv3 (donovan.muller@gmail.com)
- Remove pause after haproxy start (abutcher@redhat.com)
- Ensure nfs-utils installed for non-atomic hosts. (abutcher@redhat.com)

* Fri Jan 15 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.33-1
- Configure nodes which are also masters prior to nodes in containerized
  install. (abutcher@redhat.com)
- Call attention to openshift_master_rolling_restart_mode variable in restart
  prompt. (abutcher@redhat.com)
- Added anchors for rules in style_guide.adoc in order to make it easier to
  reference specific rules in PRs. (twiest@redhat.com)
- Update ec2.ini (jdetiber@redhat.com)

* Thu Jan 14 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.32-1
- Uninstall remove containerized wrapper and symlinks (abutcher@redhat.com)

* Thu Jan 14 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.31-1
- Check api prior to starting node. (abutcher@redhat.com)
- added anchors (twiest@redhat.com)

* Wed Jan 13 2016 Joel Diaz <jdiaz@redhat.com> 3.0.30-1
- Add -A and detail --v3 flags

* Wed Jan 13 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.29-1
- 3.1.1 upgrade playbook (bleanhar@redhat.com)
- Updated help menu for v3 flag (kwoodson@redhat.com)
- Add wait in between api and controllers start for native ha.
  (abutcher@redhat.com)
- atomic-openshift-installer: Error handling for unicode hostnames
  (smunilla@redhat.com)
- Update api verification. (abutcher@redhat.com)
- Add a Verify API Server handler that waits for the API server to become
  available (sdodson@redhat.com)
- Add -A parameter to forward ssh agent (jdiaz@redhat.com)
- Validate pacemaker cluster members. (abutcher@redhat.com)
- Removed atomic host check (kwoodson@redhat.com)
- Add is_containerized inputs to nosetests. (abutcher@redhat.com)
- Add wait for API before starting controllers w/ native ha install.
  (abutcher@redhat.com)
- Fix for to_padded_yaml filter (jdetiber@redhat.com)
- - sqashed to one commit (llange@redhat.com)
- Switch to using hostnamectl as it works on atomic and rhel7
  (sdodson@redhat.com)
- Update rolling restart playbook for pacemaker support. Replace fail with a
  warn and prompt if running ansible from a host that will be rebooted. Re-
  organize playbooks. (abutcher@redhat.com)
- Implement simple master rolling restarts. (dgoodwin@redhat.com)
- re-enable containerize installs (sdodson@redhat.com)
- Set portal net in master playbook (jdetiber@redhat.com)
- Set the cli image to match osm_image in openshift_cli role
  (sdodson@redhat.com)
- atomic-openshift-installer: Populate new_nodes group (smunilla@redhat.com)
- Always pull docker images (sdodson@redhat.com)

* Mon Jan 11 2016 Kenny Woodson <kwoodson@redhat.com> 3.0.28-1
- added the rhe7-host-monitoring service file (mwoodson@redhat.com)
- Fixing tab completion for latest metadata changes (kwoodson@redhat.com)
- Removing some internal hostnames (bleanhar@redhat.com)
- Fixing tab completion for latest metadata changes (kwoodson@redhat.com)
- Make bin/cluster able to spawn OSE 3.1 clusters (lhuard@amadeus.com)
- oso_host_monitoring role: removed the f22 and zagg client, replaced it with
  oso-rhel7-host-monitoring container (mwoodson@redhat.com)

* Fri Jan 08 2016 Kenny Woodson <kwoodson@redhat.com> 3.0.27-1
- Update to metadata tooling. (kwoodson@redhat.com)
- Fix VM drive cleanup during terminate on libvirt (lhuard@amadeus.com)

* Fri Jan 08 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.26-1
- Bug 1296388 - fixing typo (bleanhar@redhat.com)

* Thu Jan 07 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.25-1
- Bug 1296388 - The playbook still configure ManageIQ when
  openshift_use_manageiq is false (bleanhar@redhat.com)
- Add a banner to CLI wrapper instructing users that it's only for
  bootstrapping (sdodson@redhat.com)
- Rename env into clusterid and add environment in the OpenStack VMs tags
  (lhuard@amadeus.com)
- Fix terminate.yml on OpenStack (lhuard@amadeus.com)
- Install gluster and ceph packages when containerized but not atomic
  (sdodson@redhat.com)
- Update openshift_facts config_base for Online deployments (whearn@redhat.com)
- Fix multi-word arguments & cli wrapper stdin plumbing (sdodson@redhat.com)
- Improve 3.1/1.1 upgrade check (jdetiber@redhat.com)

* Thu Jan 07 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.24-1
- Setting relative paths in the upgrade playbooks wasn't working
  (bleanhar@redhat.com)

* Wed Jan 06 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.23-1
- Move extra secret validations into openshift_facts. (abutcher@redhat.com)
- Remove not is_containerized restriction on storage plugin includes.
  (abutcher@redhat.com)
- We can't enable manageiq for installations less than OSE 3.1 or Origin 1.1
  (bleanhar@redhat.com)
- Fix RHN subscription by explicitly attaching to the right pool
  (lhuard@amadeus.com)
- openshift_facts validation (abutcher@redhat.com)
- Secrets validation. (abutcher@redhat.com)
- Clean up idempotency issues with session secrets. (abutcher@redhat.com)

* Wed Jan 06 2016 Kenny Woodson <kwoodson@redhat.com> 3.0.22-1
- playbook for restarting SDN (jdiaz@redhat.com)
- Stop haproxy and remove package during uninstall. (abutcher@redhat.com)
- Group name as per hosts.origin.example (donovan.muller@gmail.com)
- I believe the ami id changed since the initial documentation was created for
  AWS deployment (rcook@redhat.com)

* Tue Jan 05 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.21-1
- Fix osm_controller_args and osm_api_server_args settings.
  (abutcher@redhat.com)
- Fix error in byo cluster_hosts.yml (jdetiber@redhat.com)
- Cleanup and fixes for cluster_id change (jdetiber@redhat.com)
- Fix typo in etcd service status fact. (abutcher@redhat.com)
- Removing environment and env tags. (kwoodson@redhat.com)
- Add node kubelet args to inventory examples. (abutcher@redhat.com)
- Adding ManageIQ service account by default (efreiber@redhat.com)
- Fixes typo assigning docker_service_status_changed which leads to
  misinterpretation in handler. (eric.mountain@amadeus.com)
- Fix restart handlers. (abutcher@redhat.com)
- Remove lb from docker hosts. (abutcher@redhat.com)
- Install iptables, iptables-services when not is_aotmic (sdodson@redhat.com)
- Install all xpaas streams when enabled (sdodson@redhat.com)
- add the necessary URLs for logging and metrics
  (git001@users.noreply.github.com)
- Link to Tito Home Page is Broken (lloy0076@adam.com.au)
- Conditionalize for 3.1.1/1.1.1 (abutcher@redhat.com)
- Use notify for workaround controllers unit. (abutcher@redhat.com)
- change dns triggers to average (jdiaz@redhat.com)
- add item/trigger for dns tests on all currently running containers
  (jdiaz@redhat.com)
- Add jboss-fuse/application-templates/fis-image-streams.json
  (sdodson@redhat.com)
- atomic-openshift-installer: Fix broken nosetest (smunilla@redhat.com)
- Update from jboss-openshift/application-templates ose-v1.2.0-1
  (sdodson@redhat.com)
- fix logic to tolerate occasional failures (jdiaz@redhat.com)
- Clean up versions.sh (sdodson@redhat.com)
- change ovs mount to /var/run/openvswitch will not require a container restart
  if openvswitch service is restarted (jdiaz@redhat.com)
- split zagg.server.processor.errors into separate heartbeat and metrics error
  items (needed since the scripts are split now). (twiest@redhat.com)
- quick installer tests (smunilla@redhat.com)
- atomic-openshift-installer: Remove HA hint for 3.0 install
  (smunilla@redhat.com)
- Add some guards to wait for images to be pulled before moving on
  (sdodson@redhat.com)
- Install httpd-tools when not is_atomic (sdodson@redhat.com)
- Properly set use_flannel fact (sbaubeau@redhat.com)
- Fix containerized variable (sdodson@redhat.com)
- Skip yum/dnf ops when is_containerized (sdodson@redhat.com)
- Move all docker config into openshift_docker to minimize docker restarts
  (sdodson@redhat.com)
- Create nfs host group with registry volume attachment. (abutcher@redhat.com)
- Add openshift_cli role (sdodson@redhat.com)
- pull docker images only if not already present (jdetiber@redhat.com)
- fixes (jdetiber@redhat.com)
- Containerization work by @sdodson (sdodson@redhat.com)
- Initial containerization work from @ibotty (tob@butter.sh)
- Add zabbix values to track docker container DNS results (jdiaz@redhat.com)
- Fix registry modification for new deployment types. (dgoodwin@redhat.com)
- Updates to ohi to pull cache if specified.  Also require version
  (kwoodson@redhat.com)
- Zabbix: added trigger to monitor app create over the last hour
  (mwoodson@redhat.com)
- added 'Template Zagg Server' (twiest@redhat.com)
- Fixes typo when setting facts to record whether master/node has been
  restarted already, to decide whether notify handler should do so or not.
  Currently, this causes random SDN network setup failures as openshift-node
  gets restarted while the setup script is running, and the subsequent start
  fails to configure the SDN because it thinks it's already done.
  (eric.mountain@amadeus.com)
- Change controllers service type to simple. (abutcher@redhat.com)
- Updating env-host-type to host patterns (kwoodson@redhat.com)
- Add note that Fedora 23+ is acceptable deployment target for origin
  (admiller@redhat.com)
- Enforce connection: local and become: no on all localhost plays
  (jdetiber@redhat.com)
- Use join for the uncompress command. (jsteffan@fedoraproject.org)
- Update for latest CentOS-7-x86_64-GenericCloud.  - Use xz compressed image  -
  Update sha256 for new image  - Update docs to reflect new settings
  (jsteffan@fedoraproject.org)

* Thu Dec 10 2015 Thomas Wiest <twiest@redhat.com> 3.0.20-1
- Revert "Automatic commit of package [openshift-ansible] release [3.0.20-1]."
  (twiest@redhat.com)
- Automatic commit of package [openshift-ansible] release [3.0.20-1].
  (twiest@redhat.com)
- Install base package in openshift_common for version facts
  (abutcher@redhat.com)
- Make the install of openshift_examples optional (jtslear@gmail.com)
- add support for remote command actions no support for anything but custom
  scripts at this time (jdiaz@redhat.com)
- Remove yum / dnf duplication (sdodson@redhat.com)
- Remove hacluster user during uninstall. (abutcher@redhat.com)
- Simplify session secrets overrides. (abutcher@redhat.com)
- Squash pcs install into one task. (abutcher@redhat.com)
- Bump ansible requirement to 1.9.4 (sdodson@redhat.com)

* Wed Dec 09 2015 Brenton Leanhardt <bleanhar@redhat.com> 3.0.19-1
- Fix version dependent image streams (sdodson@redhat.com)
- atomic-openshift-installer: Error handling on yaml loading
  (smunilla@redhat.com)
- Betterize AWS readme (jtslear@gmail.com)

* Tue Dec 08 2015 Brenton Leanhardt <bleanhar@redhat.com> 3.0.18-1
- Pass in and use first_master_ip as dnsIP for pre 3.1 nodes.
  (abutcher@redhat.com)
- Fix delete state (jdiaz@redhat.com)
- Require pyOpenSSL (sdodson@redhat.com)
- Update sync db-templates, image-streams, and quickstart-templates
  (sdodson@redhat.com)
- Clarify the preflight port check output (sdodson@redhat.com)
- Fix missing dependency version locking (sdodson@redhat.com)

* Tue Dec 08 2015 Brenton Leanhardt <bleanhar@redhat.com> 3.0.17-1
- Improving output when gathering facts (bleanhar@redhat.com)
- Bug 1287977 - Incorrect check output from atomic-openshift-installer when
  working with preconfigured load balancer (bleanhar@redhat.com)
- Add unique AEP, OSE, and Origin BYO inventories (sdodson@redhat.com)
- bring the docker udev workaround into openshift-ansible.git
  (jdiaz@redhat.com)
- Zabbix: put in a note about trigger prototype dependency
  (mwoodson@redhat.com)
- Zabbix: added dependency for inode disk check (mwoodson@redhat.com)
- Zabbix: added dependency for disk check (mwoodson@redhat.com)
- zabbix: removed ethernet graphs (mwoodson@redhat.com)
- Zabbix: added trigger dependencies to certain master checks
  (mwoodson@redhat.com)
- ManageIQ Service Account: added role for ManageIQ service account
  (efreiber@redhat.com)
- added the pv zabbix keys (mwoodson@redhat.com)
- Refactor dns options and facts. (abutcher@redhat.com)
- Fix openshift_facts playbook for yum/dnf changes (jdetiber@redhat.com)
- Configured master count should be 1 for pacemaker ha. (abutcher@redhat.com)
- Fedora changes: (admiller@redhat.com)
- Centralize etcd/schedulability logic for each host. (dgoodwin@redhat.com)
- added upgrade playbook for online (sedgar@redhat.com)
- Improved installation summary. (dgoodwin@redhat.com)
- Fix kubernetes service ip gathering. (abutcher@redhat.com)
- added docker registry cluster check (mwoodson@redhat.com)
- Add warning for HA deployments with < 3 dedicated nodes.
  (dgoodwin@redhat.com)
- Cleanup more schedulable typos. (dgoodwin@redhat.com)
- Fix validation for BasicAuthPasswordIdentityProvider (tschan@puzzle.ch)
- Fix ec2 instance type lookups (jdetiber@redhat.com)
- remove debug logging from scc/privileged patch command (jdetiber@redhat.com)
- Set api version for oc commands (jdetiber@redhat.com)
- 3.1 upgrade - use --api-version for patch commands (jdetiber@redhat.com)
- Fix bug when warning on no dedicated nodes. (dgoodwin@redhat.com)
- Suggest dedicated nodes for an HA deployment. (dgoodwin@redhat.com)
- Error out if no load balancer specified. (dgoodwin@redhat.com)
- Adjust requirement for 3 masters for HA deployments. (dgoodwin@redhat.com)
- Fixing 'unscheduleable' typo (bleanhar@redhat.com)
- Update IMAGE_PREFIX and IMAGE_VERSION values in hawkular template
  (nakayamakenjiro@gmail.com)
- Improved output when re-running after editing config. (dgoodwin@redhat.com)
- Print a system summary after adding each. (dgoodwin@redhat.com)
- Text improvements for host specification. (dgoodwin@redhat.com)
- Assert etcd section written for HA installs. (dgoodwin@redhat.com)
- Breakout a test fixture to reduce module size. (dgoodwin@redhat.com)
- Pylint touchups. (dgoodwin@redhat.com)
- Trim assertions in HA testing. (dgoodwin@redhat.com)
- Test unattended HA quick install. (dgoodwin@redhat.com)
- Don't prompt to continue during unattended installs. (dgoodwin@redhat.com)
- Block re-use of master/node as load balancer in attended install.
  (dgoodwin@redhat.com)
- Add -q flag to remove unwantend output (such as mirror and cache information)
  (urs.breu@ergon.ch)
- Uninstall: only restart docker on node hosts. (abutcher@redhat.com)
- Explicitly set schedulable when masters == nodes. (dgoodwin@redhat.com)
- Use admin.kubeconfig for get svc ip. (abutcher@redhat.com)
- Point enterprise metrics at registry.access.redhat.com/openshift3/metrics-
  (sdodson@redhat.com)
- Make sure that OpenSSL is installed before use (fsimonce@redhat.com)
- fixes for installer wrapper scaleup (jdetiber@redhat.com)
- addtl aws fixes (jdetiber@redhat.com)
- Fix failure when seboolean not present (jdetiber@redhat.com)
- fix addNodes.yml (jdetiber@redhat.com)
- more aws support for scaleup (jdetiber@redhat.com)
- start of aws scaleup (jdetiber@redhat.com)
- Improve scaleup playbook (jdetiber@redhat.com)
- Update openshift_repos to refresh package cache on changes
  (jdetiber@redhat.com)
- Add etcd nodes management in OpenStack (lhuard@amadeus.com)

* Tue Nov 24 2015 Brenton Leanhardt <bleanhar@redhat.com> 3.0.16-1
- Silencing pylint branch errors for now for the atomic-openshift-installer
  harness (bleanhar@redhat.com)
- Properly setting scheduleability for HA Master scenarios
  (bleanhar@redhat.com)
- added graphs (mwoodson@redhat.com)
- Rework setting of hostname (jdetiber@redhat.com)
- Fixed a bug in the actions.  It now supports changing opconditions
  (kwoodson@redhat.com)
- Conditionally set the nodeIP (jdetiber@redhat.com)
- Bug 1284991 - "atomic-openshift-installer uninstall" error when configuration
  file is missing. (bleanhar@redhat.com)
- Avoid printing the master and node totals in the add-a-node scenario
  (bleanhar@redhat.com)
- Fixing tests for quick_ha (bleanhar@redhat.com)
- Removing a debug line (bleanhar@redhat.com)
- atomic-openshift-installer: Fix lint issue (smunilla@redhat.com)
- Handling preconfigured load balancers (bleanhar@redhat.com)
- atomic-openshift-installer: Rename ha_proxy (smunilla@redhat.com)
- atomic-openshift-installer: Reverse version and host collection
  (smunilla@redhat.com)
- cli_installer_tests: Add test for unattended quick HA (smunilla@redhat.com)
- Breakup inventory writing (smunilla@redhat.com)
- Enforce 1 or 3 masters (smunilla@redhat.com)
- Add interactive test (smunilla@redhat.com)
- atomic-openshift-installer: HA for quick installer (smunilla@redhat.com)
- Adding zbx_graph support (kwoodson@redhat.com)
- Modified step params to be in order when passed as a list
  (kwoodson@redhat.com)
- Add serviceAccountConfig.masterCA during 3.1 upgrade (jdetiber@redhat.com)
- Use the identity_providers from openshift_facts instead of always using the
  inventory variable (jdetiber@redhat.com)
- Refactor master identity provider configuration (jdetiber@redhat.com)

* Fri Nov 20 2015 Kenny Woodson <kwoodson@redhat.com> 3.0.15-1
- Fixing clone group functionality.  Also separating extra_vars from
  extra_groups (kwoodson@redhat.com)
- Check the end result on bad config file (smunilla@redhat.com)
- Add some tests for a bad config (smunilla@redhat.com)
- atomic-openshift-installer: connect_to error handling (smunilla@redhat.com)
- atomic-openshift-installer: pylint fixes (smunilla@redhat.com)
- Replace map with oo_collect to support python-jinja2 <2.7
  (abutcher@redhat.com)
- Making the uninstall playbook more flexible (bleanhar@redhat.com)
- Install version dependent image streams for v1.0 and v1.1
  (sdodson@redhat.com)
- Do not update the hostname (jdetiber@redhat.com)
- Pylint fix for long line in cli docstring. (dgoodwin@redhat.com)
- Default to installing OSE 3.1 instead of 3.0. (dgoodwin@redhat.com)
- Fix tests on systems with openshift-ansible rpms installed.
  (dgoodwin@redhat.com)

* Thu Nov 19 2015 Brenton Leanhardt <bleanhar@redhat.com> 3.0.14-1
- added metric items to zabbix for openshift online (mwoodson@redhat.com)
- Updating usergroups to accept users (kwoodson@redhat.com)
- Differentiate machine types on GCE (master and nodes)
  (romain.dossin@amadeus.com)
- Uninstall - Remove systemd wants file for node (jdetiber@redhat.com)
- ec2 - force !requiretty for ssh_user (jdetiber@redhat.com)
- small tweaks for adding docker volume for aws master hosts
  (jdetiber@redhat.com)
- Created role to deploy ops host monitoring (jdiaz@redhat.com)
- Update certificate paths when 'names' key is provided. (abutcher@redhat.com)
- add a volume on master host, in AWS provisioning (chengcheng.mu@amadeus.com)
- First attempt at adding web scenarios (kwoodson@redhat.com)
- Use field numbers for all formats in bin/cluster for python 2.6
  (abutcher@redhat.com)
- atomic-openshift-installer: Correct single master case (smunilla@redhat.com)
- added copr-openshift-ansible releaser, removed old rel-eng stuff.
  (twiest@redhat.com)
- changed counter -> count (mwoodson@redhat.com)
- Updating zbx_item classes to support data types for bool.
  (kwoodson@redhat.com)
- Fix ec2 instance type override (jdetiber@redhat.com)
- updated my check to support the boolean data type (mwoodson@redhat.com)
- Add additive_facts_to_overwrite instead of overwriting all additive_facts
  (abutcher@redhat.com)
- added healthz check and more pod count checks (mwoodson@redhat.com)
- updating to the latest ec2.py (and re-patching with our changes).
  (twiest@redhat.com)
- atomic-openshift-installer: Temporarily restrict to single master
  (smunilla@redhat.com)
- openshift-ansible: Correct variable (smunilla@redhat.com)
- Refactor named certificates. (abutcher@redhat.com)
- atomic-openshift-utils: Version lock playbooks (smunilla@redhat.com)
- Add the native ha services and configs to uninstall (jdetiber@redhat.com)
- Bug 1282336 - Add additional seboolean for gluster (jdetiber@redhat.com)
- Raise lifetime to 2 weeks for dynamic AWS items (jdiaz@redhat.com)
- bin/cluster fix python 2.6 issue (jdetiber@redhat.com)
- cluster list: break host types by subtype (lhuard@amadeus.com)
- README_AWS: Add needed dependency (c.witt.1900@gmail.com)
- Fix invalid sudo command test (takayoshi@gmail.com)
- Docs: Fedora: Add missing dependencies and update to dnf. (public@omeid.me)
- Gate upgrade steps for 3.0 to 3.1 upgrade (jdetiber@redhat.com)
- added the tito and copr_cli roles (twiest@redhat.com)
- pylint openshift_facts (jdetiber@redhat.com)
- Update etcd default facts setting (jdetiber@redhat.com)
- Update master facts prior to upgrading incase facts are missing.
  (abutcher@redhat.com)
- pre-upgrade-check: differentiates between port and targetPort in output
  (smilner@redhat.com)
- Better structure the output of the list playbook (lhuard@amadeus.com)
- Add the sub-host-type tag to the libvirt VMs (lhuard@amadeus.com)
- atomic-openshift-installer: Update nopwd sudo test (smunilla@redhat.com)
- Fix pylint import errors for utils/test/. (dgoodwin@redhat.com)
- atomic-openshift-installer: Update prompts and help messages
  (smunilla@redhat.com)
- Dependencies need to be added when a create occurs on SLA object.
  (kwoodson@redhat.com)
- Test additions for cli_installer:get_hosts_to_install_on
  (bleanhar@redhat.com)
- adding itservice (kwoodson@redhat.com)
- remove netaddr dependency (tob@butter.sh)
- Add pyOpenSSL to dependencies for Fedora. (public@omeid.me)
- Vagrant RHEL registration cleanup (pep@redhat.com)
- RH subscription: optional satellite and pkg update (pep@redhat.com)

* Tue Nov 17 2015 Brenton Leanhardt <bleanhar@redhat.com> 3.0.13-1
- The aep3 images changed locations. (bleanhar@redhat.com)
- atomic-openshift-installer: Correct single master case (smunilla@redhat.com)
- atomic-openshift-installer: Temporarily restrict to single master
  (smunilla@redhat.com)

* Wed Nov 11 2015 Brenton Leanhardt <bleanhar@redhat.com> 3.0.12-1
- Sync with the latest image streams (sdodson@redhat.com)

* Wed Nov 11 2015 Brenton Leanhardt <bleanhar@redhat.com> 3.0.11-1
- Migrate xpaas content from pre v1.1.0 (sdodson@redhat.com)
- Import latest xpaas templates and image streams (sdodson@redhat.com)

* Wed Nov 11 2015 Brenton Leanhardt <bleanhar@redhat.com> 3.0.10-1
- Fix update error for templates that didn't previously exist
  (jdetiber@redhat.com)
- General cleanup of v3_0_to_v3_1/upgrade.yml (jdetiber@redhat.com)
- Add zabbix pieces to hold AWS S3 bucket stats (jdiaz@redhat.com)
- add ansible dep to vagrant doc (jdetiber@redhat.com)
- oo_filter: don't fail when attribute is not defined (tob@butter.sh)

* Wed Nov 11 2015 Brenton Leanhardt <bleanhar@redhat.com> 3.0.9-1
- Refactor upgrade playbook(s) (jdetiber@redhat.com)

* Tue Nov 10 2015 Scott Dodson <sdodson@redhat.com> 3.0.8-1
- Add origin-clients to uninstall playbook. (abutcher@redhat.com)
- examples: include logging and metrics infrastructure (lmeyer@redhat.com)
- Add separate step to enable services during upgrade. (dgoodwin@redhat.com)
- Update tests now that cli is not asking for rpm/container install
  (smunilla@redhat.com)
- atomic-openshift-installer: Remove question for container install
  (smunilla@redhat.com)
- Remove references to multi_ec2.py (jdetiber@redhat.com)
- 1279746: Fix leftover disabled features line in config template.
  (dgoodwin@redhat.com)
- 1279734: Ensure services are enabled after upgrade. (dgoodwin@redhat.com)
- Fix missing etcd_data_dir bug. (dgoodwin@redhat.com)
- Package the default ansible.cfg with atomic-openshift-utils.
  (dgoodwin@redhat.com)
- Add ldap auth identity provider to example inventory. (abutcher@redhat.com)
- Read etcd data dir from appropriate config file. (dgoodwin@redhat.com)
- atomic-openshift-installer: Generate inventory off hosts_to_run_on
  (smunilla@redhat.com)
- Various fixes related to connect_to (bleanhar@redhat.com)
- Remove upgrade playbook restriction on 3.0.2. (dgoodwin@redhat.com)
- Conditionals for flannel etcd client certs. (abutcher@redhat.com)
- New `iptablesSyncPeriod` field in node configuration (abutcher@redhat.com)
- Fix indentation on when (jdetiber@redhat.com)
- Bug 1278863 - Error using openshift_pkg_version (jdetiber@redhat.com)
- more cleanup of names (mwoodson@redhat.com)
- Missing conditionals for api/controller sysconfig. (abutcher@redhat.com)
- Updating the atomic-openshift-isntaller local connection logic for the
  connect_to addition. (bleanhar@redhat.com)
- cleaned up network checks (mwoodson@redhat.com)
- Minor upgrade improvements. (dgoodwin@redhat.com)
- Wait for cluster to recover after pcs resource restart. (abutcher@redhat.com)
- Bug 1278245 - Failed to add node to existing env using atomic-openshift-
  installer (bleanhar@redhat.com)
- remove debug statement (jdetiber@redhat.com)
- Fix removal of kubernetesMasterConfig.apiLevels (jdetiber@redhat.com)
- atomic-openshift-installer: Better specification of ansible connection point
  (smunilla@redhat.com)
- Fix issues related to upgrade packages being unavailable
  (jdetiber@redhat.com)
- added network checks.  also updated item prototype code to support more
  (mwoodson@redhat.com)
- Fix data_dir for 3.0 deployments (jdetiber@redhat.com)
- Fix apiLevels modifications (jdetiber@redhat.com)
- Fix creation of origin symlink when dir already exists. (dgoodwin@redhat.com)
- apiLevel changes (jdetiber@redhat.com)
- Write new config to disk after successful upgrade. (dgoodwin@redhat.com)
- Fix pylint errors with getting hosts to run on. (dgoodwin@redhat.com)
- Remove v1beta3 by default for kube_nfs_volumes (jdetiber@redhat.com)
- Add pre-upgrade script to be run on first master. (dgoodwin@redhat.com)
- Start to handle pacemaker ha during upgrade (abutcher@redhat.com)
- Fix lb group related errors (jdetiber@redhat.com)
- Fix file check conditional. (abutcher@redhat.com)
- Don't check for certs in data_dir just raise when they can't be found. Fix
  typo. (abutcher@redhat.com)
- exclude atomic-openshift-installer from bin subpackage (tdawson@redhat.com)
- add master_hostnames definition for upgrade (jdetiber@redhat.com)
- Additional upgrade enhancements (jdetiber@redhat.com)
- Handle backups for separate etcd hosts if necessary. (dgoodwin@redhat.com)
- Further upgrade improvements (jdetiber@redhat.com)
- Upgrade improvements (dgoodwin@redhat.com)
- Bug 1278243 - Confusing prompt from atomic-openshift-installer
  (bleanhar@redhat.com)
- Bug 1278244 - Previously there was no way to add a node in unattended mode
  (bleanhar@redhat.com)
- Revert to defaults (abutcher@redhat.com)
- Bug 1278244 - Incorrect node information gathered by atomic-openshift-
  installer (bleanhar@redhat.com)
- atomic-openshift-installer's unattended mode wasn't work with --force for all
  cases (bleanhar@redhat.com)
- Making it easier to use pre-release content (bleanhar@redhat.com)
- The uninstall playbook needs to remove /run/openshift-sdn
  (bleanhar@redhat.com)
- Various HA changes for pacemaker and native methods. (abutcher@redhat.com)
- Bug 1274201 - Fixing non-root installations if using a local connection
  (bleanhar@redhat.com)
- Bug 1274201 - Fixing sudo non-interactive test (bleanhar@redhat.com)
- Bug 1277592 - SDN MTU has hardcoded default (jdetiber@redhat.com)
- Atomic Enterprise/OpenShift Enterprise merge update (jdetiber@redhat.com)
- fix dueling controllers - without controllerLeaseTTL set in config, multiple
  controllers will attempt to start (jdetiber@redhat.com)
- default to source persistence for haproxy (jdetiber@redhat.com)
- hardcode openshift binaries for now (jdetiber@redhat.com)
- more tweaks (jdetiber@redhat.com)
- more tweaks (jdetiber@redhat.com)
- additional ha related updates (jdetiber@redhat.com)
- additional native ha changes (abutcher@redhat.com)
- Start of true master ha (jdetiber@redhat.com)
- Atomic Enterprise related changes. (avagarwa@redhat.com)
- Remove pacemaker bits. (abutcher@redhat.com)
- Override hosts deployment_type fact for version we're upgrading to.
  (dgoodwin@redhat.com)
- Pylint fixes for config upgrade module. (dgoodwin@redhat.com)
- Disable proxy cert config upgrade until certs being generated.
  (dgoodwin@redhat.com)
- remove debug line (florian.lambert@enovance.com)
- [roles/openshift_master_certificates/tasks/main.yml] Fix variable
  openshift.master.all_hostnames to openshift.common.all_hostnames
  (florian.lambert@enovance.com)
- Fix bug with not upgrading openshift-master to atomic-openshift-master.
  (dgoodwin@redhat.com)
- Adding aws and gce packages to ansible-inventory (kwoodson@redhat.com)
- Fix subpackage dependencies (jdetiber@redhat.com)
- Refactor common group evaluation to avoid duplication (jdetiber@redhat.com)
- common/openshift-cluster: Scaleup playbook (smunilla@redhat.com)
- Fix bug from module rename. (dgoodwin@redhat.com)
- Fix bug with default ansible playbook dir. (dgoodwin@redhat.com)
- Use the base package upgrade version so we can check things earlier.
  (dgoodwin@redhat.com)
- Skip fail if enterprise deployment type depending on version.
  (dgoodwin@redhat.com)
- Add debug output for location of etcd backup. (dgoodwin@redhat.com)
- Filter internal hostnames from the list of parsed names.
  (abutcher@redhat.com)
- Move config upgrade to correct place, fix node facts. (dgoodwin@redhat.com)
- Add custom certificates to serving info in master configuration.
  (abutcher@redhat.com)
- Add in proxyClientInfo if missing during config upgrade.
  (dgoodwin@redhat.com)
- Implement master-config.yaml upgrade for v1beta3 apiLevel removal.
  (dgoodwin@redhat.com)
- Fix installer upgrade bug following pylint fix. (dgoodwin@redhat.com)
- Document the new version field for installer config. (dgoodwin@redhat.com)
- Remove my username from some test data. (dgoodwin@redhat.com)
- Add a simple version for the installer config file. (dgoodwin@redhat.com)
- Pylint fix. (dgoodwin@redhat.com)
- Fix issue with master.proxy-client.{crt,key} and omit. (abutcher@redhat.com)
- initial module framework (jdetiber@redhat.com)
- Better info prior to initiating upgrade. (dgoodwin@redhat.com)
- Fix etcd backup bug with not-yet-created /var/lib/origin symlink
  (dgoodwin@redhat.com)
- Print info after upgrade completes. (dgoodwin@redhat.com)
- Automatically upgrade legacy config files. (dgoodwin@redhat.com)
- Remove devel fail and let upgrade proceed. (dgoodwin@redhat.com)
- Add utils subpackage missing dep on openshift-ansible-roles.
  (dgoodwin@redhat.com)
- Generate timestamped etcd backups. (dgoodwin@redhat.com)
- Add etcd_data_dir fact. (dgoodwin@redhat.com)
- Functional disk space checking for etcd backup. (dgoodwin@redhat.com)
- First cut at checking available disk space for etcd backup.
  (dgoodwin@redhat.com)
- Block upgrade if targetting enterprise deployment type. (dgoodwin@redhat.com)
- Change flannel registration default values (sbaubeau@redhat.com)
- Remove empty notify section (sbaubeau@redhat.com)
- Check etcd certs exist for flannel when its support is enabled
  (sbaubeau@redhat.com)
- Fix when neither use_openshift_sdn nor use_flannel are specified
  (sbaubeau@redhat.com)
- Generate etcd certificats for flannel when is not embedded
  (sbaubeau@redhat.com)
- Add missing 2nd true parameters to default Jinja filter (sbaubeau@redhat.com)
- Use 'command' module instead of 'shell' (sbaubeau@redhat.com)
- Add flannel modules documentation (sbaubeau@redhat.com)
- Only remove IPv4 address from docker bridge (sbaubeau@redhat.com)
- Remove multiple use_flannel fact definition (sbaubeau@redhat.com)
- Ensure openshift-sdn and flannel can't be used at the same time
  (sbaubeau@redhat.com)
- Add flannel support (sbaubeau@redhat.com)

* Wed Nov 04 2015 Kenny Woodson <kwoodson@redhat.com> 3.0.7-1
- added the %%util in zabbix (mwoodson@redhat.com)
- atomic-openshift-installer: Correct default playbook directory
  (smunilla@redhat.com)
- Support for gce (kwoodson@redhat.com)
- fixed a dumb naming mistake (mwoodson@redhat.com)
- added disk tps checks to zabbix (mwoodson@redhat.com)
- atomic-openshift-installer: Correct inaccurate prompt (smunilla@redhat.com)
- atomic-openshift-installer: Add default openshift-ansible-playbook
  (smunilla@redhat.com)
- ooinstall: Add check for nopwd sudo (smunilla@redhat.com)
- ooinstall: Update local install check (smunilla@redhat.com)
- oo-install: Support running on the host to be deployed (smunilla@redhat.com)
- Moving to Openshift Etcd application (mmahut@redhat.com)
- Add all the possible servicenames to openshift_all_hostnames for masters
  (sdodson@redhat.com)
- Adding openshift.node.etcd items (mmahut@redhat.com)
- Fix etcd cert generation when etcd_interface is defined (jdetiber@redhat.com)
- get zabbix ready to start tracking status of pcp (jdiaz@redhat.com)
- split inventory into subpackages (tdawson@redhat.com)
- changed the cpu alert to only alert if cpu idle more than 5x. Change alert to
  warning (mwoodson@redhat.com)
- Rename install_transactions module to openshift_ansible.
  (dgoodwin@redhat.com)
- atomic-openshift-installer: Text improvements (smunilla@redhat.com)
- Add utils subpackage missing dep on openshift-ansible-roles.
  (dgoodwin@redhat.com)
- Disable requiretty for only the openshift user (error@ioerror.us)
- Don't require tty to run sudo (error@ioerror.us)
- Attempt to remove the various interfaces left over from an install
  (bleanhar@redhat.com)
- Pulling latest gce.py module from ansible (kwoodson@redhat.com)
- Disable OpenShift features if installing Atomic Enterprise
  (jdetiber@redhat.com)
- Use default playbooks if available. (dgoodwin@redhat.com)
- Add uninstall subcommand. (dgoodwin@redhat.com)
- Add subcommands to CLI. (dgoodwin@redhat.com)
- Remove images options in oadm command (nakayamakenjiro@gmail.com)

* Fri Oct 30 2015 Kenny Woodson <kwoodson@redhat.com> 3.0.6-1
- Adding python-boto and python-libcloud to openshift-ansible-inventory
  dependency (kwoodson@redhat.com)
- Use more specific enterprise version for version_greater_than_3_1_or_1_1.
  (abutcher@redhat.com)
- Conditionalizing the support for the v1beta3 api (bleanhar@redhat.com)

* Thu Oct 29 2015 Kenny Woodson <kwoodson@redhat.com> 3.0.5-1
- Updating multi_ec2 to support extra_vars and extra_groups
  (kwoodson@redhat.com)
- Removing the template and doing to_nice_yaml instead (kwoodson@redhat.com)
- README_AEP.md: update instructions for creating router and registry
  (jlebon@redhat.com)
- README_AEP: Various fixes (walters@verbum.org)
- Fixing for extra_vars rename. (kwoodson@redhat.com)
- make storage_plugin_deps conditional on deployment_type (jdetiber@redhat.com)
- remove debugging pauses (jdetiber@redhat.com)
- make storage plugin dependency installation more flexible
  (jdetiber@redhat.com)
- Install storage plugin dependencies (jdetiber@redhat.com)

* Wed Oct 28 2015 Kenny Woodson <kwoodson@redhat.com> 3.0.4-1
- Removing spec files. (kwoodson@redhat.com)
- Updated example (kwoodson@redhat.com)
- Automatic commit of package [openshift-ansible-inventory] release [0.0.11-1].
  (kwoodson@redhat.com)
- Automatic commit of package [openshift-ansible-bin] release [0.0.21-1].
  (kwoodson@redhat.com)
- Automatic commit of package [openshift-ansible-inventory] release [0.0.10-1].
  (kwoodson@redhat.com)
- Automatic commit of package [openshift-ansible-bin] release [0.0.20-1].
  (kwoodson@redhat.com)
- Adding tito releasers configuration (bleanhar@redhat.com)
- Bug fixes for the uninstall playbook (bleanhar@redhat.com)
- Adding clone vars and groups. Renamed hostvars to extra_vars.
  (kwoodson@redhat.com)
- Start tracking docker info execution time (jdiaz@redhat.com)
- The uninstall playbook should remove the kubeconfig for non-root installs
  (bleanhar@redhat.com)
- Adding uninstall support for Atomic Host (bleanhar@redhat.com)
- add examples for SDN configuration (jdetiber@redhat.com)

* Tue Oct 27 2015 Troy Dawson <tdawson@redhat.com> 3.0.3-1
- Pylint fixes and ignores for incoming oo-install code. (dgoodwin@redhat.com)
- Pylint fixes (abutcher@redhat.com)
- Adding zabbix type and fixing zabbix agent vars (kwoodson@redhat.com)
- Add atomic-openshift-utils add atomic-openshift-utils to openshift-
  ansible.spec file (tdawson@redhat.com)
- Fix quotes (spinolacastro@gmail.com)
- Use standard library for version comparison. (abutcher@redhat.com)
- added docker info to the end of docker loop to direct lvm playbook.
  (twiest@redhat.com)
- Add missing quotes (spinolacastro@gmail.com)
- Adding Docker Log Options capabilities (epo@jemba.net)
- Move version greater_than_fact into openshift_facts (abutcher@redhat.com)
- Don't include proxy client cert when <3.1 or <1.1 (abutcher@redhat.com)
- Add proxy client certs to master config. (abutcher@redhat.com)
- Update imagestreams and quickstarts from origin (sdodson@redhat.com)
- Get default values from openshift_facts (spinolacastro@gmail.com)
- Cleanup (spinolacastro@gmail.com)
- Add missing inventory example (spinolacastro@gmail.com)
- Custom Project Config (spinolacastro@gmail.com)

* Mon Oct 19 2015 Troy Dawson <tdawson@redhat.com> 3.0.2-1
- Initial Package

