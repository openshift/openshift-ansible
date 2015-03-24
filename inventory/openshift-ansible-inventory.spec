Summary:       OpenShift Ansible Inventories
Name:          openshift-ansible-inventory
Version:       0.0.0
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
mkdir -p %{buildroot}/usr/share/ansible/inventory
mkdir -p %{buildroot}/usr/share/ansible/inventory/aws
mkdir -p %{buildroot}/usr/share/ansible/inventory/gce

cp -p multi_ec2.py multi_ec2.yaml.example %{buildroot}/usr/share/ansible/inventory
cp -p aws/ec2.py aws/ec2.ini %{buildroot}/usr/share/ansible/inventory/aws
cp -p gce/gce.py %{buildroot}/usr/share/ansible/inventory/gce

%files
%dir /usr/share/ansible/inventory
/usr/share/ansible/inventory/multi_ec2.py*
/usr/share/ansible/inventory/multi_ec2.yaml.example
/usr/share/ansible/inventory/aws/ec2.py*
%config(noreplace) /usr/share/ansible/inventory/aws/ec2.ini
/usr/share/ansible/inventory/gce/gce.py*

%changelog
