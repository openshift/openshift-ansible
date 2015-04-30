Summary:       OpenShift Ansible Scripts for working with metadata hosts
Name:          openshift-ansible-bin
Version:       0.0.8
Release:       1%{?dist}
License:       ASL 2.0
URL:           https://github.com/openshift/openshift-ansible
Source0:       %{name}-%{version}.tar.gz
Requires:      python2, openshift-ansible-inventory
BuildRequires: python2-devel
BuildArch:     noarch

%description
Scripts to make it nicer when working with hosts that are defined only by metadata.

%prep
%setup -q

%build

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{python_sitelib}/openshift_ansible
mkdir -p %{buildroot}/etc/bash_completion.d
mkdir -p %{buildroot}/etc/openshift_ansible

cp -p ossh oscp opssh opscp ohi %{buildroot}%{_bindir}
cp -p openshift_ansible/* %{buildroot}%{python_sitelib}/openshift_ansible
cp -p ossh_bash_completion %{buildroot}/etc/bash_completion.d

cp -p openshift_ansible.conf.example %{buildroot}/etc/openshift_ansible/openshift_ansible.conf

%files
%{_bindir}/*
%{python_sitelib}/openshift_ansible/
/etc/bash_completion.d/*
%config(noreplace) /etc/openshift_ansible/

%changelog
* Mon Apr 13 2015 Thomas Wiest <twiest@redhat.com> 0.0.8-1
- fixed bug in opssh where it wouldn't actually run pssh (twiest@redhat.com)

* Mon Apr 13 2015 Thomas Wiest <twiest@redhat.com> 0.0.7-1
- added the ability to run opssh and ohi on all hosts in an environment, as
  well as all hosts of the same host-type regardless of environment
  (twiest@redhat.com)
- added ohi (twiest@redhat.com)
* Thu Apr 09 2015 Thomas Wiest <twiest@redhat.com> 0.0.6-1
- fixed bug where opssh would throw an exception if pssh returned a non-zero
  exit code (twiest@redhat.com)

* Wed Apr 08 2015 Thomas Wiest <twiest@redhat.com> 0.0.5-1
- fixed the opssh default output behavior to be consistent with pssh. Also
  fixed a bug in how directories are named for --outdir and --errdir.
  (twiest@redhat.com)
* Tue Mar 31 2015 Thomas Wiest <twiest@redhat.com> 0.0.4-1
- Fixed when tag was missing and added opssh completion (kwoodson@redhat.com)

* Mon Mar 30 2015 Thomas Wiest <twiest@redhat.com> 0.0.3-1
- created a python package named openshift_ansible (twiest@redhat.com)

* Mon Mar 30 2015 Thomas Wiest <twiest@redhat.com> 0.0.2-1
- added config file support to opssh, ossh, and oscp (twiest@redhat.com)
* Tue Mar 24 2015 Thomas Wiest <twiest@redhat.com> 0.0.1-1
- new package built with tito

