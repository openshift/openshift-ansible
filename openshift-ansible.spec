# %commit is intended to be set by tito custom builders provided
# in the .tito/lib directory. The values in this spec file will not be kept up to date.
%{!?commit:
%global commit c64d09e528ca433832c6b6e6f5c7734a9cc8ee6f
}

Name:           openshift-ansible
Version:        3.0.3
Release:        1%{?dist}
Summary:        Openshift and Atomic Enterprise Ansible
License:        ASL 2.0
URL:            https://github.com/openshift/openshift-ansible
Source0:        https://github.com/openshift/openshift-ansible/archive/%{commit}/%{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:      ansible

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
rm -f %{buildroot}%{python_sitelib}/openshift_ansible/multi_ec2.py
rm -f %{buildroot}%{python_sitelib}/openshift_ansible/aws
ln -sf %{_datadir}/ansible/inventory/multi_ec2.py %{buildroot}%{python_sitelib}/openshift_ansible/multi_ec2.py
ln -sf %{_datadir}/ansible/inventory/aws %{buildroot}%{python_sitelib}/openshift_ansible/aws

# openshift-ansible-docs install
# -docs are currently just %doc, no install needed

# openshift-ansible-inventory install
mkdir -p %{buildroot}/etc/ansible
mkdir -p %{buildroot}%{_datadir}/ansible/inventory
mkdir -p %{buildroot}%{_datadir}/ansible/inventory/aws
mkdir -p %{buildroot}%{_datadir}/ansible/inventory/gce
cp -p inventory/multi_ec2.py %{buildroot}%{_datadir}/ansible/inventory
cp -p inventory/multi_ec2.yaml.example %{buildroot}/etc/ansible/multi_ec2.yaml
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
Requires:      %{name}-inventory
Requires:      python2
BuildRequires: python2-devel
BuildArch:     noarch

%description bin
Scripts to make it nicer when working with hosts that are defined only by metadata.

%files bin
%{_bindir}/*
%{python_sitelib}/openshift_ansible/
/etc/bash_completion.d/*
%config(noreplace) /etc/openshift_ansible/


# ----------------------------------------------------------------------------------
# openshift-ansible-docs subpackage
# ----------------------------------------------------------------------------------
%package docs
Summary:       Openshift and Atomic Enterprise Ansible documents
Requires:      %{name}
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
Requires:      python2
BuildArch:     noarch

%description inventory
Ansible Inventories used with the openshift-ansible scripts and playbooks.

%files inventory
%config(noreplace) /etc/ansible/*
%dir %{_datadir}/ansible/inventory
%{_datadir}/ansible/inventory/multi_ec2.py*
%{_datadir}/ansible/inventory/aws/ec2.py*
%{_datadir}/ansible/inventory/gce/gce.py*


# ----------------------------------------------------------------------------------
# openshift-ansible-playbooks subpackage
# ----------------------------------------------------------------------------------
%package playbooks
Summary:       Openshift and Atomic Enterprise Ansible Playbooks
Requires:      %{name}
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
Requires:      ansible
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


%changelog
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

