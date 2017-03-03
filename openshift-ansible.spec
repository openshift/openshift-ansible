# %commit is intended to be set by tito custom builders provided
# in the .tito/lib directory. The values in this spec file will not be kept up to date.
%{!?commit:
%global commit c64d09e528ca433832c6b6e6f5c7734a9cc8ee6f
}
# This is inserted to prevent RPM from requiring "/usr/bin/ansible-playbook"
# The ansible-playbook requirement will be ansibled by the explicit
#  "Requires: ansible" directive
%global __requires_exclude ^/usr/bin/ansible-playbook$

Name:           openshift-ansible
Version:        3.5.3
Release:        1%{?dist}
Summary:        Openshift and Atomic Enterprise Ansible
License:        ASL 2.0
URL:            https://github.com/openshift/openshift-ansible
Source0:        https://github.com/openshift/openshift-ansible/archive/%{commit}/%{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:      ansible >= 2.2.0.0-1
Requires:      python2
Requires:      python-six
Requires:      tar
Requires:      openshift-ansible-docs = %{version}-%{release}
Requires:      java-1.8.0-openjdk-headless
Requires:      httpd-tools
Requires:      python-ruamel-yaml
Requires:      libselinux-python

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
cp -rp library %{buildroot}%{_datadir}/ansible/%{name}/

# openshift-ansible-bin install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{python_sitelib}/openshift_ansible
mkdir -p %{buildroot}/etc/bash_completion.d
mkdir -p %{buildroot}/etc/openshift_ansible
# Fix links
rm -f %{buildroot}%{python_sitelib}/openshift_ansible/aws
rm -f %{buildroot}%{python_sitelib}/openshift_ansible/gce

# openshift-ansible-docs install
# Install example inventory into docs/examples
mkdir -p docs/example-inventories
cp inventory/byo/* docs/example-inventories/

# openshift-ansible-playbooks install
cp -rp playbooks %{buildroot}%{_datadir}/ansible/%{name}/
# remove contiv plabooks
rm -rf %{buildroot}%{_datadir}/ansible/%{name}/playbooks/adhoc/contiv

# BZ1330091
find -L %{buildroot}%{_datadir}/ansible/%{name}/playbooks -name lookup_plugins -type l -delete
find -L %{buildroot}%{_datadir}/ansible/%{name}/playbooks -name filter_plugins -type l -delete

# openshift-ansible-roles install
cp -rp roles %{buildroot}%{_datadir}/ansible/%{name}/
# remove contiv role
rm -rf %{buildroot}%{_datadir}/ansible/%{name}/roles/contiv/*
# openshift_master_facts symlinks filter_plugins/oo_filters.py from ansible_plugins/filter_plugins
pushd %{buildroot}%{_datadir}/ansible/%{name}/roles/openshift_master_facts/filter_plugins
ln -sf ../../../../../ansible_plugins/filter_plugins/oo_filters.py oo_filters.py
popd
# openshift_master_facts symlinks lookup_plugins/oo_option.py from ansible_plugins/lookup_plugins
pushd %{buildroot}%{_datadir}/ansible/%{name}/roles/openshift_master_facts/lookup_plugins
ln -sf ../../../../../ansible_plugins/lookup_plugins/oo_option.py oo_option.py
popd

# openshift-ansible-filter-plugins install
cp -rp filter_plugins %{buildroot}%{_datadir}/ansible_plugins/

# openshift-ansible-lookup-plugins install
cp -rp lookup_plugins %{buildroot}%{_datadir}/ansible_plugins/

# openshift-ansible-callback-plugins install
cp -rp callback_plugins %{buildroot}%{_datadir}/ansible_plugins/

# create symlinks from /usr/share/ansible/plugins/lookup ->
# /usr/share/ansible_plugins/lookup_plugins
pushd %{buildroot}%{_datadir}
mkdir -p ansible/plugins
pushd ansible/plugins
ln -s ../../ansible_plugins/lookup_plugins lookup
ln -s ../../ansible_plugins/filter_plugins filter
ln -s ../../ansible_plugins/callback_plugins callback
popd
popd

# atomic-openshift-utils install
pushd utils
%{__python} setup.py install --skip-build --root %{buildroot}
# Remove this line once the name change has happened
mv -f %{buildroot}%{_bindir}/oo-install %{buildroot}%{_bindir}/atomic-openshift-installer
mkdir -p %{buildroot}%{_datadir}/atomic-openshift-utils/
cp etc/ansible.cfg %{buildroot}%{_datadir}/atomic-openshift-utils/ansible.cfg
mkdir -p %{buildroot}%{_mandir}/man1/
cp -v docs/man/man1/atomic-openshift-installer.1 %{buildroot}%{_mandir}/man1/
cp etc/ansible-quiet.cfg %{buildroot}%{_datadir}/atomic-openshift-utils/ansible-quiet.cfg
popd

# Base openshift-ansible files
%files
%doc README*
%license LICENSE
%dir %{_datadir}/ansible/%{name}
%{_datadir}/ansible/%{name}/library
%ghost %{_datadir}/ansible/%{name}/playbooks/common/openshift-master/library.rpmmoved

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
# openshift-ansible-playbooks subpackage
# ----------------------------------------------------------------------------------
%package playbooks
Summary:       Openshift and Atomic Enterprise Ansible Playbooks
Requires:      %{name} = %{version}
Requires:      %{name}-roles = %{version}
Requires:      %{name}-lookup-plugins = %{version}
Requires:      %{name}-filter-plugins = %{version}
Requires:      %{name}-callback-plugins = %{version}
BuildArch:     noarch

%description playbooks
%{summary}.

%files playbooks
%{_datadir}/ansible/%{name}/playbooks

# We moved playbooks/common/openshift-master/library up to the top and replaced
# it with a symlink. RPM doesn't handle this so we have to do some pre-transaction
# magic. See https://fedoraproject.org/wiki/Packaging:Directory_Replacement
%pretrans playbooks -p <lua>
-- Define the path to directory being replaced below.
-- DO NOT add a trailing slash at the end.
path = "/usr/share/ansible/openshift-ansible/playbooks/common/openshift-master/library"
st = posix.stat(path)
if st and st.type == "directory" then
  status = os.rename(path, path .. ".rpmmoved")
  if not status then
    suffix = 0
    while not status do
      suffix = suffix + 1
      status = os.rename(path .. ".rpmmoved", path .. ".rpmmoved." .. suffix)
    end
    os.rename(path, path .. ".rpmmoved")
  end
end

%package roles
# ----------------------------------------------------------------------------------
# openshift-ansible-roles subpackage
# ----------------------------------------------------------------------------------
Summary:       Openshift and Atomic Enterprise Ansible roles
Requires:      %{name} = %{version}
Requires:      %{name}-lookup-plugins = %{version}
Requires:      %{name}-filter-plugins = %{version}
Requires:      %{name}-callback-plugins = %{version}
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
%{_datadir}/ansible/plugins/filter


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
%{_datadir}/ansible/plugins/lookup


# ----------------------------------------------------------------------------------
# openshift-ansible-callback-plugins subpackage
# ----------------------------------------------------------------------------------
%package callback-plugins
Summary:       Openshift and Atomic Enterprise Ansible callback plugins
Requires:      %{name} = %{version}
BuildArch:     noarch

%description callback-plugins
%{summary}.

%files callback-plugins
%{_datadir}/ansible_plugins/callback_plugins
%{_datadir}/ansible/plugins/callback

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
%{_mandir}/man1/*
%{_datadir}/atomic-openshift-utils/ansible-quiet.cfg


%changelog
* Tue Jan 31 2017 Scott Dodson <sdodson@redhat.com> 3.5.3-1
- Adding bool filter to ensure that we correctly set ops host for fluentd
  (ewolinet@redhat.com)
- Set default GCE hostname to shost instance name. (abutcher@redhat.com)
- Fail on Ansible version 2.2.1.0 (rteague@redhat.com)
- During node upgrade upgrade openvswitch rpms (sdodson@redhat.com)
- HTPASSWD_AUTH (tbielawa@redhat.com)
- Added repoquery to lib_utils. (twiest@redhat.com)
- Create v3_5 upgrade playbooks (rteague@redhat.com)
- GCE deployment fails due to invalid lookup (ccoleman@redhat.com)
- Resolving yamllint issues from logging playbooks (ewolinet@redhat.com)
- Updating openshift_hosted_logging to update master-configs with
  publicLoggingURL (ewolinet@redhat.com)
- Added oc_serviceaccount to lib_openshift. (twiest@redhat.com)
- Breaking out master-config changing and updated playbook to apply change to
  other masters (ewolinet@redhat.com)
- fix negative stride encountered from openshift_logging (jcantril@redhat.com)
- add persistent versions of quickstarts (bparees@redhat.com)
- Fixing docs.  Added bugzilla to doc. (kwoodson@redhat.com)
- ensuring ruamel.yaml is on target for oc_scale (ewolinet@redhat.com)
- Updating to correctly pull handler for openshift_logging. Adding logic to
  openshift_hosted_logging too (ewolinet@redhat.com)
- Adding names to plays and standardizing (rteague@redhat.com)
- Updating openshift_logging role to add kibana public url to loggingPublicURL
  in master-config (ewolinet@redhat.com)
- Only manual scale down being allowed now (ewolinet@redhat.com)
- adopt oc_scale for openshift_metrics role (jcantril@redhat.com)
- fix 1414625. Additional fix to run password commands on control node
  (jcantril@redhat.com)
- adopt oc_scale module for openshift_logging role (jcantril@redhat.com)
- Adding fix for when the resource does not exist.  Added test cases.
  (kwoodson@redhat.com)
- Updating to reuse previous ES DC names and always generate DCs
  (ewolinet@redhat.com)
- Correct usage of draining nodes (rteague@redhat.com)
- Fixing fluentd node labelling (ewolinet@redhat.com)
- Fixing linters. (kwoodson@redhat.com)
- Fixing base.py for node and scale.  Autogenerated code. (kwoodson@redhat.com)
- Added unit integration tests. Enhanced unit tests.  Fixed an issue in
  openshift_cmd for namespace. (kwoodson@redhat.com)
- Adding oadm_manage_node to lib_openshift. (kwoodson@redhat.com)
- Fixing namespace param in doc to reflect default value. (kwoodson@redhat.com)
- .gitignore cleanup (rteague@redhat.com)
- Standardize add_host: with name and changed_when (rteague@redhat.com)
- Adding banners.  Small bug fix to namespace appending in base.
  (kwoodson@redhat.com)
- Comma separate no_proxy host list in openshift_facts so that it appears as a
  string everywhere it is used. (abutcher@redhat.com)
- Fixing tests and linting. (kwoodson@redhat.com)
- Adding unit test for oc_scale (kwoodson@redhat.com)
- Adding integration test for oc_scale. (kwoodson@redhat.com)
- Adding oc_scale to lib_openshift. (kwoodson@redhat.com)
- Add 10 second wait after disabling firewalld (sdodson@redhat.com)
- Added oc_secret to lib_openshift. (twiest@redhat.com)
- Remove master_count restriction. (abutcher@redhat.com)
- flake8 mccabe dependency fix (rteague@redhat.com)
- Generate the artifacts from fragments. (tbielawa@redhat.com)
- Update the generators to include fragment banners (tbielawa@redhat.com)
- Make use of AnsibleDumper in openshift_master filters s.t. we can represent
  AnsibleUnsafeText when dumping yaml. (abutcher@redhat.com)
- Set metrics url even if metrics_deploy is false
  (alberto.rodriguez.peon@cern.ch)
- Template update for Hawkular Metrics 0.23 (mwringe@redhat.com)

* Wed Jan 25 2017 Scott Dodson <sdodson@redhat.com> 3.5.2-1
- Sync latest image streams (sdodson@redhat.com)
- Fix containerized haproxy config (andrew@andrewklau.com)
- Allow RHEL subscription for OSE 3.4 (lhuard@amadeus.com)
- fixes BZ-1415447. Error when stopping heapster.  Modify to be conditional
  include (jcantril@redhat.com)
- override nodename for gce with cloudprovider (jdetiber@redhat.com)
- fixes jks generation, node labeling, and rerunning for oauth secrets
  (ewolinet@redhat.com)
- allow openshift_logging role to specify nodeSelectors (jcantril@redhat.com)
- Remove is_containerized check for firewalld installs (rteague@redhat.com)
- Clean up pylint for delete_empty_keys. (abutcher@redhat.com)
- [os_firewall] Fix default iptables args. (abutcher@redhat.com)
- Add new option 'openshift_docker_selinux_enabled' (rteague@redhat.com)
- Temporary work-around for flake8 vs maccabe version conflict
  (tbielawa@redhat.com)
- do not set empty proxy env variable defaults (bparees@redhat.com)
- fix BZ1414477. Use keytool on control node and require java
  (jcantril@redhat.com)
- Remove unused temporary directory in master config playbook.
  (abutcher@redhat.com)
- Added link to HOOKS in README (smilner@redhat.com)
- HOOKS.md added documenting new hooks (smilner@redhat.com)
- [os_firewall] Add -w flag to wait for iptables xtables lock.
  (abutcher@redhat.com)
- fixes BZ-1414625. Check for httpd-tools and java before install
  (jcantril@redhat.com)
- Add a mid upgrade hook, re-prefix variables. (dgoodwin@redhat.com)
- treat force_pull as a bool (bparees@redhat.com)
- Adding to ansible spec and changing logging jks generation to be a
  local_action (ewolinet@redhat.com)
- Add containzerized haproxy option (andrew@andrewklau.com)
- Reorder node dnsmasq dependency s.t. networkmanager is restarted after
  firewall changes have been applied. (abutcher@redhat.com)
- Removing docker run strategy and make java a requirement for control host
  (ewolinet@redhat.com)
- Adding version to lib_openshift (kwoodson@redhat.com)
- Updating to use docker run instead of scheduling jks gen pod
  (ewolinet@redhat.com)
- jenkins v1.3 templates should not enable oauth (gmontero@redhat.com)
- fix oc_apply to allow running on any control node (jcantril@redhat.com)
- g_master_mktemp in openshift-master conflicts with
  openshift_master_certificates (rmeggins@redhat.com)
- fixes #3127. Get files for oc_apply from remote host (jcantril@redhat.com)
- Debug message before running hooks. (dgoodwin@redhat.com)
- Cleaning repo cache earlier (rteague@redhat.com)
- Added tar as a requirement per BZ1388445 (smilner@redhat.com)
- fixes BZ141619.  Corrects the variable in the README (jcantril@redhat.com)
- Run user provided hooks prior to system/service restarts.
  (dgoodwin@redhat.com)
- Implement pre/post master upgrade hooks. (dgoodwin@redhat.com)
- Adding oc_obj to the lib_openshift library (kwoodson@redhat.com)
- Addressing found issues with logging role (ewolinet@redhat.com)
- Updated the generate.py scripts for tox and virtualenv. (kwoodson@redhat.com)
- Adding tox tests for generated code. (kwoodson@redhat.com)
- Perform master upgrades in a single play serially. (dgoodwin@redhat.com)
- Validate system restart policy during pre-upgrade. (dgoodwin@redhat.com)
- Correct consistency between upgrade playbooks (rteague@redhat.com)
- Wait for nodes to be ready before proceeding with upgrade.
  (dgoodwin@redhat.com)

* Wed Jan 18 2017 Scott Dodson <sdodson@redhat.com> 3.5.1-1
- More reliable wait for master after full host reboot. (dgoodwin@redhat.com)
- kubelet must have rw to cgroups for pod/qos cgroups to function
  (decarr@redhat.com)
- Adding a few updates for python27,35 compatibility (kwoodson@redhat.com)
- update examples to cover build default/override configuration
  (bparees@redhat.com)
- Fix yaml lint in easy-mode playbook (tbielawa@redhat.com)
- Removed trailing spaces from line #34 (kunallimaye@gmail.com)
- Install subscription-manager to fix issue-3102 (kunallimaye@gmail.com)
- Changing formatting for issue#2244 update (kunallimaye@gmail.com)
- Addressing Travis errors (ewolinet@redhat.com)
- Adding --verfiy to generate script. (kwoodson@redhat.com)
- v1.3 Add RHAMP (sdodson@redhat.com)
- Update v1.4 content, add api-gateway (sdodson@redhat.com)
- Add v1.5 content (sdodson@redhat.com)
- Update example sync script (sdodson@redhat.com)
- use pod to generate keystores (#14) (jcantrill@users.noreply.github.com)
- Ensure serial certificate generation for node and master certificates.
  (abutcher@redhat.com)
- [Cert Expiry] Add serial numbers, include example PBs, docs
  (tbielawa@redhat.com)
- properly set changes when oc apply (jcantril@redhat.com)
- additional cr fixes (jcantril@redhat.com)
- metrics fixes for yamlint (jcantril@redhat.com)
- additional code reviews (jcantril@redhat.com)
- set replicas to current value so not to disrupt current pods (#13)
  (jcantrill@users.noreply.github.com)
- User provided certs pushed from control. vars reorg (#12)
  (jcantrill@users.noreply.github.com)
- update vars to allow scaling of components (#9)
  (jcantrill@users.noreply.github.com)
- allow definition of cpu/memory limits/resources (#11)
  (jcantrill@users.noreply.github.com)
- rename variables to be less extraneous (#10)
  (jcantrill@users.noreply.github.com)
- copy admin cert for use in subsequent tasks (#8)
  (jcantrill@users.noreply.github.com)
- Add tasks to uninstall metrics (#7) (jcantrill@users.noreply.github.com)
- Custom certificates (#5) (bbarcaro@redhat.com)
- prefix vars with metrics role (#4) (jcantrill@users.noreply.github.com)
- Bruno Barcarol Guimarães work to move metrics to ansible from deployer
  (jcantril@redhat.com)
- Adding oc_edit module to lib_openshift. (kwoodson@redhat.com)
- Create individual serving cert and loopback kubeconfig for additional
  masters. (abutcher@redhat.com)
- add configuration for build default+overrides settings (bparees@redhat.com)
- delete idempotent (ewolinet@redhat.com)
- additional comments addressed (ewolinet@redhat.com)
- Updating upgrade_logging to be more idempotent (ewolinet@redhat.com)
- Using oc_apply task for idempotent (ewolinet@redhat.com)
- Removing shell module calls and cleaning up changed (ewolinet@redhat.com)
- lib_openshift modules.  This is the first one. oc_route.
  (kwoodson@redhat.com)
- Updated modify_yaml with docstring and clarifications (smilner@redhat.com)
- Rename subrole facts -> init (rhcarvalho@gmail.com)
- Move Python modules into role (rhcarvalho@gmail.com)
- Document playbook directories (rhcarvalho@gmail.com)
- Document bin/cluster tool (rhcarvalho@gmail.com)
- keys should be lowercase according to the spec (jf.cron0@gmail.com)
- filter: Removed unused validation calls (smilner@redhat.com)
- Updated initializer usage in filters (smilner@redhat.com)
- fix when statement indentation, cast to bool (jf.cron0@gmail.com)
- add openshift_facts as role dependency (jf.cron0@gmail.com)
- Added setup.py to flake8 tests (smilner@redhat.com)
- Do not default registry storage kind to 'nfs' when 'nfs' group exists.
  (abutcher@redhat.com)
- Fix inconsistent task name (rhcarvalho@gmail.com)
- Reduce code duplication using variable (rhcarvalho@gmail.com)
- Another proposed update to the issue template (tbielawa@redhat.com)
- Replace custom variables with openshift_facts (rhcarvalho@gmail.com)
- Catch DBus exceptions on class initialization (rhcarvalho@gmail.com)
- addressing comments (ewolinet@redhat.com)
- Move playbook to BYO (rhcarvalho@gmail.com)
- Fix typo in inventory README.md (lberk@redhat.com)
- Refactor preflight check into roles (rhcarvalho@gmail.com)
- Make flake8 (py35) happy on bare except (rhcarvalho@gmail.com)
- Make callback plugin an always-on aggregate plugin (rhcarvalho@gmail.com)
- Add RPM checks as an adhoc playbook (rhcarvalho@gmail.com)
- first swing at release version wording (timbielawa@gmail.com)
- Correct tox to run on Travis (rteague@redhat.com)
- Adding ability to systematically modify yaml from ansible.
  (kwoodson@redhat.com)
- oo_filters: Moved static methods to functions (smilner@redhat.com)
- Correct return code compairison for yamllint (rteague@redhat.com)
- Add a fact to select --evacuate or --drain based on your OCP version
  (tbielawa@redhat.com)
- Update branch status (sdodson@redhat.com)
- rename openshift_metrics to openshift_hosted_metrics (jcantril@redhat.com)
- Update aws dynamic inventory (lhuard@amadeus.com)
- improve issue template (sdodson@redhat.com)
- cleanup: Removed debug prints from tests (smilner@redhat.com)
- remove debug statement from test (jdetiber@redhat.com)
- Support openshift_node_port_range for configuring service NodePorts
  (ccoleman@redhat.com)
- Workaround for dnf+docker version race condition (smilner@redhat.com)
- use etcdctl from the container when containerized=True (gscrivan@redhat.com)
- Partial uninstall (sejug@redhat.com)
- increase test coverage (jdetiber@redhat.com)
- Update aws dynamic inventory (lhuard@amadeus.com)
- update travis to use tox for utils (jdetiber@redhat.com)
- More toxification (jdetiber@redhat.com)
- add test for utils to bump coverage (jdetiber@redhat.com)
- The scaleup subcommand does not support the unattended option
  (tbielawa@redhat.com)
- Move role dependencies out of playbooks for openshift_master, openshift_node
  and openshift_hosted. (abutcher@redhat.com)
- Remove unused file (rhcarvalho@gmail.com)
- Remove unused file (rhcarvalho@gmail.com)
- Remove spurious argument (rhcarvalho@gmail.com)
- Fixing collision of system.admin cert generation (ewolinet@redhat.com)
- minor updates for code reviews, remove unused params (jcantril@redhat.com)
- Updating to use deployer pod to generate JKS chain instead
  (ewolinet@redhat.com)
- Creating openshift_logging role for deploying Aggregated Logging without a
  deployer image (ewolinet@redhat.com)
- Begin requiring Docker 1.12. (dgoodwin@redhat.com)

* Mon Jan 09 2017 Scott Dodson <sdodson@redhat.com> 3.5.0-1
- Update manpage version. (tbielawa@redhat.com)
- Fix openshift_image_tag=latest. (abutcher@redhat.com)
- Use registry.access.redhat.com/rhel7/etcd instead of etcd3
  (sdodson@redhat.com)
- Fix repo defaults (sdodson@redhat.com)
- Use openshift.common.hostname when verifying API port available.
  (abutcher@redhat.com)
- Re-add when condition which was removed mistakenly in #3036
  (maszulik@redhat.com)
- logging-deployer pull fixes from origin-aggregated-logging/#317
  (sdodson@redhat.com)
- Don't upgrade etcd on atomic host, ever. (sdodson@redhat.com)
- Change wording in the quick installer callback plugin (tbielawa@redhat.com)
- Fix jsonpath expected output when checking registry volume secrets
  (maszulik@redhat.com)
- Enable repos defined in openshift_additional_repos by default
  (sdodson@redhat.com)
- Add required python-six package to installation (tbielawa@redhat.com)
- Hush the sudo privs check in oo-installer (tbielawa@redhat.com)
- Add future versions to openshift_facts (ccoleman@redhat.com)
- Cast openshift_enable_origin_repo to bool. (abutcher@redhat.com)
- Update CFME template to point to GA build (simaishi@redhat.com)
- Update aoi manpage with correct operation count (tbielawa@redhat.com)
- Add templates for CFME Beta pod images (simaishi@redhat.com)
- Add osnl_volume_reclaim_policy variable to nfs_lvm role
  (ando.roots@bigbank.ee)
- remove duplicate filter name and oo_pdb (jdetiber@redhat.com)
- remove old Ops tooling (jdetiber@redhat.com)
- enable pip cache for travis (jdetiber@redhat.com)
- python3 support, add tox for better local testing against multiple python
  versions (jdetiber@redhat.com)
- modify_yaml: handle None value during update. (abutcher@redhat.com)
- Update the openshift-certificate-expiry README to reflect latest changes
  (tbielawa@redhat.com)
- Deprecate node 'evacuation' with 'drain' (tbielawa@redhat.com)
- Add master config hook for 3.4 upgrade and fix facts ordering for config hook
  run. (abutcher@redhat.com)
- The next registry.access.redhat.com/rhel7/etcd image will be 3.0.15
  (sdodson@redhat.com)
- [uninstall] Remove excluder packages (sdodson@redhat.com)
- Check embedded etcd certs now, too (tbielawa@redhat.com)
- Include 'total' and 'ok' in check results (tbielawa@redhat.com)
- Enable firewalld by default (rteague@redhat.com)
- Fix access_modes initialization (luis.fernandezalvarez@epfl.ch)
- Updated OpenShift Master iptables rules (rteague@redhat.com)
- YAML Linting (rteague@redhat.com)
- Make both backup and upgrade optional (sdodson@redhat.com)
- [upgrades] Upgrade etcd by default (sdodson@redhat.com)
- upgrades - Fix logic error about when to backup etcd (sdodson@redhat.com)
- Limit node certificate SAN to node hostnames/ips. (abutcher@redhat.com)
- Make 'cover-erase' a config file setting. Move VENT target to pre-req for all
  ci-* targets (tbielawa@redhat.com)
- Fixes to 'make ci' (tbielawa@redhat.com)
- Resolved lint issues (rteague@redhat.com)
- Minimum Ansible version check (rteague@redhat.com)
- Removed verify_ansible_version playbook refs (rteague@redhat.com)
- Fix coverage not appending new data (tbielawa@redhat.com)
- Drop 3.2 upgrade playbooks. (dgoodwin@redhat.com)
- Silence warnings when using rpm directly (dag@wieers.com)
- Silence warnings when using rpm directly (dag@wieers.com)
- Silence warnings when using rpm directly (dag@wieers.com)
- Remove Hostname from 1.1 and 1.2 predicates (jdetiber@redhat.com)
- Properly handle x.y.z formatted versions for openshift_release
  (jdetiber@redhat.com)
- etcd_upgrade: Simplify package installation (sdodson@redhat.com)
- Speed up 'make ci' and trim the output (tbielawa@redhat.com)
- add comments and remove debug code (jdetiber@redhat.com)
- Pre-pull master/node/ovs images during upgrade. (dgoodwin@redhat.com)
- Handle updating of scheduler config during upgrade (jdetiber@redhat.com)
- Fix templating (jdetiber@redhat.com)
- test updates (jdetiber@redhat.com)
- Always install latest etcd for containerized hosts (sdodson@redhat.com)
- etcd_upgrade : Use different variables for rpm vs container versions
  (sdodson@redhat.com)
- Switch back to using etcd rather than etcd3 (sdodson@redhat.com)
- node_dnsmasq - restart dnsmasq if it's not currently running
  (sdodson@redhat.com)
- Conditionalize master config update for admission_plugin_config.
  (abutcher@redhat.com)
- upgrade_control_plane.yml: systemd_units.yaml nees the master facts
  (mchappel@redhat.com)
- openshift-master/restart : use openshift.common.hostname instead of
  inventory_hostname (mchappel@redhat.com)
- Update scheduler predicate/priorities vars (jdetiber@redhat.com)
- fix tags (jdetiber@redhat.com)
- openshift_node_dnsmasq - Remove strict-order option from dnsmasq
  (sdodson@redhat.com)
- Fix metricsPublicURL only being set correctly on first master.
  (dgoodwin@redhat.com)
- Explictly set etcd vars for byo scaleup (smunilla@redhat.com)
- Cleanup ovs file and restart docker on every upgrade. (dgoodwin@redhat.com)
- Sync latest image stream and templates for v1.3 and v1.4 (sdodson@redhat.com)
- xpaas v1.3.5 (sdodson@redhat.com)
- Ansible version check update (tbielawa@redhat.com)
- allow 'latest' origin_image_tag (sjenning@redhat.com)
- Remove duplicate when key (rteague@redhat.com)
- refactor handling of scheduler defaults (jdetiber@redhat.com)
- update tests and flake8/pylint fixes (jdetiber@redhat.com)
- fix tagging (jdetiber@redhat.com)
- do not report changed for group mapping (jdetiber@redhat.com)
- fix selinux issues with etcd container (dusty@dustymabe.com)
- etcd upgrade playbook is not currently applicable to embedded etcd installs
  (sdodson@redhat.com)
- Fix invalid embedded etcd fact in etcd upgrade playbook.
  (dgoodwin@redhat.com)
- Gracefully handle OpenSSL module absence (misc@redhat.com)
- Refactored to use Ansible systemd module (rteague@redhat.com)
- Updating docs for Ansible 2.2 requirements (rteague@redhat.com)
- Fix the list done after cluster creation on libvirt and OpenStack
  (lhuard@amadeus.com)
- Set nameservers on DHCPv6 event (alexandre.lossent@cern.ch)
- Systemd `systemctl show` workaround (rteague@redhat.com)
- Verify the presence of dbus python binding (misc@redhat.com)
- Update README.md (jf.cron0@gmail.com)
- Reference master binaries when delegating from node hosts which may be
  containerized. (abutcher@redhat.com)
- Merge kube_admission_plugin_config with admission_plugin_config
  (smunilla@redhat.com)
- Added a BYO playbook for configuring NetworkManager on nodes
  (skuznets@redhat.com)
- Make the role work on F25 Cloud (misc@redhat.com)
- Make os_firewall_manage_iptables run on python3 (misc@redhat.com)
- Modified the error message being checked for (vishal.patil@nuagenetworks.net)
- Only run tuned-adm if tuned exists. (dusty@dustymabe.com)
- Delegate openshift_manage_node tasks to master host. (abutcher@redhat.com)
- Fix rare failure to deploy new registry/router after upgrade.
  (dgoodwin@redhat.com)
- Refactor os_firewall role (rteague@redhat.com)
- Allow ansible to continue when a node is unaccessible or fails.
  (abutcher@redhat.com)
- Create the file in two passes, atomicly copy it over (sdodson@redhat.com)
- Escape LOGNAME variable according to GCE rules (jacek.suchenia@ocado.com)
- node_dnsmasq -- Set dnsmasq as our only nameserver (sdodson@redhat.com)
- Refactor to use Ansible package module (rteague@redhat.com)
- Allow users to disable the origin repo creation (sdodson@redhat.com)
- Fix yum/subman version check on Atomic. (dgoodwin@redhat.com)
- Check for bad versions of yum and subscription-manager. (dgoodwin@redhat.com)
- Corrected syntax and typos (rteague@redhat.com)
- Fix GCE cluster creation (lhuard@amadeus.com)
- Optimize the cloud-specific list.yml playbooks (lhuard@amadeus.com)
- Added ip forwarding for nuage (vishal.patil@nuagenetworks.net)
- Fix typo (sdodson@redhat.com)
- Fix a few places where we're not specifying the admin kubeconfig
  (sdodson@redhat.com)
- Add rolebinding-reader (sdodson@redhat.com)
- Add view permissions to hawkular sa (sdodson@redhat.com)
- Use multiple '-v's when creating the metrics deployer command
  (tbielawa@redhat.com)
- Sync logging deployer changes from origin to enterprise (sdodson@redhat.com)
- Docker daemon is started prematurely. (eric.mountain@amadeus.com)
- Sync latest enterprise/metrics-deployer.yaml (sdodson@redhat.com)
- Sync latest s2i content (sdodson@redhat.com)
- Actually upgrade host etcdctl no matter what (sdodson@redhat.com)
- Make etcd containerized upgrade stepwise (sdodson@redhat.com)
- Fix commit-offsets in version detection for containerized installs
  (tbielawa@redhat.com)
- Fix HA upgrade when fact cache deleted. (dgoodwin@redhat.com)
- Fix openshift_hosted_metrics_deployer_version set_fact. (abutcher@redhat.com)
- Added dependency of os_firewall to docker role (rteague@redhat.com)
- Add updates for containerized (sdodson@redhat.com)
- Add etcd upgrade for RHEL and Fedora (sdodson@redhat.com)
- Drop /etc/profile.d/etcdctl.sh (sdodson@redhat.com)
- Move backups to a separate file for re-use (sdodson@redhat.com)
- Uninstall etcd3 package (sdodson@redhat.com)
- Resolve docker and iptables service dependencies (rteague@redhat.com)
- Add Travis integration (rhcarvalho@gmail.com)
- Default groups.oo_etcd_to_config when setting embedded_etcd in control plane
  upgrade. (abutcher@redhat.com)
- Enable quiet output for all a-o-i commands (tbielawa@redhat.com)
- Update override cluster_hostname (smunilla@redhat.com)
- Reconcile role bindings for jenkins pipeline during upgrade.
  (dgoodwin@redhat.com)
- Fix typos in openshift_facts gce cloud provider (sdodson@redhat.com)
- Don't upgrade etcd on backup operations (sdodson@redhat.com)
- Bump ansible requirement to 2.2.0.0-1 (GA) (sdodson@redhat.com)
- Fix etcd backup failure due to corrupted facts. (dgoodwin@redhat.com)
- Re-sync v1.4 image streams (andrew@andrewklau.com)
- Revert "Revert openshift.node.nodename changes" (sdodson@redhat.com)
- Change to allow cni deployments without openshift SDN (yfauser@vmware.com)
- README: fix markdown formatting (rhcarvalho@gmail.com)
- Create contribution guide (rhcarvalho@gmail.com)
- Remove README_AEP.md (rhcarvalho@gmail.com)
- Install flannel RPM on containerized but not atomic (sdodson@redhat.com)
- README: move structure overview to the top (rhcarvalho@gmail.com)
- README: cleanup setup steps (rhcarvalho@gmail.com)
- README: remove OSX setup requirements (rhcarvalho@gmail.com)
- Add missing symlink for node openvswitch oom fix. (dgoodwin@redhat.com)
- README: improve first paragraph (rhcarvalho@gmail.com)
- README: add links, fix typos (rhcarvalho@gmail.com)
- README: improve markdown formatting (rhcarvalho@gmail.com)
- Make it easier to run Python tests (rhcarvalho@gmail.com)
- FIx flannel var name (jprovazn@redhat.com)
- Always add local dns domain to no_proxy (jawed.khelil@amadeus.com)
- Refactor default sdn_cluster_network_cidr and sdn_host_subnet_length
  (sdodson@redhat.com)
- Revert "Fix the nodeName of the OpenShift nodes on OpenStack"
  (sdodson@redhat.com)
- Revert "Fix OpenStack cloud provider" (sdodson@redhat.com)
- Revert "Check that OpenStack hostnames are resolvable" (sdodson@redhat.com)
- set AWS creds task with no_logs (somalley@redhat.com)
- Change the logic to just compare against masters and nodes.
  (tbielawa@redhat.com)
- Append /inventory/README.md to explain what is BYO inventory folder #2742
  (contact@stephane-klein.info)
- Remove unused openshift-ansible/inventory/hosts file #2740 (contact@stephane-
  klein.info)
- Remove unused playbooks adhoc metrics_setup files #2717 (contact@stephane-
  klein.info)
- a-o-i: remove dummy data_file (rhcarvalho@gmail.com)
- a-o-i: remove script leftover from OpenShift v2 (rhcarvalho@gmail.com)
- [openstack] allows timeout option for heat create stack
  (douglaskippsmith@gmail.com)
- [openstack] updates documentation to show that you need to install shade
  (douglaskippsmith@gmail.com)
- default to multizone GCE config (sjenning@redhat.com)
- Add some tests for utils to get the coverage up. (tbielawa@redhat.com)
- Update defaults for clusterNetworkCIDR & hostSubnetLength
  (smunilla@redhat.com)
- Add hawkular admin cluster role to management admin (fsimonce@redhat.com)
- Prevent useless master by reworking template for master service enf file
  (jkhelil@gmail.com)
- support 3rd party scheduler (jannleno1@gmail.com)
- Add nuage rest server port to haproxy firewall rules. (abutcher@redhat.com)
- Port openshift_facts to py3 (misc@redhat.com)
- storage/nfs_lvm: Also export as ReadWriteOnce (walters@verbum.org)

* Fri Nov 04 2016 Scott Dodson <sdodson@redhat.com> 3.4.17-1
- Fix indentation for flannel etcd vars (smunilla@redhat.com)
- Update hosted_templates (sdodson@redhat.com)
- remove console exclusions (sdodson@redhat.com)
- Restart API service always as well. (dgoodwin@redhat.com)
- Update v1.4 content (sdodson@redhat.com)
- Update quick installer upgrade mappings for 3.4 (smunilla@redhat.com)
- Update flannel etcd vars for 0.5.5 (smunilla@redhat.com)
- Where we use curl force it to use tlsv1.2 (sdodson@redhat.com)
- Bump etcd_ca_default_days to 5 years. (abutcher@redhat.com)
- Update master_lb vs cluster_hostname workflow (smunilla@redhat.com)

* Wed Nov 02 2016 Scott Dodson <sdodson@redhat.com> 3.4.16-1
- Fix HA environments incorrectly detecting mixed installed environments
  (tbielawa@redhat.com)
- Deploy an OOM systemd override for openvswitch. (dgoodwin@redhat.com)
- Only restart dnsmasq if the DNS servers have changed (tbielawa@redhat.com)
- Update installation summary for etcd members (smunilla@redhat.com)
- Fix changed_when (sdodson@redhat.com)
- add io labels (tdawson@redhat.com)
- Touch all ini_file files before using them (sdodson@redhat.com)
- Remove commit offset strings from parsed versions (tbielawa@redhat.com)
- Update variant_version (smunilla@redhat.com)

* Mon Oct 31 2016 Troy Dawson <tdawson@redhat.com> 3.4.15-1
- Bump documented openshift_release for 1.4/3.4. (dgoodwin@redhat.com)
- Add requirements, fix a small formatting issue.
  (erinn.looneytriggs@gmail.com)

* Fri Oct 28 2016 Troy Dawson <tdawson@redhat.com> 3.4.14-1
- Change HA master controller service to restart always. (dgoodwin@redhat.com)
- Default hosted_registry_insecure true when insecure registry present in
  existing /etc/sysconfig/docker. (abutcher@redhat.com)
- Fix race condtion in openshift_facts (smunilla@redhat.com)

* Wed Oct 26 2016 Troy Dawson <tdawson@redhat.com> 3.4.13-1
- [upgrades] Fix containerized node (sdodson@redhat.com)
- Add support for 3.4 upgrade. (dgoodwin@redhat.com)
- Update link to latest versions upgrade README (ebballon@gmail.com)
- Bump logging and metrics deployers to 3.3.1 and 3.4.0 (sdodson@redhat.com)
- Remove Vagrantfile (jdetiber@redhat.com)
- Enable dnsmasq service (sdodson@redhat.com)
- Default infra template modification based on
  openshift_examples_modify_imagestreams (abutcher@redhat.com)
- Added a parameter for cert validity (vishal.patil@nuagenetworks.net)
- Fix and reorder control plane service restart. (dgoodwin@redhat.com)
- Add node-labels to kubeletArguments (tbielawa@redhat.com)

* Mon Oct 24 2016 Troy Dawson <tdawson@redhat.com> 3.4.12-1
- Move infrastructure templates into openshift_hosted_templates role.
  (abutcher@redhat.com)
- Unit tests for the debug_env logger thing (tbielawa@redhat.com)
- a-o-i: Separate install and scaleup workflows (smunilla@redhat.com)
- Reference full vars for registry object storage. (abutcher@redhat.com)

* Fri Oct 21 2016 Troy Dawson <tdawson@redhat.com> 3.4.11-1
- trouble creating service signer while running upgrade dockerized
  (henning.fjellheim@nb.no)
- Don't freak out if the oc command doesn't exist. (tbielawa@redhat.com)
- Make the json template filter-driven. (tbielawa@redhat.com)
- Add JSON result CLI parsing notes to the README (tbielawa@redhat.com)
- The JSON result saving template now includes a summary of expired/warned
  certs for easier parsing. (tbielawa@redhat.com)
- Clean up lint and other little things (polish++) (tbielawa@redhat.com)
- Fix playbooks, update readme, update default vars (tbielawa@redhat.com)
- Refactor into a role (tbielawa@redhat.com)
- Get router/registry certs. Collect common names and subjectAltNames
  (tbielawa@redhat.com)
- Support etcd certs now. Fix lint. Generate HTML report. (tbielawa@redhat.com)
- Try to make boiler plate for cert expiry checking (tbielawa@redhat.com)
- Override __init__ in default callback to avoid infinite loop.
  (abutcher@redhat.com)
- Drop pacemaker restart logic. (dgoodwin@redhat.com)
- Fix typos (rhcarvalho@gmail.com)
- Switch from "oadm" to "oc adm" and fix bug in binary sync.
  (dgoodwin@redhat.com)
- Remove uneeded import of ansible.module_utils.splitter (misc@redhat.com)

* Wed Oct 19 2016 Troy Dawson <tdawson@redhat.com> 3.4.10-1
- Get rid of openshift_node_config_file entirely (sdodson@redhat.com)
- [logging] Fix NFS volume binding (sdodson@redhat.com)
- Build full node config path in systemd_units tasks. (abutcher@redhat.com)
- Default [] (abutcher@afrolegs.com)
- Template with_items for upstream ansible-2.2 compat. (abutcher@redhat.com)

* Mon Oct 17 2016 Troy Dawson <tdawson@redhat.com> 3.4.9-1
- formatting updates in template (tobias@tobru.ch)
- Do not error on node labels set too non-string values. (manuel@hutter.io)
- Use inventory variables rather than facts (sdodson@redhat.com)
- Resume restarting node after upgrading node rpms. (dgoodwin@redhat.com)
- upgrade: Don't check avail docker version if not already installed.
  (dgoodwin@redhat.com)
- revise docs (tobias@tobru.ch)
- adjustments in docs and j2 template (tobias@tobru.ch)
- add regionendpoint parameter for registry s3 (tobias.brunner@vshn.ch)

* Fri Oct 14 2016 Troy Dawson <tdawson@redhat.com> 3.4.8-1
- update handling of use_dnsmasq (jdetiber@redhat.com)
- Fix standalone docker upgrade playbook skipping nodes. (dgoodwin@redhat.com)
- Fix missing play assignment in a-o-i callback plugin (tbielawa@redhat.com)
- Stop restarting node after upgrading master rpms. (dgoodwin@redhat.com)
- Fix upgrade mappings in quick installer (smunilla@redhat.com)
- nfs: Handle seboolean aliases not just in Fedora (walters@verbum.org)

* Wed Oct 12 2016 Troy Dawson <tdawson@redhat.com> 3.4.7-1
- set defaults for debug_level in template and task (jhcook@gmail.com)
- Set HTTPS_PROXY in example builddefaults_json (sdodson@redhat.com)
- Fix config and namespace for registry volume detection (sdodson@redhat.com)
- Apply same pattern to HA master services (sdodson@redhat.com)
- Improve how we handle containerized node failure on first startup
  (sdodson@redhat.com)
- Check that OpenStack hostnames are resolvable (lhuard@amadeus.com)

* Mon Oct 10 2016 Troy Dawson <tdawson@redhat.com> 3.4.6-1
- Retry failed master startup once (ironcladlou@gmail.com)
- [logging] Fix openshift_hosted_logging_fluentd_nodeselector
  (sdodson@redhat.com)
- Changes for etcd servers (vishal.patil@nuagenetworks.net)

* Fri Oct 07 2016 Scott Dodson <sdodson@redhat.com> 3.4.5-1
- [a-o-i] -v disables quiet ansible config. (abutcher@redhat.com)

* Fri Oct 07 2016 Troy Dawson <tdawson@redhat.com> 3.4.4-1
- note different product versions (jeder@redhat.com)
- Error out if containerized=true for lb host. (dgoodwin@redhat.com)
- Removes an unused file (jtslear@gmail.com)
- Update v1.3 content (sdodson@redhat.com)
- Add v1.4 content (sdodson@redhat.com)
- Set master facts for first master in node scaleup. (abutcher@redhat.com)
- Fix default port typo. (abutcher@redhat.com)
- Add example openid/request header providers and explain certificate
  variables. (abutcher@redhat.com)
- Move openshift.common.debug.level to openshift_facts. (abutcher@redhat.com)
- Don't secure registry or deploy registry console when infra replics == 0
  (abutcher@redhat.com)
- the example line fails on releases prior to 3.3, so put a comment there.
  (jeder@redhat.com)

* Tue Oct 04 2016 Scott Dodson <sdodson@redhat.com> 3.4.3-1
- Check if openshift_master_ingress_ip_network_cidr is defined
  (Mathias.Merscher@dg-i.net)
- allow networkConfig.ingressIPNetworkCIDRs to be configured
  (Mathias.Merscher@dg-i.net)
- Filterize haproxy frontends/backends and add method for providing additional
  frontends/backends. (abutcher@redhat.com)
- a-o-i: Force option should allow reinstall (smunilla@redhat.com)
- a-o-i: Fix openshift_node_labels (smunilla@redhat.com)
- Enable registry support for image pruning (andrew@andrewklau.com)
- Default openshift_hosted_{logging,metrics}_deploy to false.
  (abutcher@redhat.com)
- README_CONTAINERIZED_INSTALLATION: fixed link markdown
  (jakub.kramarz@freshmail.pl)
- README_AWS: makes links consistent and working again
  (jakub.kramarz@freshmail.pl)
- a-o-i: Allow better setting of host level variables (smunilla@redhat.com)
- Further secure registry improvements (abutcher@redhat.com)
- Delgate handlers to first master (smunilla@redhat.com)
- Secure registry improvements. (abutcher@redhat.com)
- Install Registry by Default (smunilla@redhat.com)
- Update play names for consistency. (abutcher@redhat.com)
- Addressed review comments (vishal.patil@nuagenetworks.net)
- Configure ops cluster storage to match normal cluster storage
  (sdodson@redhat.com)
- Fix bug with service signer cert on upgrade. (dgoodwin@redhat.com)
- Add messages to let the user know if some plays were skipped, but it's ok.
  Also, remove the final 'press a key to continue' prompt.
  (tbielawa@redhat.com)
- Set named certificate destinations as basenames of provided paths.
  (abutcher@redhat.com)
- 'fix' unittests by removing the users ability to specify an ansible config
  (tbielawa@redhat.com)
- Copy and paste more methods (tbielawa@redhat.com)
- Silence/dot-print more actions in the callback (tbielawa@redhat.com)
- Fix conflicts in spec file (tbielawa@redhat.com)
- Use pre_upgrade tag instread of a dry run variable. (dgoodwin@redhat.com)
- Move etcd backup from pre-upgrade to upgrade itself. (dgoodwin@redhat.com)
- Allow a couple retries when unscheduling/rescheduling nodes in upgrade.
  (dgoodwin@redhat.com)
- Skip the docker role in early upgrade stages. (dgoodwin@redhat.com)
- Allow filtering nodes to upgrade by label. (dgoodwin@redhat.com)
- Allow customizing node upgrade serial value. (dgoodwin@redhat.com)
- Split upgrade for control plane/nodes. (dgoodwin@redhat.com)
- Set the DomainName or DomainID in the OpenStack cloud provider
  (lhuard@amadeus.com)
- Use ansible.module_utils._text.to_text instead of
  ansible.utils.unicode.to_unicode. (abutcher@redhat.com)
- Suppress more warnings. (abutcher@redhat.com)
- Add gitHTTPProxy and gitHTTPSProxy to advanced config json option
  (sdodson@redhat.com)
- Don't set IMAGE_PREFIX if openshift_cockpit_deployer_prefix is empty
  (Robert.Bohne@ConSol.de)
- Update spec file to install manpage (tbielawa@redhat.com)
- Verify masters are upgraded before proceeding with node only upgrade.
  (dgoodwin@redhat.com)
- Attempt to tease apart pre upgrade for masters/nodes. (dgoodwin@redhat.com)
- Split upgrade entry points into control plane/node. (dgoodwin@redhat.com)
- Reunite upgrade reconciliation gating with the play it gates on.
  (dgoodwin@redhat.com)
- Drop atomic-enterprise as a valid deployment type in upgrade.
  (dgoodwin@redhat.com)
- Stop guarding against pacemaker in upgrade, no longer necessary.
  (dgoodwin@redhat.com)
- Support openshift_upgrade_dry_run=true for pre-upgrade checks only.
  (dgoodwin@redhat.com)
- Make rhel_subscribe role default to OpenShift Container Platform 3.3
  (lhuard@amadeus.com)
- Addresses most comments from @adellape (tbielawa@redhat.com)
- Changes for Nuage HA (vishal.patil@nuagenetworks.net)
- Fix deployer template for enterprise (sdodson@redhat.com)
- Add a manpage for atomic-openshift-installer (tbielawa@redhat.com)
- Remove the DNS VM on OpenStack (lhuard@amadeus.com)
- tweak logic (jdetiber@redhat.com)
- test fix for systemd changes (sdodson@redhat.com)
- Set default_subdomain properly for logging (sdodson@redhat.com)
- Adjust wait for loops (sdodson@redhat.com)
- Add storage for logging (sdodson@redhat.com)
- Fix some bugs in OpenShift Hosted Logging role (contact@stephane-klein.info)
- Add some sample inventory stuff, will update this later (sdodson@redhat.com)
- Label all nodes for fluentd (sdodson@redhat.com)
- Rename openshift_hosted_logging_image_{prefix,version} to match metrics
  (sdodson@redhat.com)
- Fix deployer template for enterprise (sdodson@redhat.com)
- Add logging to install playbooks (sdodson@redhat.com)
- Fix OpenStack cloud provider (lhuard@amadeus.com)
- Add rhaos-3.4-rhel-7 releaser to tito (sdodson@redhat.com)
- Fix the nodeName of the OpenShift nodes on OpenStack (lhuard@amadeus.com)
- Fix GCE Launch (brad@nolab.org)

* Mon Sep 26 2016 Scott Dodson <sdodson@redhat.com> 3.4.2-1
- Add an issue template (sdodson@redhat.com)
- Add openshift_hosted_router_name (andrew@andrewklau.com)
- Fix master service status changed fact. (abutcher@redhat.com)
- Clarify openshift_hosted_metrics_public_url (sdodson@redhat.com)
- Add GCE cloud provider kind. (abutcher@redhat.com)
- add documentation about the openshift_hosted_metrics_public_url option
  (kobi.zamir@gmail.com)
- Split openshift_builddefaults_no_proxy if it's not a list
  (sdodson@redhat.com)
- Fix references to openshift.master.sdn_cluster_network_cidr in node roles
  (sdodson@redhat.com)
- Update the OpenStack dynamic inventory script (lhuard@amadeus.com)
- move LICENSE to /usr/share/licenses/openshift-ansible-VERSION/
  (nakayamakenjiro@gmail.com)
- [uninstall] Stop services on all hosts prior to removing files.
  (abutcher@redhat.com)
- Do not create volume claims for hosted components when storage type is
  object. (abutcher@redhat.com)
- Add portal_net and sdn_cluster_network_cidr to node NO_PROXY
  (sdodson@redhat.com)
- Add origin-node.service.wants to uninstall (andrew@andrewklau.com)
- Update README.md (sdodson@redhat.com)
- Add 'MaxGCEPDVolumeCount' to default scheduler predicates.
  (abutcher@redhat.com)
- Switch to origin-1.x branch names (sdodson@redhat.com)
- Open ports for vxlan and Nuage monitor (vishal.patil@nuagenetworks.net)
- Add role to manageiq to allow creation of projects (azellner@redhat.com)
- Add 'MaxEBSVolumeCount' to default scheduler predicates.
  (abutcher@redhat.com)
- a-o-i: Don't set unschedulable nodes as infra (smunilla@redhat.com)
- [redeploy-certificates] Set default value for
  openshift_master_default_subdomain as workaround. (abutcher@redhat.com)
- [redeploy-certificates] Correct etcd service name. (abutcher@redhat.com)
- [upgrade] Create/configure service signer cert when missing.
  (abutcher@redhat.com)
- get quickstarts from origin, not upstream example repos (bparees@redhat.com)
- Define proxy settings for node services (sdodson@redhat.com)
- Check for use_openshift_sdn when restarting openvswitch.
  (abutcher@redhat.com)
- Move delegated_serial_command module to etcd_common. (abutcher@redhat.com)
- Fix README links. (abutcher@redhat.com)
- Check for is_atomic when uninstalling flannel package. (abutcher@redhat.com)
- Add atomic-guest tuned profile (andrew.lau@newiteration.com)
- Pause after restarting openvswitch in containerized upgrade.
  (dgoodwin@redhat.com)
- Add acceptschema2 and enforcequota settings for hosted registry
  (andrew.lau@newiteration.com)
- Always deduplicate detected certificate names (elyscape@gmail.com)
- Add option for specifying s3 registry storage root directory.
  (abutcher@redhat.com)
- Set config/namespace where missing for secure registry deployment.
  (abutcher@redhat.com)
- Flush handlers before marking a node schedulable after upgrade.
  (dgoodwin@redhat.com)
- Iterate over node inventory hostnames instead of openshift.common.hostname
  within openshift_manage_node role. (abutcher@redhat.com)
- a-o-i: Do not display version number in quick installer (smunilla@redhat.com)
- Explain our branching strategy (sdodson@redhat.com)
- Fix warnings (mkumatag@in.ibm.com)
- Don't loop over hostvars when setting node schedulability.
  (abutcher@redhat.com)
- Copy admin kubeconfig in openshift_manage_node role. (abutcher@redhat.com)
- Adjust to_padded_yaml transformation to use the AnsibleDumper
  (tbielawa@redhat.com)
- Secure registry for atomic registry deployment (deployment_subtype=registry).
  (abutcher@redhat.com)
- Record schedulability of node prior to upgrade and re-set it to that
  (sdodson@redhat.com)
- Fix string substitution error in the to_padded_yaml filter
  (tbielawa@redhat.com)
- Update image stream data (sdodson@redhat.com)
- Fix ops/qps typo (jliggitt@redhat.com)
- initial support for v1.3 with logging v1.3 (rmeggins@redhat.com)
- Only prompt for proxy vars if none are set and our version recognizes them
  (tbielawa@redhat.com)
- Don't advise people to use additional registries over oreg_url
  (sdodson@redhat.com)
- Persist net.ipv4.ip_forward sysctl entry for openshift nodes
  (tbielawa@redhat.com)
- Add flannel package removal in uninstallation playbook (mkumatag@in.ibm.com)
- This fixes an issue in AWS where the master node was not part of the nodes in
  an unschedulable way (mdanter@gmail.com)
- Don't attempt to create retry files (tbielawa@redhat.com)
- Fix nuage check. (abutcher@redhat.com)
- Change test requirements file name (tbielawa@redhat.com)
- Fix review comments (mkumatag@in.ibm.com)
- Try installing setuptools before the rest of the requirements
  (tbielawa@redhat.com)
- Switch to using a requirements.txt file and ensure that setuptools is pinned
  to the latest version available on RHEL7 (tbielawa@redhat.com)
- Try using parse_version from pkg_resources instead (tbielawa@redhat.com)
- Add missing pip requirement to virtualenv (tbielawa@redhat.com)
- Fix PyLint errors discovered when upgrading to newer version
  (tbielawa@redhat.com)
- Bug 1369410 - uninstall fail at task [restart docker] on atomic-host
  (bleanhar@redhat.com)
- Fix typo (mkumatag@in.ibm.com)
- Fix errors in docker role (mkumatag@in.ibm.com)
- Allow overriding the Docker 1.10 requirement for upgrade.
  (dgoodwin@redhat.com)
- skip if the objects already exist (rmeggins@redhat.com)
- create and process the logging deployer template in the current project,
  logging (rmeggins@redhat.com)
- do not create logging project if it already exists (rmeggins@redhat.com)

* Thu Sep 01 2016 Scott Dodson <sdodson@redhat.com> 3.4.1-1
- Bump to 3.4.0

* Wed Aug 31 2016 Scott Dodson <sdodson@redhat.com> 3.3.20-1
- Restore network plugin configuration (sdodson@redhat.com)
- Remove openshift_master_metrics_public_url (abutcher@redhat.com)
- Bug 1371836 - The variant should be Registry 3.3 (smunilla@redhat.com)

* Wed Aug 31 2016 Troy Dawson <tdawson@redhat.com> 3.3.19-1
- update flannel_subnet_len default value (mkumatag@in.ibm.com)
- Reload docker facts after upgrading docker (sdodson@redhat.com)

* Tue Aug 30 2016 Scott Dodson <sdodson@redhat.com> 3.3.18-1
- Enable dynamic storage (sdodson@redhat.com)
- Change how we set master's metricsPublicURL (sdodson@redhat.com)
- update kubelet argument example with references to new pods-per-core and new
  max-pods threshold for 3.3 (jeder@redhat.com)
- update kubelet argument example with references to new pods-per-core and new
  max-pods threshold for 3.3 (jeder@redhat.com)

* Mon Aug 29 2016 Scott Dodson <sdodson@redhat.com> 3.3.17-1
- Reload units after node container service modified. (dgoodwin@redhat.com)
- Fix flannel check (mkumatag@in.ibm.com)
- Default to port 80 when deploying cockpit-ui (smunilla@redhat.com)
- Set cloudprovider kind with openshift_facts. (abutcher@redhat.com)
- Fix openstack cloudprovider template conditional. (abutcher@redhat.com)

* Sat Aug 27 2016 Scott Dodson <sdodson@redhat.com> 3.3.16-1
- Sync image stream data (sdodson@redhat.com)
- Update metrics example inventories (sdodson@redhat.com)
- Preserve AWS options in sysconfig files. (dgoodwin@redhat.com)
- Fix metrics for containerized installs (sdodson@redhat.com)
- Cleanup items botched during rebase (sdodson@redhat.com)
- add check for server and account already exist (mangirdas@judeikis.lt)
- add run_once to repeatable actions (mangirdas@judeikis.lt)
- Remove atomic check and cockpit.socket (smunilla@redhat.com)
- Re-organize registry-console deployment. (abutcher@redhat.com)
- Add registry console template (aweiteka@redhat.com)
- Add support for Atomic Registry Installs (smunilla@redhat.com)
- Apply indentation changes to some other lines (tbielawa@redhat.com)
- Don't use openshift_env for cloud provider facts. (abutcher@redhat.com)
- Enable PEP8 tests by default in the 'make ci' target now
  (tbielawa@redhat.com)
- Fix PEP8 errors in cli_installer.py (tbielawa@redhat.com)
- Fix PEP8 in openshift_ansible.py (tbielawa@redhat.com)
- Fix PEP8 in oo_config.py (tbielawa@redhat.com)
- Fix PEP8 in variants.py (tbielawa@redhat.com)
- Fix PEP8 in facts_callback.py (tbielawa@redhat.com)
- fix duplicate src field (jdetiber@redhat.com)
- Refactor volume directory creation (sdodson@redhat.com)
- Rely on IMAGE_PREFIX and IMAGE_VERSION defaults from the templates themselves
  (sdodson@redhat.com)
- Add metrics exports to nfs role, move exports to /etc/exports.d/openshift-
  ansible.exports (sdodson@redhat.com)
- Add ability to disable pvc creation (sdodson@redhat.com)
- Fix registry volume (sdodson@redhat.com)
- add selectors for metrics and logging (sdodson@redhat.com)
- Add logic to detect existing installs (sdodson@redhat.com)
- Deploy metrics after our router (sdodson@redhat.com)
- Add Enterprise 3.3 template (sdodson@redhat.com)
- Pull in keynote demo changes (sdodson@redhat.com)
- [tags] add some support for running a subset of config via tags
  (jdetiber@redhat.com)
- [metrics] add filter to clean up hostname for use in metrics deployment
  (jdetiber@redhat.com)
- enable service-serving-cert-signer by default (abutcher@redhat.com)
- Fix review comments (mkumatag@in.ibm.com)
- Remove duplicate flannel registration (mkumatag@in.ibm.com)

* Wed Aug 24 2016 Scott Dodson <sdodson@redhat.com> 3.3.15-1
- simplify repo configuration (jdetiber@redhat.com)
- don't set virt_sandbox_use_nfs on Fedora, it was replaced by virt_use_nfs
  (maxamillion@fedoraproject.org)
- Correct flannel cert variables. (abutcher@redhat.com)
- Make note about ansible/install logs messing up ci tests
  (tbielawa@redhat.com)
- remove fedora origin copr (it's in mainline fedora now), some dnf/yum clean
  up (maxamillion@fedoraproject.org)
- Move nested print_read_config_error function into it's own function
  (tbielawa@redhat.com)
- Makefile includes ci-pyflakes target now (tbielawa@redhat.com)
- Fix BZ1368296 by quietly recollecting facts if the cache is removed
  (tbielawa@redhat.com)
- Correct masterCA config typo. (abutcher@redhat.com)
- don't gather facts when bootstrapping ansible for Fedora hosts
  (maxamillion@fedoraproject.org)
- a-o-i: Add variant and variant_version to migration (smunilla@redhat.com)
- Fix upgrade failure when master-config does not have pluginOrderOverride.
  (dgoodwin@redhat.com)
- Add externalIPNetworkCIDRs to config (smunilla@redhat.com)

* Tue Aug 23 2016 Scott Dodson <sdodson@redhat.com> 3.3.14-1
- a-o-i: Fix ansible_ssh_user question (smunilla@redhat.com)
- Don't run node config upgrade hook if host is not a node.
  (dgoodwin@redhat.com)
- Link ca to ca-bundle when ca-bundle does not exist. (abutcher@redhat.com)
- Better error if no OpenShift RPMs are available. (dgoodwin@redhat.com)
- Revert "Due to problems with with_fileglob lets avoid using it for now"
  (sdodson@redhat.com)
- Replace some virsh commands by native virt_XXX ansible module
  (lhuard@amadeus.com)
- Add warning at end of 3.3 upgrade if pluginOrderOverride is found.
  (dgoodwin@redhat.com)
- a-o-i: Remove Legacy Config Upgrade (smunilla@redhat.com)
- Fix etcd uninstall (sdodson@redhat.com)
- Bug 1358951 - Error loading config, no such key: 'deployment' when using
  previously valid answers file (smunilla@redhat.com)
- Fix standalone Docker upgrade missing symlink. (dgoodwin@redhat.com)
- Open OpenStack security group for the service node port range
  (lhuard@amadeus.com)
- Fix the “node on master” feature (lhuard@amadeus.com)
- Due to problems with with_fileglob lets avoid using it for now
  (sdodson@redhat.com)

* Fri Aug 19 2016 Troy Dawson <tdawson@redhat.com> 3.3.13-1
- Fix warnings in OpenStack provider with ansible 2.1 (lhuard@amadeus.com)
- Mount /sys rw (sdodson@redhat.com)
- Update uninstall.yml (sdodson@redhat.com)
- Fix padding on registry config (sdodson@redhat.com)

* Wed Aug 17 2016 Troy Dawson <tdawson@redhat.com> 3.3.12-1
- Fixes to typos, grammar, and product branding in cli_installer
  (tpoitras@redhat.com)
- Reconcile roles after master upgrade, but before nodes. (dgoodwin@redhat.com)
- a-o-i: Fix nosetests after removing 3.2 from installer (smunilla@redhat.com)
- Bug 1367323 - the "OpenShift Container Platform 3.2" variant is still listed
  when quick install ose-3.3 (smunilla@redhat.com)
- Bug 1367199 - iptablesSyncPeriod should default to 30s OOTB
  (smunilla@redhat.com)
- Sync remaining content (sdodson@redhat.com)
- XPaas 1.3.3 (sdodson@redhat.com)
- a-o-i: Fix broken tests from installed hosts check (smunilla@redhat.com)
- Add clientCommonNames to RequestHeaderProvider optional items
  (sdodson@redhat.com)
- a-o-i: Mapping for 3.2 Upgrades (smunilla@redhat.com)
- a-o-i: fix bz#1329455 (ghuang@redhat.com)
- Add nfs group to OSEv3:vars (sdodson@redhat.com)
- fixing openshift key error in case of node failure during run (ssh issue)
  (jawed.khelil@amadeus.com)
- add 3.3 to installer (rmeggins@redhat.com)

* Mon Aug 15 2016 Troy Dawson <tdawson@redhat.com> 3.3.11-1
- Ensure etcd user exists in etcd_server_certificates by installing etcd.
  (abutcher@redhat.com)
- a-o-i: Fix broken upgrades (smunilla@redhat.com)

* Fri Aug 12 2016 Troy Dawson <tdawson@redhat.com> 3.3.10-1
- Reference tmpdir from first master hostvars when evacuating nodes.
  (abutcher@redhat.com)
- Support for redeploying certificates. (abutcher@redhat.com)
- qps typo (deads@redhat.com)
- a-o-i: Automatically Label Nodes as Infra (smunilla@redhat.com)
- Improvements for Docker 1.10+ upgrade image nuking. (dgoodwin@redhat.com)
- a-o-i: Restrict installed host check (smunilla@redhat.com)
- Shutdown Docker before upgrading the rpm. (dgoodwin@redhat.com)
- Restrict the middleware stanza contains 'registry' and 'storage' at least on
  3.3 (ghuang@redhat.com)
- docker-registry's middleware stanza should contain 'registry' and 'storage'
  by default (ghuang@redhat.com)

* Wed Aug 10 2016 Troy Dawson <tdawson@redhat.com> 3.3.9-1
- Enable 'NoVolumeZoneConflict' policy for scheduler (abutcher@redhat.com)
- a-o-i: Update nosetests for ansible_ssh_user (smunilla@redhat.com)
- move ansible_ssh_user to deployment, remove ansible_config and
  ansible_log_path (ghuang@redhat.com)
- Labeling nodes only (ghuang@redhat.com)
- Set become=no for etcd server certificates temporary directory.
  (abutcher@redhat.com)
- Move storage includes up to main. (abutcher@redhat.com)
- Support gathering ansible 2.1/2.2 system facts (abutcher@redhat.com)
- Try/except urlparse calls. (abutcher@redhat.com)
- with_fileglob no longer supports wildcard prefixes. (abutcher@redhat.com)
- BUILD.md lies (jmainguy@redhat.com)
- Migrate ca.crt to ca-bundle.crt (sdodson@redhat.com)
- Upgrade configs for protobuf support. (dgoodwin@redhat.com)
- Fixed a bug in modify_yaml module. (dgoodwin@redhat.com)
- make the improved log formatter work with ansible 2.1 (rmeggins@redhat.com)
- Convert ansible facts callback to v2. (abutcher@redhat.com)
- Add 3.3 protobuf config stanzas for master/node config. (dgoodwin@redhat.com)
- Introduce 1.3/3.3 upgrade path. (dgoodwin@redhat.com)

* Mon Aug 08 2016 Troy Dawson <tdawson@redhat.com> 3.3.8-1
- Fix little mistake in openshift_master_htpasswd_users value .
  (jmferrer@paradigmatecnologico.com)

* Fri Aug 05 2016 Troy Dawson <tdawson@redhat.com> 3.3.7-1
- Call relocated openshift-loadbalancer playbook in master scaleup.
  (abutcher@redhat.com)
- [openshift_ca] correct check for missing CA. (abutcher@redhat.com)
- a-o-i: Rename OSE in Install Menu (smunilla@redhat.com)
- a-o-i: Allow Arbitrary Deployment Variables (smunilla@redhat.com)
- Add knobs for disabling router/registry management. (abutcher@redhat.com)
- Restore missing etcd_image fact. (abutcher@redhat.com)
- Add options for specifying named ca certificates to be added to the openshift
  ca bundle. (abutcher@redhat.com)
- oo_collect can be ran against dicts where key isn't present.
  (abutcher@redhat.com)
- Don't set a networkPluginName in 3.3 installs (sdodson@redhat.com)

* Wed Aug 03 2016 Troy Dawson <tdawson@redhat.com> 3.3.6-1
- Rename router and registry node list variables. (abutcher@redhat.com)
- a-o-i: Fix broken uninstall (smunilla@redhat.com)
- Refactor etcd certificates roles. (abutcher@redhat.com)

* Mon Aug 01 2016 Troy Dawson <tdawson@redhat.com> 3.3.5-1
- Update for issue#2244 (kunallimaye@gmail.com)
- Update for issue-2244 (kunallimaye@gmail.com)
- a-o-i: Remove AEP, OSE 3.0, and OSE 3.2 choices (smunilla@redhat.com)
- Move role dependencies to playbooks. (abutcher@redhat.com)
- Fix xpaas_templates_base (sdodson@redhat.com)
- a-o-i: Better inventory group handling (smunilla@redhat.com)
- Add dotnet image stream to enterprise installs (sdodson@redhat.com)
- Fix haproxy logs (sdodson@redhat.com)
- update bootstrap-fedora playbook with new python crypto deps
  (maxamillion@fedoraproject.org)
- Remove old sso70-basic templates (sdodson@redhat.com)
- xPaaS v1.3.2 release (sdodson@redhat.com)

* Fri Jul 29 2016 Troy Dawson <tdawson@redhat.com> 3.3.4-1
- a-o-i: Set roles on standalone storage (smunilla@redhat.com)
- Disable too many branches pylint (sdodson@redhat.com)
- a-o-i: write missing openshift_node_labels (dkorn@redhat.com)
- a-o-i: Support for arbitrary host-level variables (smunilla@redhat.com)
- Beautiful -v output from ansible (jamespic@gmail.com)
- a-o-i: Move inventory vars to the correct location (smunilla@redhat.com)
- Fix registry/router being created despite no infra nodes.
  (dgoodwin@redhat.com)
- Document openshift_portal_net (sdodson@redhat.com)
- Stagger the start of master services. (abutcher@redhat.com)
- make rpm-q module pylint warning-free (tob@butter.sh)
- add rpm_q module to query rpm database (tob@butter.sh)

* Wed Jul 27 2016 Troy Dawson <tdawson@redhat.com> 3.3.3-1
- Template named certificates with_items. (abutcher@redhat.com)
- Replace master_cert_config_dir with common config_base fact.
  (abutcher@redhat.com)
- remove outdated openshift_cluster_metrics role (jdetiber@redhat.com)
- Fix "deloyment" typo in deployment types doc (lxia@redhat.com)
- Add missing nuke_images.sh symlink. (dgoodwin@redhat.com)
- a-o-i: Persist Roles Variables (smunilla@redhat.com)
- Default nodes matching selectors when not collected. (abutcher@redhat.com)
- Copy openshift binaries instead of using wrapper script.
  (dgoodwin@redhat.com)
- Correct relative include for ansible version check. (abutcher@redhat.com)
- Fix libvirt provider for Ansible 2.1.0.0 (lhuard@amadeus.com)
- Re-arrange master and node role dependencies. (abutcher@redhat.com)
- Refactor openshift certificates roles. (abutcher@redhat.com)
- Check ansible version prior to evaluating cluster hosts and groups.
  (abutcher@redhat.com)
- Stop reporting changes when docker pull is already up to date.
  (dgoodwin@redhat.com)
- a-o-i: Write Role variable groups (smunilla@redhat.com)
- Slight modification to error when using mismatched openshift_release.
  (dgoodwin@redhat.com)
- fix "databcase" typo in example roles (lxia@redhat.com)
- Secure router only when openshift.hosted.router.certificate.contents exists.
  (abutcher@redhat.com)
- Add jenkinstemplate (sdodson@redhat.com)
- Fix bugs with origin 1.2 rpm based upgrades. (dgoodwin@redhat.com)
- Sync latest image streams and templates (sdodson@redhat.com)
- Ensure 'oo_nfs_to_config' in groups prior to checking group length when nfs
  host unset. (abutcher@redhat.com)
- We have proper ansible support and requirements in place now, de-revert this
  commit (tbielawa@redhat.com)
- Skip docker upgrades on Atomic. (dgoodwin@redhat.com)
- Resolve some deprecation warnings. (abutcher@redhat.com)
- a-o-i: Looser facts requirements for unattended (smunilla@redhat.com)
- Temporarily link registry config templates for ansible 1.9.x support.
  (abutcher@redhat.com)
- Remove relative lookup for registry config and check for skipped update in
  registry redeploy conditional. (abutcher@redhat.com)
- Arbitrary Installer yaml (smunilla@redhat.com)
- Check for existence of sebooleans prior to setting. (abutcher@redhat.com)
- Require ansible-2.1 (abutcher@redhat.com)

* Sun Jul 17 2016 Scott Dodson <sdodson@redhat.com> 3.3.2-1
- Convert openshift_release and openshift_version to strings for startswith
  (sdodson@redhat.com)
- Symlink ansible 2.x locations to ansible 1.9 locations (sdodson@redhat.com)
- Clarify message when old docker pre-installed but 1.10+ requested.
  (dgoodwin@redhat.com)
- Fix quick install 3.2 upgrade path. (dgoodwin@redhat.com)
- Fix upgrade with docker_version set. (dgoodwin@redhat.com)
- Move the bash completion into the cli role. Only add when not containerized
  (tbielawa@redhat.com)
- [master] add support for setting auditConfig (jdetiber@redhat.com)
- Remove too recent pylint option keys. (dgoodwin@redhat.com)
- pylint fixes (dgoodwin@redhat.com)
- Install bash-completion package for the oc/oadm tools (tbielawa@redhat.com)
- Fix more docker role logic. (dgoodwin@redhat.com)
- Add checks to docker role for 1.9.1+. (dgoodwin@redhat.com)
- Make libvirt’s VM use virtio-scsi insteal of virtio-blk
  (lhuard@amadeus.com)
- Fix erroneous pylint error (smunilla@redhat.com)
- Remove 3.0 and 3.1 upgrade sub-dirs. (dgoodwin@redhat.com)
- Rename upgrade to just v3_2 as it's now major and minor.
  (dgoodwin@redhat.com)
- Set registry replicas = 1 when no storage specified. (abutcher@redhat.com)
- Re-align the OpenStack firewall rules with the iptables rules
  (lhuard@amadeus.com)
- Fix bin/cluster openstack related error (lhuard@amadeus.com)
- Fix upgrades with an openshift_image_tag set. (dgoodwin@redhat.com)
- ops-docker-loopback-to-direct-lvm.yml: fix typo on the variable name
  "cli_name vs cli_host" (gael.lambert@redhat.com)
- Remove cleanup code from 1.0 to 1.1 upgrade era (sdodson@redhat.com)
- Move repoquery_cmd fact setting into a more logical place.
  (dgoodwin@redhat.com)
- Add dependency on docker to openshift_docker role. (dgoodwin@redhat.com)
- Enable pullthrough by default in registry config for object storage.
  (abutcher@redhat.com)
- Fix gpg key path (sdodson@redhat.com)
- Use proper startswith. (dgoodwin@redhat.com)
- Sync latest image stream content (sdodson@redhat.com)
- Role dependency cleanup (abutcher@redhat.com)
- Fix up some broken markdown formatting (mostly tables) (tbielawa@redhat.com)
- Rename things to avoid conflicts with paas sig release rpms
  (sdodson@redhat.com)
- Remove/update TODOs. (dgoodwin@redhat.com)
- Remove all debug used during devel of openshift_version.
  (dgoodwin@redhat.com)
- Update quick upgrade to remove unsupported options. (dgoodwin@redhat.com)
- Don't special case origin on centos (sdodson@redhat.com)
- Various hosted component improvements (abutcher@redhat.com)
- Move repoquery fact definition to openshift_common. (dgoodwin@redhat.com)
- Clean up some deprecation warnings (tbielawa@redhat.com)
- Add CentOS PaaS SIG repos for RHEL (sdodson@redhat.com)
- Remove Origin 1.1 as an option (smunilla@redhat.com)
- Make /var/lib/origin mounted rslave (sdodson@redhat.com)
- fix "hapoxy" typo in loadbalancer playbook (Mathias.Merscher@dg-i.net)
- Fix dnf variant of rpm_versions.sh (sdodson@redhat.com)
- Make image stream munging optional (sdodson@redhat.com)
- Add aos-3.3 to tito releasers.conf (sdodson@redhat.com)
- Add symlinks for node templates. (dgoodwin@redhat.com)
- Fixes for Ansible 2.1. (dgoodwin@redhat.com)
- Update repoquery_cmd definitions to match latest in master.
  (dgoodwin@redhat.com)
- Fix unsafe bool usage. (dgoodwin@redhat.com)
- Fix typo in example inventories. (dgoodwin@redhat.com)
- Fixes for non-containerized separate etcd hosts. (dgoodwin@redhat.com)
- More docker upgrade fixes. (dgoodwin@redhat.com)
- Only nuke images when crossing the Docker 1.10 boundary in upgrade.
  (dgoodwin@redhat.com)
- Fix node/openvswitch containers not restarting after upgrade.
  (dgoodwin@redhat.com)
- Allow skipping Docker upgrade during OpenShift upgrade. (dgoodwin@redhat.com)
- a-o-i: Add Origin 1.2 Installs (smunilla@redhat.com)
- a-o-i: Add support for installing OpenShift Origin (smunilla@redhat.com)
- Refactor 3.2 upgrade to avoid killing nodes without evac.
  (dgoodwin@redhat.com)
- Update docker upgrade playbook to be more flexible. (dgoodwin@redhat.com)
- Add missing defaults file. (dgoodwin@redhat.com)
- Use common fact initialization include in upgrade. (dgoodwin@redhat.com)
- Fix use of v3.2 format for openshift_release in upgrade.
  (dgoodwin@redhat.com)
- Remove more legacy upgrade playbooks. (dgoodwin@redhat.com)
- Fix docker restarts during openshift_version role. (dgoodwin@redhat.com)
- Support setting a docker version in inventory. (dgoodwin@redhat.com)
- Fix version facts with trailing newline. (dgoodwin@redhat.com)
- Document the new and old version variables. (dgoodwin@redhat.com)
- Normalize some of the version inventory vars which users might mistakenly
  enter wrong. (dgoodwin@redhat.com)
- Check that detected version matches openshift_release in rpm installations.
  (dgoodwin@redhat.com)
- Block attempts to install origin without specifying any release info.
  (dgoodwin@redhat.com)
- More stable lookup of running openshift version. (dgoodwin@redhat.com)
- Upgrade fixes. (dgoodwin@redhat.com)
- Fix typo in facts. (dgoodwin@redhat.com)
- Cleanup, fix 3.1 version bug in facts. (dgoodwin@redhat.com)
- More version fixes. (dgoodwin@redhat.com)
- Support origin alpha tags. (dgoodwin@redhat.com)
- More stable containerized version lookup. (dgoodwin@redhat.com)
- Remove old upgrade playbooks. (dgoodwin@redhat.com)
- Fix performance hit in openshift_facts. (dgoodwin@redhat.com)
- Always populate openshift_image_tag and openshift_pkg_version.
  (dgoodwin@redhat.com)
- Remove the use of the upgrading variable. (dgoodwin@redhat.com)
- Don't be specific about rpm version to upgrade to for now.
  (dgoodwin@redhat.com)
- Restore 3.2 RPM version check before upgrading. (dgoodwin@redhat.com)
- Make openshift_version role docker dep conditional. (dgoodwin@redhat.com)
- Fix rpm installs. (dgoodwin@redhat.com)
- Temporary fix for upgrading issue. (dgoodwin@redhat.com)
- Remove unused docker facts tasks. (dgoodwin@redhat.com)
- Fix version unset bug, and set common ver fact on containerized nodes.
  (dgoodwin@redhat.com)
- Fix missing openshift.common.version fact on containerized nodes.
  (dgoodwin@redhat.com)
- Begin major simplification of 3.2 upgrade. (dgoodwin@redhat.com)
- Respect image tag/pkg version during upgrade. (dgoodwin@redhat.com)
- Force version to latest 3.2 during upgrade. (dgoodwin@redhat.com)
- Verify openshift_release is correct or absent in inventory before upgrade.
  (dgoodwin@redhat.com)
- Drop unused and broken "when" in vars section. (dgoodwin@redhat.com)
- Do not install rpm for version in openshift_version role.
  (dgoodwin@redhat.com)
- Fix bin/cluster libvirt related error (jdetiber@redhat.com)
- Update openshift_version author info. (dgoodwin@redhat.com)
- Fix installing release 3.1 not converting to precise version.
  (dgoodwin@redhat.com)
- Stop requiring/using first master version fact and use openshift_version var
  instead. (dgoodwin@redhat.com)
- Break version calc out into a role, separate yaml for containerized/rpm.
  (dgoodwin@redhat.com)
- Drop unnecessary node playbook version calculation. (dgoodwin@redhat.com)
- Add leading v for remaining IMAGE_VERSION templates. (dgoodwin@redhat.com)
- Fix error restarting master service that may not be there.
  (dgoodwin@redhat.com)
- Fix use of openshift_version in ca role. (dgoodwin@redhat.com)
- Fix image tag to rpm version filter. (dgoodwin@redhat.com)
- Fix error with containerized etcd install. (dgoodwin@redhat.com)
- Refactor openshift_version behavior. (dgoodwin@redhat.com)
- Protect installed version on subsequent masters. (dgoodwin@redhat.com)
- Get rpm installations functional again. (dgoodwin@redhat.com)
- Convert generic openshift_version=3.2 to specific early in install.
  (dgoodwin@redhat.com)
- Preserve node versions on re-run. (dgoodwin@redhat.com)
- Fix version compare with using just 3.2 or 1.2. (dgoodwin@redhat.com)
- Hookup node configuration. (dgoodwin@redhat.com)
- Complete installation of first master containerized. (dgoodwin@redhat.com)
- Stop downgrading Docker because we don't know what version to install yet.
  (dgoodwin@redhat.com)
- Work towards determining openshift_version when unspecified.
  (dgoodwin@redhat.com)
- Remove now unnecessary pull and ver check in openshift_docker role.
  (dgoodwin@redhat.com)
- Set openshift_version in config playbooks for first master.
  (dgoodwin@redhat.com)
- Debug output. (dgoodwin@redhat.com)
- cleanup broken symlinks - lookup_plugins filter_plugins (tdawson@redhat.com)
- Add libselinux-python as a dependency for the installation process
  (frederic.boulet@gmail.com)

* Tue Jul 05 2016 Scott Dodson <sdodson@redhat.com> 3.3.1-1
- Add v1.3 examples (sdodson@redhat.com)
- Change the examples content sync directory (sdodson@redhat.com)
- Add gte_3_3 (sdodson@redhat.com)
- Adds quotes to gpgkey element in byo/config.yml (smerrill@covermymeds.com)
- Restart dnsmasq encase it was already running (sdodson@redhat.com)
- Add support for supplying a dnsmasq.conf file (sdodson@redhat.com)
- Update image streams with SCL 2.2 components (sdodson@redhat.com)
- Bump rhel subscribe default version. (abutcher@redhat.com)
- Revert "Speed up copying OpenShift examples" (abutcher@afrolegs.com)
- Switch to repoquery, enable plugins for satellite support
  (sdodson@redhat.com)
- update conditional expression to save steps (lxia@redhat.com)
- Enable additional 'virt_sandbox_use_nfs' seboolean as per documentation:
  (george.goh@redhat.com)
- Set any_errors_fatal for initialize facts play. (abutcher@redhat.com)
- Set any_errors_fatal for etcd facts play. (abutcher@redhat.com)
- Speed up copying OpenShift examples (tbielawa@redhat.com)
- Check if last rule is DROP when inserting iptables rules.
  (abutcher@redhat.com)
- Don't upgrade docker on non-containerized etcd. (abutcher@redhat.com)
- Access embedded_etcd variable from oo_first_master hostvars.
  (abutcher@redhat.com)
- Add missing quote in metrics deployer template. (dgoodwin@redhat.com)
- Allow flag to uninstall playbook to preserve images. (dgoodwin@redhat.com)
- Add MODE to metrics deployer (sdodson@redhat.com)
- NetworkManager service never changes (tbielawa@redhat.com)
- Update the rest of the templates (sdodson@redhat.com)
- Update logging and metrics templates (sdodson@redhat.com)
- Block Docker 1.10 upgrade playbook when run against an Atomic OS.
  (dgoodwin@redhat.com)
- If registry_url != registry.access.redhat.com then modify image streams
  (sdodson@redhat.com)
- Add 30 second pause before retrying to start the node (sdodson@redhat.com)
- Stop dumping debug output, re-try startng the node once (sdodson@redhat.com)
- Fix uninstall.yml indentation for deamon-reload
  (florian.lambert@enovance.com)
- Fix no proxy hostnames during upgrade. (dgoodwin@redhat.com)
- Attempt to fix containerized node start failure with Docker 1.10.
  (dgoodwin@redhat.com)
- also volume-mount /etc/sysconfig/docker (tob@butter.sh)
- Separate uninstall plays by group. (abutcher@redhat.com)
- Add per-service environment variables. (abutcher@redhat.com)
- - Prevent the script to override n number of the time the same nameserver -
  Prevent the script to echo blank values from IP4_NAMESERVERS variable
  (william17.burton@gmail.com)
- Make a note about Requires: docker (sdodson@redhat.com)
- Remove Docker 1.10 requirement temporarily. (dgoodwin@redhat.com)
- Fix docker 1.10 upgrade on embedded etcd masters. (dgoodwin@redhat.com)
- Add lower case proxy variables (pascal.bach@siemens.com)
- default unit in openshift_facts (you@example.com)
- add unit in seconds for metrics resolution (you@example.com)

* Thu Jun 09 2016 Scott Dodson <sdodson@redhat.com> 3.3.0-1
- Restore mistakenly reverted code. (dgoodwin@redhat.com)
- Add openshift_loadbalancer_facts role to set lb facts prior to running
  dependencies. (abutcher@redhat.com)
- Bug 1338726 - never abort install if the latest version of docker is already
  installed (bleanhar@redhat.com)
- Preserve proxy config if it's undefined (sdodson@redhat.com)
- At least backup things (sdodson@redhat.com)
- Use unique play names to make things easier to debug (sdodson@redhat.com)
- Ansible 2.1 support. (abutcher@redhat.com)
- add skydns port 8053 to openstack master sec group (jawed.khelil@amadeus.com)
- fix dns openstack flavor instead of openshift flavor
  (jawed.khelil@amadeus.com)
- Fix Docker 1.10 problems with empty tags and trailing : (dgoodwin@redhat.com)
- ensure htpasswd file exists (tob@butter.sh)
- Docker 1.10 Upgrade (dgoodwin@redhat.com)
- Add flag to manage htpasswd, or not. (tob@butter.sh)

* Mon Jun 06 2016 Scott Dodson <sdodson@redhat.com> 3.0.97-1
- Only run node specific bits on nodes (sdodson@redhat.com)
- Update main.yaml (detiber@gmail.com)
- Hardcoded values in "launch_instances" - isue # 1970 (daniel@dumdan.com)
- XPAAS v1.3.1 content for Origin 1.1 / OSE 3.1 (sdodson@redhat.com)
- XPAAS v1.3.1 release for Origin 1.2 / OSE 3.2 (sdodson@redhat.com)
- Configure default docker logging options. (abutcher@redhat.com)
- Run rhel_subscribe on l_oo_all_hosts rather than all (sdodson@redhat.com)
- Fix error with stopping services that may not exist. (dgoodwin@redhat.com)
- Add haproxy_frontend_port to vars for openshift-loadbalancer.
  (abutcher@redhat.com)
- Move os_firewall_allow from defaults to role dependencies.
  (abutcher@redhat.com)
- Ensure registry url evaluated when creating router. (abutcher@redhat.com)
- Document protocol in readme aws. (abutcher@redhat.com)
- Revert openshift-certificates changes. (abutcher@redhat.com)
- wait metrics-deployer complete (need to configure nodes before hosted
  services) (you@example.com)
- switch to using sig release packages (jdetiber@redhat.com)
- temporarily disable gpg checking until we have a way to cleanly enable it
  (jdetiber@redhat.com)
- Switch to using CentOS SIG repos for Origin installs (jdetiber@redhat.com)
- Separate master and haproxy config playbooks. (abutcher@redhat.com)
- Cleanup bin, test and roles/openshift_ansible_inventory following move to
  openshift-tools (abutcher@redhat.com)
- Catch more uninstall targets (sdodson@redhat.com)
- Adding openshift_clock parameters to example inventory files
  (jstuever@redhat.com)
- Enable openshift_clock role for openshift_master, openshift_node, and
  openshift_etcd (jstuever@redhat.com)
- Add openshift_clock role to manage system clocks (jstuever@redhat.com)
- Allow clock role in openshift_facts (jstuever@redhat.com)
- Consolidate ca/master/node certificates roles into openshift_certificates.
  (abutcher@redhat.com)
- allow for overriding dns_flavor for openstack provider (jdetiber@redhat.com)
- add user-data file back to openstack provisioner (jdetiber@redhat.com)
- g_all_hosts with templated with_items causes errors with ansible 1.9.4 under
  some conditions (jdetiber@redhat.com)
- openstack_fixes (jdetiber@redhat.com)
- libvirt_fixes (jdetiber@redhat.com)
- gce fixes (jdetiber@redhat.com)
- aws provider fixes (jdetiber@redhat.com)
- Call evaluate_groups from update_repos_and_packages (jdetiber@redhat.com)

* Thu May 26 2016 Scott Dodson <sdodson@redhat.com> 3.0.94-1
- Use grep to decide when to add our comment (sdodson@redhat.com)

* Tue May 24 2016 Troy Dawson <tdawson@redhat.com> 3.0.93-1
- Fixup spec file (tdawson@redhat.com)

* Tue May 24 2016 Troy Dawson <tdawson@redhat.com> 3.0.92-1
-  Conditionally bind mount /usr/bin/docker-current when it is present (#1941)
  (sdodson@redhat.com)

* Tue May 24 2016 Troy Dawson <tdawson@redhat.com> 3.0.91-1
- Removed the echo line and replaced it with inline comment. To keep 99-origin-
  dns.sh from adding a new line in /etc/resolv.conf everytime the
  NetworkManager dispatcher script is executed. (jnordell@redhat.com)
- Extend multiple login provider check to include origin. (abutcher@redhat.com)
- Allow multiple login providers post 3.2. (abutcher@redhat.com)
- Make rhel_subscribe role able to subscribe for OSE 3.2 (lhuard@amadeus.com)
- Ensure yum-utils installed. (abutcher@redhat.com)
- Remove newline from docker_options template string. (abutcher@redhat.com)
- Use systemctl restart docker instead of ansible service.
  (dgoodwin@redhat.com)
- Use cluster hostname while generating certificate on the master nodes
  (vishal.patil@nuagenetworks.net)
- Fix playbooks/openshift-master/library move to symlink (sdodson@redhat.com)
- Task "Update router image to current version" failed, if router not in
  default namespace (jkroepke@users.noreply.github.com)
- docker-current was missing from the containerized atomic-openshift-
  node.service file (maci.stgn@gmail.com)
- fixed issue with blank spaces instead commas as variables template separators
  (j.david.nieto@gmail.com)
- Refactor where we compute no_proxy hostnames (sdodson@redhat.com)
- Fix for ansible v2 (sdodson@redhat.com)
- Fix rhel_subscribe (sdodson@redhat.com)
- remove interpolated g_all_hosts with_items arg from upgrade playbooks
  (cboggs@rallydev.com)
- Set openshift.common.hostname early in playbook execution.
  (abutcher@redhat.com)
- Fix 'recursive loop detected in template string' for upgrading variable.
  (abutcher@redhat.com)
- a-o-i: No proxy questions for 3.0/3.1 (smunilla@redhat.com)
- Fix minor upgrades in 3.1 (sdodson@redhat.com)
- Don't pull cli image when we're not containerized (sdodson@redhat.com)
- Check consumed pools prior to attaching. (abutcher@redhat.com)

* Mon May 16 2016 Troy Dawson <tdawson@redhat.com> 3.0.90-1
- Fixes for openshift_docker_hosted_registry_insecure var.
  (dgoodwin@redhat.com)
- Move latest to v1.2 (sdodson@redhat.com)
- Sync latest content (sdodson@redhat.com)
- Update default max-pods parameter (mwysocki@redhat.com)
- Allow overriding servingInfo.maxRequestsInFlight via
  openshift_master_max_requests_inflight. (abutcher@redhat.com)
- update logging and metrics deployer templates (lmeyer@redhat.com)
- Update default max-pods parameter (maci.stgn@gmail.com)
- Block upgrading w/ ansible v2. (abutcher@redhat.com)
- Fixed openvswitch not upgrading. (dgoodwin@redhat.com)
- Do not upgrade containers to latest avail during a normal config run.
  (dgoodwin@redhat.com)
- Update StringIO import for py2/3 compat. (abutcher@redhat.com)
- Fix mistaken quotes on proxy sysconfig variables. (dgoodwin@redhat.com)
- Sync comments with origin pr (sdodson@redhat.com)
- Use IP4_NAMESERVERS rather than DHCP4_DOMAIN_NAME_SERVERS
  (sdodson@redhat.com)
- Remove vars_files on play includes for upgrade playbooks.
  (abutcher@redhat.com)
- Document oauth token config inventory vars. (dgoodwin@redhat.com)
- Why is the node failing to start (sdodson@redhat.com)
- Move os_firewall out of openshift_common (sdodson@redhat.com)
- Remove old unused firewall rules (sdodson@redhat.com)
- Fix firewall rules (sdodson@redhat.com)
- Remove double evaluate_groups include. (abutcher@redhat.com)
- a-o-i: Write proxy variables (smunilla@redhat.com)
- Add support for Openstack based persistent volumes (sbaubeau@redhat.com)
- Fixes for flannel configuration. (abutcher@redhat.com)
- Initialize facts for all hosts. (abutcher@redhat.com)
- Fix version (sdodson@redhat.com)
- Fix cli_docker_additional_registries being erased during upgrade.
  (dgoodwin@redhat.com)
- Unmask atomic-openshift-master on uninstall (sdodson@redhat.com)
- Add *.retry to gitignore. (abutcher@redhat.com)
- Move modify_yaml up into top level library directory (sdodson@redhat.com)
- Enable dnsmasq on all hosts (sdodson@redhat.com)
- Fixed the credentials (vishal.patil@nuagenetworks.net)
- Remove vars_files on play includes for byo, scaleup and restart playbooks.
  (abutcher@redhat.com)
- Ensure ansible version greater than 1.9.4 (abutcher@redhat.com)
- Add oo_merge_hostvars filter for merging host & play variables.
  (abutcher@redhat.com)
- Replace hostvars with vars for openshift env facts when ansible >= v2.
  (abutcher@redhat.com)
- Add system:image-auditor role to ManageIQ SA (mtayer@redhat.com)
- Added extra install dependency on OSX (leenders.gert@gmail.com)
- Check and unmask iptables/firewalld. (abutcher@redhat.com)
- Default os_firewall_use_firewalld to false in os_firewall and remove
  overrides. (abutcher@redhat.com)
- listen on all interfaces (sdodson@redhat.com)
- Fix configuration of dns_ip (sdodson@redhat.com)
- Fix markdown in roles/openshift_metrics/README.md (cben@redhat.com)
- use stat module instead of shell module and ls to check for rpm-ostree
  (jdetiber@redhat.com)
-  fix openstack template (sjenning@redhat.com)
- Remove duplicate oauth_template fact. (abutcher@redhat.com)
- Cleanup various deprecation warnings. (abutcher@redhat.com)
- Make NetworkManager failure friendlier (sdodson@redhat.com)
- README Updates (detiber@gmail.com)
- Remove deprecated online playbooks/roles (jdetiber@redhat.com)
- fix up variable references remove "online" support from bin/cluster
  (jdetiber@redhat.com)
- Remove Ops specific ansible-tower aws playbooks (jdetiber@redhat.com)
- Fix inventory syntaxe (florian.lambert@enovance.com)
- Add openshift_docker_hosted_registry_insecure option (andrew@andrewklau.com)
- additional fixes (jdetiber@redhat.com)
- Fix templating issue with logging role (jdetiber@redhat.com)
- BuildDefaults are a kube admission controller not an openshift admission
  controller (sdodson@redhat.com)
- a-o-i: More friendly proxy questions (smunilla@redhat.com)
- update tenand_id typo in example file (jialiu@redhat.com)
- Update hosts.ose.example (jialiu@redhat.com)
- update tenand_id typo in example file (jialiu@redhat.com)
- Update repos per inventory before upgrading (sdodson@redhat.com)
- Fix openshift_generate_no_proxy_hosts boolean (sdodson@redhat.com)
- Fix openshift_generate_no_proxy_hosts examples (sdodson@redhat.com)
- Fix inventory properties with raw booleans, again... (dgoodwin@redhat.com)
- Allow containerized deployment of dns role (jprovazn@redhat.com)

* Mon May 09 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.89-1
- Use yum swap to downgrade docker (sdodson@redhat.com)

* Fri May 06 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.88-1
- Open port 53 whenever we're unsure of version (sdodson@redhat.com)
- Fix unsafe boolean handling on use_dnsmasq (sdodson@redhat.com)

* Wed Apr 27 2016 Troy Dawson <tdawson@redhat.com> 3.0.87-1
- a-o-i-: Allow empty proxy (smunilla@redhat.com)
- a-o-i: Populate groups for openshift_facts (smunilla@redhat.com)
- Replace sudo with become when accessing deployment_vars.
  (abutcher@redhat.com)
- Port lookup plugins to ansible v2. (abutcher@redhat.com)
- Add masterConfig.volumeConfig.dynamicProvisioningEnabled (sdodson@redhat.com)

* Tue Apr 26 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.86-1
- Don't set empty HTTP_PROXY, HTTPS_PROXY, NO_PROXY values (sdodson@redhat.com)
- a-o-i tests: Update attended tests for proxy (smunilla@redhat.com)
- Move portal_net from openshift_common to openshift_facts.
  (abutcher@redhat.com)
- Apply openshift_common to all masters prior to creating certificates for
  portal_net. (abutcher@redhat.com)
- Access portal_net in common facts. (abutcher@redhat.com)
- Add support for setting identity provider custom values (jdetiber@redhat.com)
- port filter_plugins to ansible2 (tob@butter.sh)
- a-o-i: Update prompt when asking for proxy (smunilla@redhat.com)
- a-o-i: UI additions for proxies (smunilla@redhat.com)

* Mon Apr 25 2016 Troy Dawson <tdawson@redhat.com> 3.0.85-1
- Fix backward compat for osm_default_subdomain (jdetiber@redhat.com)
- Replace deprecated sudo with become. (abutcher@redhat.com)
- Fix image version handling for v1.2.0-rc1 (sdodson@redhat.com)
- Pod must be recreated for the upgrade (bleanhar@redhat.com)
- openshift_etcd_facts should rely on openshift_facts not openshift_common
  (jdetiber@redhat.com)
- Sort and de-dupe no_proxy list (sdodson@redhat.com)
- openshift-metrics: adding duration and resolution options
  (efreiber@redhat.com)
- Changed service account creation to ansible (vishal.patil@nuagenetworks.net)
- As per https://github.com/openshift/openshift-
  ansible/issues/1795#issuecomment-213873564, renamed openshift_node_dnsmasq to
  openshift_use_dnsmasq where applicable. Fixes 1795 (donovan@switchbit.io)
- Add global proxy configuration (sdodson@redhat.com)
- remove duplicate register: (tob@butter.sh)

* Fri Apr 22 2016 Troy Dawson <tdawson@redhat.com> 3.0.84-1
- Fix for docker not present (jdetiber@redhat.com)
- Reconcile roles in additive-only mode on upgrade (jliggitt@redhat.com)
- Set etcd_hostname and etcd_ip for masters w/ external etcd.
  (abutcher@redhat.com)

* Thu Apr 21 2016 Troy Dawson <tdawson@redhat.com> 3.0.83-1
- a-o-i: Correct bug with default storage host (smunilla@redhat.com)
- Only add new sccs (bleanhar@redhat.com)
- Fix bug after portal_net move from master to common role.
  (dgoodwin@redhat.com)
- Sync latest content (sdodson@redhat.com)
- Use xpaas 1.3.0-1, use enterprise content for metrics (sdodson@redhat.com)
- Support configurable admin user and password for the enterprise Prefix
  changes for admin and password with nuage_master (abhat@nuagenetworks.net)

* Wed Apr 20 2016 Troy Dawson <tdawson@redhat.com> 3.0.82-1
- Use a JSON list for docker log options. (dgoodwin@redhat.com)
- Fix legacy cli_docker_* vars not migrating. (dgoodwin@redhat.com)
- Fix use of older image tag version during upgrade. (dgoodwin@redhat.com)
- Remove etcd_interface variable. Remove openshift_docker dependency from the
  etcd role. (abutcher@redhat.com)
- Use openshift_hostname/openshift_ip values for etcd configuration and
  certificates. (abutcher@redhat.com)
- added new openshift-metrics service (j.david.nieto@gmail.com)
- Translate legacy facts within the oo_openshift_env filter.
  (abutcher@redhat.com)
- Remove empty facts from nested dictionaries. (abutcher@redhat.com)
- Fix router selector fact migration and match multiple selectors when counting
  nodes. (abutcher@redhat.com)
- Fixing the spec for PR 1734 (bleanhar@redhat.com)
- Add openshift_use_dnsmasq (sdodson@redhat.com)
- Promote portal_net to openshift.common, add kube_svc_ip (sdodson@redhat.com)
- Add example inventories to docs, install docs by default (sdodson@redhat.com)
- Fix use of JSON inventory vars with raw booleans. (dgoodwin@redhat.com)
- cleanup roles after roles move to openshift-tools (jdiaz@redhat.com)
- Reference Setup for Origin and Ose from up-to-date docs.openshift.[com|org]
  instead of local README_[origin|OSE].md (jchaloup@redhat.com)

* Mon Apr 18 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.81-1
- IMAGE_PREFIX=openshift3/ for enterprise logging/metrics (sdodson@redhat.com)
- a-o-i: Don't assume storage on 1st master (smunilla@redhat.com)
- Bug 1320829 - Handle OSE 3.0 installs (bleanhar@redhat.com)

* Fri Apr 15 2016 Troy Dawson <tdawson@redhat.com> 3.0.80-1
- Refactor docker failed state cleanup (sdodson@redhat.com)
- Support mixed RPM/container installs (bleanhar@redhat.com)
- The openshift_docker role must set the version facts for containerized
  installs (bleanhar@redhat.com)
- start it, check for failure, reset it, start again (sdodson@redhat.com)
- Enable docker before potentially resetting the failure (sdodson@redhat.com)
- Fix mappingMethod option in identity provider. (abutcher@redhat.com)
- Support setting imagePolicyConfig JSON in inventory. (dgoodwin@redhat.com)

* Tue Apr 12 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.79-1
- Bug 1324728 - Ansible should not downgrade docker when installing 3.2
  containerized env (bleanhar@redhat.com)
- Fixing non-HA master restart conditional (bleanhar@redhat.com)
- Fetching the current version a little more carefully (bleanhar@redhat.com)
- Make sure Docker is restarted after we have correctly configured the
  containerized systemd units (bleanhar@redhat.com)
- use RestartSec to avoid default rate limit in systemd (bleanhar@redhat.com)
- Convert image_tag on masters (smunilla@redhat.com)
- Installs and upgrades from authenticated registries are not supported for now
  (bleanhar@redhat.com)
- Handle cases where the pacemaker variables aren't set (bleanhar@redhat.com)
- Containerized installs on RHEL were downgrading docker unnecessarily
  (bleanhar@redhat.com)

* Tue Apr 12 2016 Troy Dawson <tdawson@redhat.com> 3.0.78-1
- Add support for creating secure router. (abutcher@redhat.com)

* Mon Apr 11 2016 Troy Dawson <tdawson@redhat.com> 3.0.77-1
- Fix a docker-storage sysconfig bug. (dgoodwin@redhat.com)
- update bootstrap-fedora to include python2-firewall for F24+
  (maxamillion@fedoraproject.org)
- Merge openshift_env hostvars. (abutcher@redhat.com)
- Add openshift_hosted_facts role and remove hosted facts from
  openshift_common. (abutcher@redhat.com)

* Fri Apr 08 2016 Troy Dawson <tdawson@redhat.com> 3.0.76-1
- a-o-i: Support openshift_image_tag (smunilla@redhat.com)
- Bug 1324729 - Import xPaas image streams failed during 3.2 installation
  (bleanhar@redhat.com)
- Test docker_version_result.stdout when determining if docker should be
  installed/downgraded. (abutcher@redhat.com)

* Thu Apr 07 2016 Troy Dawson <tdawson@redhat.com> 3.0.75-1
- First attempt at oadm router module (kwoodson@redhat.com)
- Remove openshift_common dep from openshift_storage_nfs (abutcher@redhat.com)
- Add cloudprovider config dir to docker options. (abutcher@redhat.com)
- Check for kind in cloudprovider facts prior to accessing.
  (abutcher@redhat.com)

* Wed Apr 06 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.74-1
- Add support for configuring oauth templates. (dgoodwin@redhat.com)
- Add support for templating master admissionConfig. (dgoodwin@redhat.com)

* Wed Apr 06 2016 Troy Dawson <tdawson@redhat.com> 3.0.73-1
- Replace unused Dockerfile with one used for official builds.
  (dgoodwin@redhat.com)
- Update for zbx_user refresh (kwoodson@redhat.com)
- Docker 1.9 is actually cool starting in origin 1.1.4 (sdodson@redhat.com)
- Unmask services (bleanhar@redhat.com)
- XPAAS v1.3 for OSE 3.2 (sdodson@redhat.com)
- XPAAS 1.3 content for OSE 3.1 (sdodson@redhat.com)
- Bug 1322788 - The IMAGE_VERSION wasn't added to atomic-openshift-master-api
  and atomic-openshift-master-controllers (bleanhar@redhat.com)
- Bug 1323123 - upgrade failed to containerized OSE on RHEL Host without ose3.2
  repo (bleanhar@redhat.com)
- Write inventory to same directory as quick install config.
  (dgoodwin@redhat.com)
- Add --gen-inventory command to atomic-openshift-installer.
  (dgoodwin@redhat.com)

* Tue Apr 05 2016 Troy Dawson <tdawson@redhat.com> 3.0.72-1
- when docker is installed, make it 1.8.2 to avoid issues (mwoodson@redhat.com)
- Downgrade to docker 1.8.2 if installing OSE < 3.2 (sdodson@redhat.com)
- Pacemaker is unsupported for 3.2 (bleanhar@redhat.com)
- Fixing regexp.  Periods are no longer allowed (kwoodson@redhat.com)
- We require docker 1.9 for the 3.2 upgrade (bleanhar@redhat.com)

* Mon Apr 04 2016 Troy Dawson <tdawson@redhat.com> 3.0.71-1
- Fixed oc_edit by requiring name and content (kwoodson@redhat.com)
- add higher severity trigger if no heartbeat for 1 hour (jdiaz@redhat.com)
- Yedit enhancements (kwoodson@redhat.com)

* Fri Apr 01 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.70-1
- Enable Ansible ssh pipelining to speedup deployment (lhuard@amadeus.com)
- Allow for overriding scheduler config (jdetiber@redhat.com)
- a-o-i: Add 3.2 to list of supported versions (smunilla@redhat.com)
- a-o-i: Support for unattended upgrades (smunilla@redhat.com)
- a-o-i: More flexible upgrade mappings (smunilla@redhat.com)
- a-o-i: OSE/AEP 3.2 product option (smunilla@redhat.com)
- a-o-i: Error out early if callback_facts is None (smunilla@redhat.com)

* Thu Mar 31 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.69-1
- Bug 1320829 - Ensure docker installed for facts (jdetiber@redhat.com)
- Bug 1322788 - The IMAGE_VERSION wasn't added to atomic-openshift-master-api
  and atomic-openshift-master-controllers (bleanhar@redhat.com)
- Fixed generate header. (kwoodson@redhat.com)
- Bug 1322335 - The package name is wrong for rpm upgrade (bleanhar@redhat.com)
- Add AWS cloud provider support. (abutcher@redhat.com)

* Wed Mar 30 2016 Troy Dawson <tdawson@redhat.com> 3.0.68-1
- Moving generation of ansible module side by side with module.
  (kwoodson@redhat.com)
- Bug 1322338 - The upgrade should keep the option insecure-
  registry=172.30.0.0/16 (bleanhar@redhat.com)

* Tue Mar 29 2016 Troy Dawson <tdawson@redhat.com> 3.0.67-1
- The systemd unit for atomic-openshift-master wasn't not being created
  (bleanhar@redhat.com)
- Use openshift.master.ha instead of duplicating the logic
  (bleanhar@redhat.com)
- Workaround for authenticated registries (bleanhar@redhat.com)
- First pass at systemd unit refactor (bleanhar@redhat.com)
- fix the key name for the dynamic item of avalable (zhizhang@zhizhang-laptop-
  nay.redhat.com)
- make docker service want ose containerized services (sjenning@redhat.com)

* Mon Mar 28 2016 Troy Dawson <tdawson@redhat.com> 3.0.66-1
- Fixed error message to add valid yaml (kwoodson@redhat.com)
- added admin binary varibale usage as well as specifying kubeconfig copy to be
  used (jkwiatko@redhat.com)
- Sync latest db-templates and qucikstart-templates (sdodson@redhat.com)
- adding playbook (jkwiatko@redhat.com)
- Tested of refactored code (jkwiatko@redhat.com)
- fix some typo (zhizhang@use-tower1.ops.rhcloud.com)
- add the total and available space item (zhizhang@use-tower1.ops.rhcloud.com)
- add dynamic pv count (zhizhang@use-tower1.ops.rhcloud.com)
- revised and restructured logging role (jkwiatko@redhat.com)
- Adding openshift_efk role (jkwiatko@redhat.com)
- Attempt to fix error validating when extraScopes and extraAuthorizeParameters
  are not present (jdetiber@redhat.com)

* Thu Mar 24 2016 Troy Dawson <tdawson@redhat.com> 3.0.65-1
- Adding deployment config and refactored. (kwoodson@redhat.com)
- ManageIQ SA: Adding image-puller role (efreiber@redhat.com)

* Wed Mar 23 2016 Troy Dawson <tdawson@redhat.com> 3.0.64-1
- Latest cli updates from generated files (kwoodson@redhat.com)
- Add /dev to node containers (sdodson@redhat.com)
- Fix indention (whearn@redhat.com)
- Support setting local storage perFSGroup quota in node config.
  (dgoodwin@redhat.com)
- Fix line break (whearn@redhat.com)
- Lock down permissions on named certificates (elyscape@gmail.com)
- Add namespace flag to oc create (whearn@redhat.com)

* Mon Mar 21 2016 Kenny Woodson <kwoodson@redhat.com> 3.0.63-1
- Modified group selectors for muliple clusters per account
  (kwoodson@redhat.com)

* Fri Mar 18 2016 Troy Dawson <tdawson@redhat.com> 3.0.62-1
- Yaml editor first attempt (kwoodson@redhat.com)
- libvirt cluster variables cleanup (pep@redhat.com)

* Thu Mar 17 2016 Troy Dawson <tdawson@redhat.com> 3.0.61-1
- Bug 1317755 - Set insecure-registry for internal registry by default
  (jdetiber@redhat.com)

* Wed Mar 16 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.60-1
- Fall back to deployment_type in openshift_facts. (abutcher@redhat.com)
- Fixing undefined variable check (kwoodson@redhat.com)
- Fix path to cacert on /healthz/ready check (sdodson@redhat.com)
- Load environment files in containerized installs (sdodson@redhat.com)
- change type to value_type (zhizhang@zhizhang-laptop-nay.redhat.com)
- change time from int to float (zhizhang@zhizhang-laptop-nay.redhat.com)
- change the check time from 1 hour to 2 hour (zhizhang@zhizhang-laptop-
  nay.redhat.com)
- add item of time cost a app build and app create (zhizhang@zhizhang-laptop-
  nay.redhat.com)
- add trigger for app creation with build process (zhizhang@zhizhang-laptop-
  nay.redhat.com)
- add key of openshift.master.app.build.create (zhizhang@zhizhang-laptop-
  nay.redhat.com)

* Wed Mar 16 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.59-1
- Only mask etcd service for containerized installls when it's installed
  (sdodson@redhat.com)
- Provide cacert when performing health checks (abutcher@redhat.com)

* Tue Mar 15 2016 Kenny Woodson <kwoodson@redhat.com> 3.0.58-1
- Group selector feature added (kwoodson@redhat.com)
- nfs: replace yum with dnf (efreiber@redhat.com)
- Move common common facts to openshift_facts (jdetiber@redhat.com)
- perform oc client config tasks only once when ansible_ssh_user is root
  (jdetiber@redhat.com)
- OSE/Origin < 3.2/1.2 should not get Docker 1.9 (sdodson@redhat.com)

* Mon Mar 14 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.57-1
- Docker stderr can break this script if ansible executes it remotely
  (bleanhar@redhat.com)
- Handle HA master case (bleanhar@redhat.com)
- Bug 1315564 - Containerized installs require a running environment
  (bleanhar@redhat.com)
- Updating the docker registry variables to use the new name
  (bleanhar@redhat.com)
- Bug 1316761 - Skip the available version check if openshift_image_tag is
  defined. (bleanhar@redhat.com)
- Ansible module to manage secrets for openshift api (kwoodson@redhat.com)

* Mon Mar 14 2016 Kenny Woodson <kwoodson@redhat.com> 3.0.56-1
- Updating our metadata tooling to work without env (kwoodson@redhat.com)
- improve ordering of systemd units (jdetiber@redhat.com)
- Docker role refactor (jdetiber@redhat.com)
- Ensure is_containerized is cast as bool. (abutcher@redhat.com)
- Sync latest to v1.2 (sdodson@redhat.com)
- Sync with latest image stream and templates (sdodson@redhat.com)
- Allow origin version to be passed in as an argument (sdodson@redhat.com)
- Add support for Openstack integration (sbaubeau@redhat.com)
- Expose log level on the monitor (abhat@nuagenetworks.net)
- openshift_facts: Safe cast additional bools (smunilla@redhat.com)
- openshift-ansible: Wrap boolean facts (smunilla@redhat.com)
- fixed copr releasers file (twiest@redhat.com)
- Libvirt provider fixes (jdetiber@redhat.com)
- Support log level configuration for plugin (abhat@nuagenetworks.net)

* Wed Mar 09 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.55-1
- Bug 1315564 - upgrade to ose3.2 failed on Atomic Hosts (bleanhar@redhat.com)
- Bug 1315563 - Upgrade failed to containerized install OSE 3.1 on RHEL
  (bleanhar@redhat.com)
- a-o-i: Fix NFS storage tests (smunilla@redhat.com)
- First attempt at NFS setup (smunilla@redhat.com)
- reverting back to pre-pulling the master image (bleanhar@redhat.com)
- Use /healthz/ready when verifying api (abutcher@redhat.com)
- Formatting error (Viet.atx@gmail.com)
- Introduce origin-metrics playbook (vnguyen@redhat.com)

* Tue Mar 08 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.54-1
- Bug 1315563 - stdout IO redirection wasn't working as expected over SSH
  connections (bleanhar@redhat.com)
- Bug 1315637 - The docker wasn't upgraded on node during upgrade
  (bleanhar@redhat.com)
- Bug 1315564 - upgrade to ose3.2 failed on Atomic Hosts (bleanhar@redhat.com)
- Fix issue when there are no infra nodes (lhuard@amadeus.com)
- Stop the etcd container during uninstall (bleanhar@redhat.com)

* Mon Mar 07 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.53-1
- Don't enable cockpit-ws for containerized installs (bleanhar@redhat.com)
- Support openshift_image_tag (bleanhar@redhat.com)
- Set g_new_master_hosts in upgrade playbooks. (abutcher@redhat.com)
- Add setting for configuring nofile limit for haproxy (jdetiber@redhat.com)

* Mon Mar 07 2016 Joel Diaz <jdiaz@redhat.com> 3.0.52-1
- fixed monitoring containers to restart (sten@redhat.com)
- Lock down generated certs dir (sdodson@redhat.com)
- package up lib_zabbix into its own subpackage (jdiaz@redhat.com)

* Fri Mar 04 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.51-1
- Bug 1314645 - Upgrade failed with "One or more undefined variables 'dict
  object' has no attribute 'stdout'" (bleanhar@redhat.com)
- EBS storage does not support Recycle (sedgar@redhat.com)
- Remove cockpit and kubernetes-client packages in uninstall playbook.
  (abutcher@redhat.com)
- Update README_origin.md (trond.hapnes@gmail.com)
- Add cockpit-docker package by default (nakayamakenjiro@gmail.com)

* Thu Mar 03 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.50-1
- change lib_zabbix's import to new pathing (jdiaz@redhat.com)
- upgrade README fixes (bleanhar@redhat.com)
- A few images weren't being uninstalled (bleanhar@redhat.com)
- Adding support for v1.2 examples (bleanhar@redhat.com)
- Adding templates for v1.2 (bleanhar@redhat.com)
- Adding verify_upgrade_version variable for upgrade debugging
  (bleanhar@redhat.com)
- Correctly set the image tag for containerized installs (and upgrades)
  (bleanhar@redhat.com)
- Adding newly required variable (bleanhar@redhat.com)
- Updating the containerized cli wrapper to work for both docker 1.8 and 1.9
  (bleanhar@redhat.com)
- uninstall the QE images (bleanhar@redhat.com)
- First past at the upgrade process (bleanhar@redhat.com)
- Check for is_containerized value when setting binary locations.
  (abutcher@redhat.com)
- Bug 1313169 - Ansible installer tries to enable etcd_container service even
  though containerized=false (bleanhar@redhat.com)
- Fix logging infra template version mismatch. (dgoodwin@redhat.com)
- Changes required for Nuage monitor REST server
  (vishal.patil@nuagenetworks.net)
- disable http-server-close option (jdetiber@redhat.com)
- change [HEAL] to [Heal] to match with v2 (jdiaz@redhat.com)
- Increase maxconn settings for haproxy lb (jdetiber@redhat.com)

* Tue Mar 01 2016 Matt Woodson <mwoodson@redhat.com> 3.0.49-1
- fixed error in awsutil.py (mwoodson@redhat.com)

* Tue Mar 01 2016 Matt Woodson <mwoodson@redhat.com> 3.0.48-1
- ohi: added subtype searching (mwoodson@redhat.com)
- make heal remote actions generic for all [HEAL] triggers (jdiaz@redhat.com)
- added extra steps to ensure docker starts up (mwoodson@redhat.com)
- role_removal: docker_storage;  This is the old way, no longer used
  (mwoodson@redhat.com)
- role: added docker_storage_setup (mwoodson@redhat.com)
- Use inventory_hostname for openshift master certs to sync.
  (abutcher@redhat.com)
- Adding a symlink to making loading the examples more convenient
  (bleanhar@redhat.com)
- docs: Explain a bit more how to expand Atomic Host rootfs
  (walters@verbum.org)
- a-o-i: Rename osm_default_subdomain (smunilla@redhat.com)
- Updating tito config for OSE 3.2 (bleanhar@redhat.com)
- Synchronize master kube configs (abutcher@redhat.com)
- added os_utils, os_reboot_server role; removed containerization stuff from
  the updated (mwoodson@redhat.com)
- Add warnings to bin/cluster and READMEs (abutcher@redhat.com)
- Add host subnet length example. (abutcher@redhat.com)
- Upgrade -1510 to CentOS-7-x86_64-GenericCloud-1602. (cben@redhat.com)
- Pin down CentOS-7-x86_64-GenericCloud-1510.qcow2.xz version, which the
  checksum currently expects (#1384). (cben@redhat.com)
- Change is_atomic to is_containerized (florian.lambert@enovance.com)
- Rename variable to openshift_master_default_subdomain with backwards
  compatibility. (jstuever@redhat.com)
- lib_dyn: more updates to the lib_dyn module. Made the TTL more flexible
  (mwoodson@redhat.com)
- remote heal action for OVS down (jdiaz@redhat.com)
- Pass registry claim to openshift_registry. (abutcher@redhat.com)
- Refactor - increase retries instead of delay in "Wait for Node Registration"
  (david.mat@archimiddle.com)
- Better diagnostic messages when an OpenStack heat stack creation fails
  (lhuard@amadeus.com)
- made some changes to lib_dyn update (mwoodson@redhat.com)
- Increase timeout on Wait for Node Registration (david.mat@archimiddle.com)
- Fix typo in oscp (agrimm@redhat.com)
- Add correct parsing of ec2_security_groups env variable
  (david.mat@archimiddle.com)
- changed oso_host_monitoring to use the oo_ vars (twiest@redhat.com)
- Add quotes around src argument to support paths with spaces
  (david.mat@archimiddle.com)
- Add missing is_atomic condition on upgrade package
  (florian.lambert@enovance.com)
- configure debug_level for master and node from cli (jawed.khelil@amadeus.com)
- remove version requirement from etcd, shouldn't be needed anymore
  (maxamillion@fedoraproject.org)
- Add ansible.cfg to .gitignore (jdetiber@redhat.com)
- added node-secgroup to master_nodes (j.david.nieto@gmail.com)
- Document setting the VPC subnet (puiterwijk@redhat.com)
- Update the AMIs used in README_AWS (puiterwijk@redhat.com)
- Add byo examples for network cidr and api/console ports.
  (abutcher@redhat.com)
- Add openshift_docker roles to master/node scaleup. (abutcher@redhat.com)
- Fail when master.master_count descreases or master.ha changes.
  (abutcher@redhat.com)
- Protected facts. (abutcher@redhat.com)
- Add modify_yaml module. (abutcher@redhat.com)
- Re-arrange scaleup playbooks. (abutcher@redhat.com)
- Move additional master configuration into a separate master playbook.
  (abutcher@redhat.com)
- Generate each master's certificates separately. (abutcher@redhat.com)
- Add new_masters to scaleup playbook. (abutcher@redhat.com)

* Wed Feb 24 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.47-1
- a-o-i: Double safety check on master_lb (smunilla@redhat.com)
- a-o-i: Better method for identifying master_lb (smunilla@redhat.com)

* Tue Feb 23 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.46-1
- a-o-i: Exception checking around master_lb (smunilla@redhat.com)

* Mon Feb 22 2016 Brenton Leanhardt <bleanhar@redhat.com> 3.0.45-1
- Do not monitor for etcd watchers (mmahut@redhat.com)
- remove old master registry item/triggers (jdiaz@redhat.com)
- a-o-i: Redo logic for detecting master_lb (smunilla@redhat.com)
- Fix 1.2 version check (jdetiber@redhat.com)
- Fix pv/c creation failed_when. (abutcher@redhat.com)
- Rename variable to delete temporary file, add configurable path.
  (hrosnet@redhat.com)
- Add /var/log to containerized node mounts (sdodson@redhat.com)
- Add extra parameters for S3 registry: delete file, create bucket.
  (hrosnet@redhat.com)
- Don't make config files world readable (sdodson@redhat.com)
- Fix requiring state and providing a default (rharriso@redhat.com)
- bind in /etc/origin/node for non-master monitoring to be able to talk with
  master (jdiaz@redhat.com)
- a-o-i: pylint fixes related to too-long lines (smunilla@redhat.com)

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
