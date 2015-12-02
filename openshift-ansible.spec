# %commit is intended to be set by tito custom builders provided
# in the .tito/lib directory. The values in this spec file will not be kept up to date.
%{!?commit:
%global commit c64d09e528ca433832c6b6e6f5c7734a9cc8ee6f
}

Name:           openshift-ansible
Version:        3.0.16
Release:        1%{?dist}
Summary:        Openshift and Atomic Enterprise Ansible
License:        ASL 2.0
URL:            https://github.com/openshift/openshift-ansible
Source0:        https://github.com/openshift/openshift-ansible/archive/%{commit}/%{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:      ansible >= 1.9.3
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
ln -sf %{_datadir}/ansible/inventory/multi_inventory.py %{buildroot}%{python_sitelib}/openshift_ansible/multi_inventory.py
ln -sf %{_datadir}/ansible/inventory/aws %{buildroot}%{python_sitelib}/openshift_ansible/aws

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
Requires:      %{name}
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
Requires:      %{name}
BuildArch:     noarch

%description filter-plugins
%{summary}.

%files filter-plugins
%{_datadir}/ansible_plugins/filter_plugins


# ----------------------------------------------------------------------------------
# openshift-ansible-lookup-plugins subpackage
# ----------------------------------------------------------------------------------
%package lookup-plugins
Summary:       Openshift and Atomic Enterprise Ansible lookup plugins
Requires:      %{name}
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

