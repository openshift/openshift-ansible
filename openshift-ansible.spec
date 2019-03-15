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
Version:        4.1.0
Release:        0.0.0%{?dist}
Summary:        Openshift and Atomic Enterprise Ansible
License:        ASL 2.0
URL:            https://github.com/openshift/openshift-ansible
Source0:        https://github.com/openshift/openshift-ansible/archive/%{commit}/%{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:      ansible >= 2.7.8
Requires:      python2
Requires:      python-six
Requires:      tar
Requires:      %{name}-docs = %{version}-%{release}
Requires:      %{name}-playbooks = %{version}-%{release}
Requires:      %{name}-roles = %{version}-%{release}
Obsoletes:     atomic-openshift-utils <= 3.10
Requires:      libselinux-python
Requires:      pyOpenSSL
Requires:      python2-openshift

%description
Openshift and Atomic Enterprise Ansible

This repo contains Ansible code and playbooks
for Openshift and Atomic Enterprise.

%prep
%setup -q

%build

%install
# Base openshift-ansible install
mkdir -p %{buildroot}%{_datadir}/%{name}
mkdir -p %{buildroot}%{_datadir}/ansible/%{name}/inventory
cp -rp inventory/dynamic %{buildroot}%{_datadir}/ansible/%{name}/inventory
cp ansible.cfg %{buildroot}%{_datadir}/ansible/%{name}/ansible.cfg

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
cp inventory/hosts.* inventory/README.md docs/example-inventories/

# openshift-ansible-playbooks install
cp -rp playbooks %{buildroot}%{_datadir}/ansible/%{name}/
cp -rp test %{buildroot}%{_datadir}/ansible/%{name}/

# BZ1330091
find -L %{buildroot}%{_datadir}/ansible/%{name}/playbooks -name lookup_plugins -type l -delete
find -L %{buildroot}%{_datadir}/ansible/%{name}/playbooks -name filter_plugins -type l -delete

# openshift-ansible-roles install
cp -rp roles %{buildroot}%{_datadir}/ansible/%{name}/

# Base openshift-ansible files
%files
%doc README*
%license LICENSE
%dir %{_datadir}/ansible/%{name}
%{_datadir}/ansible/%{name}/inventory
%{_datadir}/ansible/%{name}/ansible.cfg

# ----------------------------------------------------------------------------------
# openshift-ansible-docs subpackage
# ----------------------------------------------------------------------------------
%package docs
Summary:       Openshift and Atomic Enterprise Ansible documents
Requires:      %{name} = %{version}-%{release}
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
Requires:      %{name} = %{version}-%{release}
Requires:      %{name}-roles = %{version}-%{release}
BuildArch:     noarch

%description playbooks
%{summary}.

%files playbooks
%{_datadir}/ansible/%{name}/playbooks

# Along the history of openshift-ansible, some playbook directories had to be
# moved and were replaced with symlinks for backwards compatibility.
# RPM doesn't handle this so we have to do some pre-transaction magic.
# See https://fedoraproject.org/wiki/Packaging:Directory_Replacement
%pretrans playbooks -p <lua>
-- Define the paths to directories being replaced below.
-- DO NOT add a trailing slash at the end.
dirs_to_sym = {
    "/usr/share/ansible/openshift-ansible/playbooks/common/openshift-master/library",
    "/usr/share/ansible/openshift-ansible/playbooks/certificate_expiry"
}
for i,path in ipairs(dirs_to_sym) do
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
end

%package roles
# ----------------------------------------------------------------------------------
# openshift-ansible-roles subpackage
# ----------------------------------------------------------------------------------
Summary:       Openshift and Atomic Enterprise Ansible roles
Requires:      %{name} = %{version}-%{release}
Obsoletes:      %{name}-lookup-plugins
Obsoletes:      %{name}-filter-plugins
Obsoletes:      %{name}-callback-plugins
BuildArch:     noarch

%description roles
%{summary}.

%files roles
%{_datadir}/ansible/%{name}/roles

%pretrans roles
#RHBZ https://bugzilla.redhat.com/show_bug.cgi?id=1626048
#roles/openshift_examples/latest used to be a symlink, now its a dir
# workaround for RPM bug https://bugzilla.redhat.com/show_bug.cgi?id=975909
if [ -d %{_datadir}/ansible/%{name}/roles/openshift_examples/files/examples ]; then
  find %{_datadir}/ansible/%{name}/roles/openshift_examples/files/examples -name latest -type l -delete
fi

# ----------------------------------------------------------------------------------
# openshift-ansible-tests subpackage
# ----------------------------------------------------------------------------------
%package test
Summary:       Openshift and Atomic Enterprise Ansible Test Playbooks
Requires:      %{name} = %{version}-%{release}
Requires:      %{name}-roles = %{version}-%{release}
Requires:      %{name}-playbooks = %{version}-%{release}
Requires:      python-boto3
Requires:      openssh-clients
BuildArch:     noarch

%description test
%{summary}.

%files test
%{_datadir}/ansible/%{name}/test

%changelog
