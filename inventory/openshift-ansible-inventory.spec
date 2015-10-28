Summary:       OpenShift Ansible Inventories
Name:          openshift-ansible-inventory
Version:       0.0.10
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
cp -p aws/hosts/ec2.py %{buildroot}/usr/share/ansible/inventory/aws
cp -p gce/hosts/gce.py %{buildroot}/usr/share/ansible/inventory/gce

%files
%config(noreplace) /etc/ansible/*
%dir /usr/share/ansible/inventory
/usr/share/ansible/inventory/multi_ec2.py*
/usr/share/ansible/inventory/aws/ec2.py*
/usr/share/ansible/inventory/gce/gce.py*

%changelog
* Wed Oct 28 2015 Kenny Woodson <kwoodson@redhat.com> 0.0.10-1
- new package built with tito

* Thu Aug 20 2015 Kenny Woodson <kwoodson@redhat.com> 0.0.9-1
- Merge pull request #408 from sdodson/docker-buildvm (bleanhar@redhat.com)
- Merge pull request #428 from jtslear/issue-383
  (twiest@users.noreply.github.com)
- Merge pull request #407 from aveshagarwal/ae-ansible-merge-auth
  (bleanhar@redhat.com)
- Enable htpasswd by default in the example hosts file. (avagarwa@redhat.com)
- Add support for setting default node selector (jdetiber@redhat.com)
- Merge pull request #429 from spinolacastro/custom_cors (bleanhar@redhat.com)
- Updated to read config first and default to users home dir
  (kwoodson@redhat.com)
- Fix Custom Cors (spinolacastro@gmail.com)
- Revert "namespace the byo inventory so the group names aren't so generic"
  (sdodson@redhat.com)
- Removes hardcoded python2 (jtslear@gmail.com)
- namespace the byo inventory so the group names aren't so generic
  (admiller@redhat.com)
- docker-buildvm-rhose is dead (sdodson@redhat.com)
- Add support for setting routingConfig:subdomain (jdetiber@redhat.com)
- Initial HA master (jdetiber@redhat.com)
- Make it clear that the byo inventory file is just an example
  (jdetiber@redhat.com)
- Playbook updates for clustered etcd (jdetiber@redhat.com)
- Update for RC2 changes (sdodson@redhat.com)
- Templatize configs and 0.5.2 changes (jdetiber@redhat.com)

* Tue Jun 09 2015 Kenny Woodson <kwoodson@redhat.com> 0.0.8-1
- Added more verbosity when error happens.  Also fixed a bug.
  (kwoodson@redhat.com)
- Implement OpenStack provider (lhuard@amadeus.com)
- * rename openshift_registry_url oreg_url * rename option_images to
  _{oreg|ortr}_images (jhonce@redhat.com)
- Fix the remaining pylint warnings (lhuard@amadeus.com)
- Fix some of the pylint warnings (lhuard@amadeus.com)
- [libvirt cluster] Use net-dhcp-leases to find VMs’ IPs (lhuard@amadeus.com)
- fixed the openshift-ansible-bin build (twiest@redhat.com)

* Fri May 15 2015 Kenny Woodson <kwoodson@redhat.com> 0.0.7-1
- Making multi_ec2 into a library (kwoodson@redhat.com)

* Wed May 13 2015 Thomas Wiest <twiest@redhat.com> 0.0.6-1
- Added support for grouping and a bug fix. (kwoodson@redhat.com)

* Tue May 12 2015 Thomas Wiest <twiest@redhat.com> 0.0.5-1
- removed ec2.ini from the openshift-ansible-inventory.spec file so that we're
  not dictating what the ec2.ini file should look like. (twiest@redhat.com)
- Added capability to pass in ec2.ini file. (kwoodson@redhat.com)

* Thu May 07 2015 Thomas Wiest <twiest@redhat.com> 0.0.4-1
- Fixed a bug due to renaming of variables. (kwoodson@redhat.com)

* Thu May 07 2015 Thomas Wiest <twiest@redhat.com> 0.0.3-1
- fixed build problems with openshift-ansible-inventory.spec
  (twiest@redhat.com)
- Allow option in multi_ec2 to set cache location. (kwoodson@redhat.com)
- Add ansible_connection=local to localhost in inventory (jdetiber@redhat.com)
- Adding refresh-cache option and cleanup for pylint. Also updated for
  aws/hosts/ being added. (kwoodson@redhat.com)

* Thu Mar 26 2015 Thomas Wiest <twiest@redhat.com> 0.0.2-1
- added the ability to have a config file in /etc/openshift_ansible to
  multi_ec2.py. (twiest@redhat.com)
- Merge pull request #97 from jwhonce/wip/cluster (jhonce@redhat.com)
- gce inventory/playbook updates for node registration changes
  (jdetiber@redhat.com)
- Various fixes (jdetiber@redhat.com)

* Tue Mar 24 2015 Thomas Wiest <twiest@redhat.com> 0.0.1-1
- new package built with tito

