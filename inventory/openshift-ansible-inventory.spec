Summary:       OpenShift Ansible Inventories
Name:          openshift-ansible-inventory
Version:       0.0.2
Release:       1%{?dist}
License:       ASL 2.0
URL:           https://github.com/openshift/openshift-ansible
Source0:       %{name}-%{version}.tar.gz
Requires:      python2
BuildRequires: python2-devel
BuildArch:     noarch

%description
Ansible Inventories used with the openshift-ansible scripts and playbooks.

%prep
%setup -q

%build

%install
mkdir -p %{buildroot}/etc/ansible
mkdir -p %{buildroot}/usr/share/ansible/inventory
mkdir -p %{buildroot}/usr/share/ansible/inventory/aws
mkdir -p %{buildroot}/usr/share/ansible/inventory/gce

cp -p multi_ec2.py %{buildroot}/usr/share/ansible/inventory
cp -p multi_ec2.yaml.example %{buildroot}/etc/ansible/multi_ec2.yaml
cp -p aws/ec2.py aws/ec2.ini %{buildroot}/usr/share/ansible/inventory/aws
cp -p gce/gce.py %{buildroot}/usr/share/ansible/inventory/gce

%files
%config(noreplace) /etc/ansible/*
%dir /usr/share/ansible/inventory
/usr/share/ansible/inventory/multi_ec2.py*
/usr/share/ansible/inventory/aws/ec2.py*
%config(noreplace) /usr/share/ansible/inventory/aws/ec2.ini
/usr/share/ansible/inventory/gce/gce.py*

%changelog
* Thu Mar 26 2015 Thomas Wiest <twiest@redhat.com> 0.0.2-1
- added the ability to have a config file in /etc/openshift_ansible to
  multi_ec2.py. (twiest@redhat.com)
- Merge pull request #97 from jwhonce/wip/cluster (jhonce@redhat.com)
- gce inventory/playbook updates for node registration changes
  (jdetiber@redhat.com)
- Various fixes (jdetiber@redhat.com)

* Tue Mar 24 2015 Thomas Wiest <twiest@redhat.com> 0.0.1-1
- new package built with tito

