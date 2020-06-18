# %commit is intended to be set by tito custom builders provided
# in the .tito/lib directory. The values in this spec file will not be kept up to date.
%{!?commit:
%global commit c64d09e528ca433832c6b6e6f5c7734a9cc8ee6f
}
# This is inserted to prevent RPM from requiring "/usr/bin/ansible-playbook"
# The ansible-playbook requirement will be provided by the explicit
#  "Requires: ansible" directive
%global __requires_exclude ^/usr/bin/ansible-playbook$

Name:           openshift-ansible
Version:        4.1.0
Release:        0.0.0%{?dist}
Summary:        Openshift and Atomic Enterprise Ansible
License:        ASL 2.0
URL:            https://github.com/openshift/openshift-ansible
Source0:        https://github.com/openshift/openshift-ansible/archive/%{commit}/%{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:      ansible >= 2.9.5
Requires:      openshift-clients
Requires:      openssl

%description
OpenShift RHEL Worker Management Ansible Playbooks

%prep
%setup -q

%build

%install
# Base openshift-ansible install
mkdir -p %{buildroot}%{_datadir}/%{name}
mkdir -p %{buildroot}%{_datadir}/ansible/%{name}/inventory
cp -rp inventory/dynamic %{buildroot}%{_datadir}/ansible/%{name}/inventory
cp ansible.cfg %{buildroot}%{_datadir}/ansible/%{name}/ansible.cfg

# Install example inventory into docs/examples
mkdir -p docs/example-inventories
cp inventory/hosts.* inventory/README.md docs/example-inventories/

cp -rp playbooks %{buildroot}%{_datadir}/ansible/%{name}/
cp -rp roles %{buildroot}%{_datadir}/ansible/%{name}/
cp -rp test %{buildroot}%{_datadir}/ansible/%{name}/

# Base openshift-ansible files
%files
%doc README*
%license LICENSE
%dir %{_datadir}/ansible/%{name}
%{_datadir}/ansible/%{name}/inventory
%{_datadir}/ansible/%{name}/ansible.cfg
%doc  docs
%{_datadir}/ansible/%{name}/playbooks
%{_datadir}/ansible/%{name}/roles

# ----------------------------------------------------------------------------------
# openshift-ansible-tests subpackage
# ----------------------------------------------------------------------------------
%package test
Summary:       Openshift and Atomic Enterprise Ansible Test Playbooks
Requires:      %{name} = %{version}-%{release}
Requires:      ansible >= 2.9.5
Requires:      openssh-clients
BuildArch:     noarch

%description test
%{summary}.

%files test
%{_datadir}/ansible/%{name}/test

%changelog
