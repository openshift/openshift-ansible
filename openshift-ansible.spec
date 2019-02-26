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

Requires:      ansible >= 2.5.7
Requires:      python2
Requires:      python-six
Requires:      tar
Requires:      %{name}-docs = %{version}-%{release}
Requires:      %{name}-playbooks = %{version}-%{release}
Requires:      %{name}-roles = %{version}-%{release}
Obsoletes:     atomic-openshift-utils <= 3.10
Requires:      java-1.8.0-openjdk-headless
Requires:      httpd-tools
Requires:      libselinux-python
Requires:      python-passlib
Requires:      python2-crypto
Requires:      patch
Requires:      pyOpenSSL
Requires:      iproute

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
# remove contiv plabooks
rm -rf %{buildroot}%{_datadir}/ansible/%{name}/playbooks/adhoc/contiv

# BZ1330091
find -L %{buildroot}%{_datadir}/ansible/%{name}/playbooks -name lookup_plugins -type l -delete
find -L %{buildroot}%{_datadir}/ansible/%{name}/playbooks -name filter_plugins -type l -delete

# openshift-ansible-roles install
cp -rp roles %{buildroot}%{_datadir}/ansible/%{name}/
# remove contiv role
rm -rf %{buildroot}%{_datadir}/ansible/%{name}/roles/contiv/*
# touch a file in contiv so that it can be added to SCM's
touch %{buildroot}%{_datadir}/ansible/%{name}/roles/contiv/.empty_dir

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
BuildArch:     noarch

%description test
%{summary}.

%files test
%{_datadir}/ansible/%{name}/test

%changelog
* Mon Feb 25 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.185.0
- 

* Sun Feb 24 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.184.0
- 

* Sat Feb 23 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.183.0
- 

* Fri Feb 22 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.182.0
- 

* Fri Feb 22 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.181.0
- 

* Thu Feb 21 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.180.0
- 

* Wed Feb 20 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.179.0
- 

* Tue Feb 19 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.178.0
- 

* Mon Feb 18 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.177.0
- 

* Sun Feb 17 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.176.0
- 

* Sat Feb 16 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.175.0
- 

* Fri Feb 15 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.174.0
- 

* Thu Feb 14 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.173.0
- 

* Wed Feb 13 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.172.0
- 

* Tue Feb 12 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.171.0
- 

* Mon Feb 11 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.170.0
- 

* Sun Feb 10 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.169.0
- 

* Sun Feb 10 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.168.0
- 

* Fri Feb 08 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.167.0
- 

* Fri Feb 08 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.166.0
- 

* Thu Feb 07 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.165.0
- 

* Thu Feb 07 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.164.0
- 

* Wed Feb 06 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.163.0
- 

* Wed Feb 06 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.162.0
- 

* Wed Feb 06 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.161.0
- 

* Wed Feb 06 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.160.0
- 

* Tue Feb 05 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.159.0
- 

* Tue Feb 05 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.158.0
- 

* Mon Feb 04 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.157.0
- 

* Sun Feb 03 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.156.0
- 

* Sun Feb 03 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.155.0
- 

* Fri Feb 01 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.154.0
- 

* Thu Jan 31 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.153.0
- 

* Thu Jan 31 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.152.0
- 

* Wed Jan 30 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.151.0
- 

* Tue Jan 29 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.150.0
- 

* Mon Jan 28 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.149.0
- Add additional gluster SMEs to approvers, update ansible reviewers
  (sdodson@redhat.com)
- Add new team members to OWNERS file. (pdd@redhat.com)

* Fri Jan 25 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.148.0
- 

* Thu Jan 24 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.147.0
- 

* Wed Jan 23 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.146.0
- 

* Tue Jan 22 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.145.0
- 

* Tue Jan 22 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.144.0
- 

* Thu Jan 17 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.143.0
- 

* Wed Jan 16 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.142.0
- 

* Tue Jan 15 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.141.0
- 

* Tue Jan 15 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.140.0
- 

* Mon Jan 14 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.139.0
- 

* Sun Jan 13 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.138.0
- 

* Fri Jan 11 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.137.0
- 

* Fri Jan 11 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.136.0
- 

* Thu Jan 10 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.135.0
- 

* Thu Jan 10 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.134.0
- 

* Thu Jan 10 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.133.0
- 

* Thu Jan 10 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.132.0
- Remove vendored ansible-profile callback (rteague@redhat.com)

* Wed Jan 09 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.131.0
- 

* Tue Jan 08 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.130.0
- 

* Tue Jan 08 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.129.0
- 

* Mon Jan 07 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.128.0
- 

* Mon Jan 07 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.127.0
- 

* Sun Jan 06 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.126.0
- 

* Sat Jan 05 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.125.0
- 

* Fri Jan 04 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.124.0
- 

* Thu Jan 03 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.123.0
- 

* Wed Jan 02 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.122.0
- 

* Tue Jan 01 2019 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.121.0
- 

* Mon Dec 31 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.120.0
- 

* Sun Dec 30 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.119.0
- 

* Sat Dec 29 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.118.0
- 

* Fri Dec 28 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.117.0
- 

* Thu Dec 27 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.116.0
- 

* Wed Dec 26 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.115.0
- 

* Tue Dec 25 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.114.0
- 

* Mon Dec 24 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.113.0
- 

* Sun Dec 23 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.112.0
- 

* Sat Dec 22 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.111.0
- 

* Fri Dec 21 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.110.0
- 

* Fri Dec 21 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.109.0
- 

* Fri Dec 21 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.108.0
- 

* Fri Dec 21 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.107.0
- 

* Thu Dec 20 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.106.0
- 

* Thu Dec 20 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.105.0
- 

* Thu Dec 20 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.104.0
- 

* Wed Dec 19 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.103.0
- 

* Tue Dec 18 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.102.0
- 

* Mon Dec 17 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.101.0
- 

* Sun Dec 16 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.100.0
- 

* Sat Dec 15 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.99.0
- 

* Fri Dec 14 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.98.0
- 

* Thu Dec 13 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.97.0
- Use ansible 2.7.4 (roignac@gmail.com)
- Install python-docker-py instead of python-docker (sgaikwad@redhat.com)
- Install boto3 from pip (roignac@gmail.com)

* Wed Dec 12 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.96.0
- Revert "Devel 4.0: CI test" (sdodson@redhat.com)
- DEBUG: skip openshift-apiserver operator (roignac@gmail.com)
- Add retries when installing openshift packages (roignac@gmail.com)
- Wait for core operators to come up (roignac@gmail.com)
- GCP: open ports on masters for cadvisor and CVO (roignac@gmail.com)
- GCP: open port on masters to collect cadvisor metrics (roignac@gmail.com)
- Don't install atomic - we don't use it (roignac@gmail.com)
- Install nfs-utils on nodes to pass storage tests (roignac@gmail.com)
- GCP: use YAML output (roignac@gmail.com)
- bootstrap kubeconfig location is now /opt/openshift (roignac@gmail.com)
- GCP: set MTU to 1500 (1450 on veth + 50) (roignac@gmail.com)
- Router is now a deployment (roignac@gmail.com)
- Open ports for cadvisor and CVO metrics - this is master-internal
  (roignac@gmail.com)
- GCP firewall: nodes don't expose 80/443 (roignac@gmail.com)
- Install boto3 from pip (roignac@gmail.com)
- base: install python-docker-py (roignac@gmail.com)
- Remove crio pause_image hack (roignac@gmail.com)
- GCP: include all etcd discovery records in one line (roignac@gmail.com)
- HACK CRIO: set docker.io as a source for unqualified images
  (roignac@gmail.com)
- Fix ident errors in new playbooks (roignac@gmail.com)
- Wait for ingress to appear (roignac@gmail.com)
- HACK GCP: create and remove etcd discovery entries via a script
  (roignac@gmail.com)
- Rework playbooks to setup 4.0 on GCP (roignac@gmail.com)
- Enhance parse_ignition file content decoding (mgugino@redhat.com)
- Add additional parse_igintion options and support (mgugino@redhat.com)
- WIP: Scale node to new-installer cluster (mgugino@redhat.com)

* Tue Dec 11 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.95.0
- Dockerfile.rhel7: remove superfluous labels (lmeyer@redhat.com)

* Mon Dec 10 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.94.0
- 

* Sun Dec 09 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.93.0
- 

* Sat Dec 08 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.92.0
- 

* Sat Dec 08 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.91.0
- 

* Fri Dec 07 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.90.0
- 

* Fri Dec 07 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.89.0
- 

* Thu Dec 06 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.88.0
- 

* Thu Dec 06 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.87.0
- 

* Thu Dec 06 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.86.0
- 

* Thu Dec 06 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.85.0
- 

* Wed Dec 05 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.84.0
- 

* Tue Dec 04 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.83.0
- 

* Mon Dec 03 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.82.0
- 

* Sun Dec 02 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.81.0
- 

* Sat Dec 01 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.80.0
- 

* Sat Dec 01 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.79.0
- 

* Thu Nov 29 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.78.0
- 

* Wed Nov 28 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.77.0
- 

* Tue Nov 27 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.76.0
- 

* Tue Nov 27 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.75.0
- 

* Sun Nov 25 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.74.0
- 

* Sun Nov 25 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.73.0
- 

* Sat Nov 24 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.72.0
- 

* Sat Nov 24 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.71.0
- 

* Fri Nov 23 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.70.0
- 

* Fri Nov 23 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.69.0
- 

* Thu Nov 22 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.68.0
- 

* Wed Nov 21 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.67.0
- 

* Tue Nov 20 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.66.0
- 

* Tue Nov 20 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.65.0
- 

* Tue Nov 20 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.64.0
- 

* Mon Nov 19 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.63.0
- 

* Sun Nov 18 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.62.0
- 

* Sat Nov 17 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.61.0
- 

* Fri Nov 16 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.60.0
- 

* Thu Nov 15 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.59.0
- 

* Wed Nov 14 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.58.0
- 

* Tue Nov 13 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.57.0
- 

* Mon Nov 12 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.56.0
- 

* Mon Nov 12 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.55.0
- 

* Sat Nov 10 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.54.0
- 

* Sat Nov 10 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.53.0
- GitHubIdentityProvider catering for GitHub Enterprise and includes examples
  on using the provider. Installation includes parameters for ca and hostname
  (GH enterprise specific) (ckyriaki@redhat.com)
- Check both service catalog and install vars (ruju@itu.dk)

* Thu Nov 08 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.52.0
- Simplify PR template and add text to README.md (sdodson@redhat.com)
- Pre-pull CLI image using openshift_container_cli (vrutkovs@redhat.com)
- Start node image prepull after CRIO is restarted (vrutkovs@redhat.com)
- sdn: tolerate all taints (vrutkovs@redhat.com)
- sync: tolerate all taints (vrutkovs@redhat.com)
- Update centos_repos.yml (camabeh@users.noreply.github.com)
- Update centos_repos.yml (camabeh@users.noreply.github.com)
- Update .github/PULL_REQUEST_TEMPLATE.md (roignac@gmail.com)
- Add notice about MASTER branch (sdodson@redhat.com)

* Thu Nov 08 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.51.0
- Mount /etc/pki into controller pod (mchappel@redhat.com)

* Wed Nov 07 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.50.0
- Restart docker after openstack storage setup (tzumainn@redhat.com)
- Update crio.conf.j2 template for registries (umohnani@redhat.com)
- Fix master paths check, while using Istio (faust64@gmail.com)

* Tue Nov 06 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.49.0
- Add instructions to use cri-o in openstack (e.minguez@gmail.com)
- Fix broken link in README.md (artheus@users.noreply.github.com)
- openshift_prometheus: cleanup unused variables (pgier@redhat.com)
- fix gce-logging problem (rmeggins@redhat.com)
- Run the init/main playbook properly (e.minguez@gmail.com)

* Mon Nov 05 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.48.0
- 

* Mon Nov 05 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.47.0
- 

* Sun Nov 04 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.46.0
- 

* Sat Nov 03 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.45.0
- added needed space in error message as stated in bug# 1645718
  (pruan@redhat.com)

* Fri Nov 02 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.44.0
- glusterfs: Fix a typo in the README (obnox@redhat.com)

* Thu Nov 01 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.43.0
- Update playbooks/azure/openshift-cluster/build_node_image.yml
  (roignac@gmail.com)
- add oreg_url check (mangirdas@judeikis.lt)

* Wed Oct 31 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.42.0
- Adding configuration documentation for etcd (bedin@redhat.com)
- Fixing provisioning of separate etcd (bedin@redhat.com)
- Fixing provisioning of separate etcd (bedin@redhat.com)
- Fixing provisioning of separate etcd (bedin@redhat.com)

* Tue Oct 30 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.41.0
- 4.0 -> 3.11 (mangirdas@judeikis.lt)
- add 3.11 build steps (mangirdas@judeikis.lt)
- rollback azure cli version and sas image config path (mangirdas@judeikis.lt)
- Make timeout a param and increase default to 20 for docker_creds.py
  (chmurphy@redhat.com)
- Ensure Kuryr-controller runs on infra nodes (ltomasbo@redhat.com)
- Updating clean up task to match become of creation task (ewolinet@redhat.com)

* Mon Oct 29 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.40.0
- 

* Mon Oct 29 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.39.0
- Increase Octavia OpenShift API loadbalancer timeouts (ltomasbo@redhat.com)

* Sun Oct 28 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.38.0
- Improve cleanup of networks and disks in GCP (ccoleman@redhat.com)

* Sat Oct 27 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.37.0
- Added validation to avoid upload template always (jparrill@redhat.com)
- openshift_console: remove OAuthClient when uninstalling (mlibra@redhat.com)
- adding kuryr ports back (egarcia@redhat.com)
- Prepull node image using openshift_container_cli (vrutkovs@redhat.com)
- clarification in response to comments (iamemilio@users.noreply.github.com)
- correction (i.am.emilio@gmail.com)
- clearer instructions (iamemilio@users.noreply.github.com)
- Certain ports were incorrectly configured by default. (i.am.emilio@gmail.com)
- Update existing template for registry-console and make sure created objects
  are updated (vrutkovs@redhat.com)

* Fri Oct 26 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.36.0
- Fix ansible version checking (celebdor@gmail.com)

* Thu Oct 25 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.35.0
- Don't install cockpit unless required (e.minguez@gmail.com)
- openshift_ovirt: Add a task to create the VMs (rgolan@redhat.com)
- Decalre the dns variable in the defaults (rgolan@redhat.com)
- Fix version number in upgrade readme to 4.0. (pdd@redhat.com)
- Add pull secret to the Calico controllers (mleung975@gmail.com)
- Fix Calico liveness and readiness checks to include Calico 3.2
  (mleung975@gmail.com)
- Fail installation if Atomic Host variant ID is detected (vrutkovs@redhat.com)
- Don't use 'atomic' RPM (vrutkovs@redhat.com)
- Remove an option to install 4.0 on Atomic Hosts (vrutkovs@redhat.com)

* Wed Oct 24 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.34.0
- Fix incorrect until condition in servicecatalog api check
  (sdodson@redhat.com)
- Run the init playbooks to properly set vars (e.minguez@gmail.com)
- Add permissions for the Calico CNI plugin to access namespaces
  (mleung975@gmail.com)

* Tue Oct 23 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.33.0
- Remove hostname override from OpenStack inventory (tomas@sedovic.cz)
- Fixing Typo (jparrill@redhat.com)
- quick fix for formatting of error messages, bz# 1640823 (pruan@redhat.com)
- Mount /etc/pki into apiserver pod (sdodson@redhat.com)
- Set openshift_hosted_registry_storage_swift_insecureskipverify's default
  (mickael.canevet@camptocamp.com)
- Document openshift_hosted_registry_storage_swift_insecureskipverify
  (mickael.canevet@camptocamp.com)
- Added capability to add dns_search and dns_server even without static
  configuration (jparrill@redhat.com)
- Fixes #10415 maintains the name and host_name when vm count field are 1.
  (jparrill@redhat.com)
- Add openshift_hosted_registry_storage_swift_insecureskipverify parameter
  (mickael.canevet@camptocamp.com)
- Updated logging namespace name (andy.block@gmail.com)
- Update oc_group.py in src (camabeh@gmail.com)
- cluster-monitoring: Adds storageclass name variable (davivcgarcia@gmail.com)
- Update tests (camabeh@gmail.com)
- Fix oc group get (camabeh@gmail.com)

* Mon Oct 22 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.32.0
- Allow Ansible 2.5.7 (tomas@sedovic.cz)
- Remove value rather than replacing it with an empty string
  (sdodson@redhat.com)

* Sun Oct 21 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.31.0
- 

* Sat Oct 20 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.30.0
- 

* Fri Oct 19 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.29.0
- 

* Thu Oct 18 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.28.0
- Fix scaleup failure for hostname override (mgugino@redhat.com)
- Fail on openshift_kubelet_name_override for new hosts. (mgugino@redhat.com)

* Thu Oct 18 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.27.0
- Make sure images are prepulled when CRIO is used (vrutkovs@redhat.com)
- pin azure cli to version 2.0.47 and fix start copy playbook task
  (akalugwu@redhat.com)

* Wed Oct 17 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.26.0
- 

* Wed Oct 17 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.25.0
- 

* Tue Oct 16 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.24.0
- 

* Mon Oct 15 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.23.0
- Add ansible 2.6 repo (vrutkovs@redhat.com)

* Sun Oct 14 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.22.0
- 

* Sun Oct 14 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.21.0
- 

* Fri Oct 12 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.20.0
- Require ansible 2.6.5 (vrutkovs@redhat.com)
- Dockerfile: install ansible 2.6 and remove epel-testing (vrutkovs@redhat.com)
- Dockerfile: install ansible 2.6 (vrutkovs@redhat.com)

* Fri Oct 12 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.19.0
- README: ansible 2.7 is not supported (vrutkovs@redhat.com)
- Modify sync pod to check for KUBELET_HOSTNAME_OVERRIDE (mgugino@redhat.com)
- Configure Ansible service broker secrets (simon.ruegg@vshn.ch)

* Wed Oct 10 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.18.0
- Update main.yml (sgaikwad@redhat.com)
- Openshift autoheal fails to pull images even if oreg_url is specified
  (sgaikwad@redhat.com)

* Tue Oct 09 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.17.0
- Add missing option in Openstack documentation and sample file.
  (juriarte@redhat.com)
- Replace openshift.node.nodename with l_kubelet_node_name (mgugino@redhat.com)
- Increase number of retries in sync DS (vrutkovs@redhat.com)
- test/ci: update atomic hosts and restart only when necessary
  (vrutkovs@redhat.com)
- test/ci: make sure all packages are updated before starting install
  (vrutkovs@redhat.com)
- test/ci: set hostname before collecting facts (vrutkovs@redhat.com)
- Fix etcd scaleup on standalone hosts (rteague@redhat.com)

* Mon Oct 08 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.16.0
- Fail on openshift_hostname defined; add openshift_kubelet_name_override
  (mgugino@redhat.com)

* Sun Oct 07 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.15.0
- 

* Sun Oct 07 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.14.0
- 

* Sat Oct 06 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.13.0
- unmount just before removing (rmeggins@redhat.com)

* Fri Oct 05 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.12.0
- 

* Fri Oct 05 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.11.0
- prelim/partial update to jenkins imagestream to enable tests (while we wait
  for global PR in openshift/origin to merge) (gmontero@redhat.com)
- Remove unused registry migration task (vrutkovs@redhat.com)

* Thu Oct 04 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.10.0
- glusterfs: add probe script for liveness and readiness checks
  (jmulligan@redhat.com)

* Thu Oct 04 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.9.0
- 

* Wed Oct 03 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.8.0
- roles/cluster_monitoring: minor wording improvement (pgier@redhat.com)
- Remove unlicensed code from internet in sanity checks (mgugino@redhat.com)
- Use clusterid attribute to filter servers in dynamic inventory
  (rusichen@redhat.com)
- Add CI scripts in hack/ (vrutkovs@redhat.com)
- Replace 'command chmod' with 'file mode=...' (vrutkovs@redhat.com)
- Start only the ovsdb so we can add the config safely (bbennett@redhat.com)
- Add pyOpenSSL and iproute to RPM dependencies (sdodson@redhat.com)
- Fixes #8267 (mavazque@redhat.com)
- Node problem detector always pull images from registry.redhat.io for
  openshift-enterprise (sgaikwad@redhat.com)
- Replace undefined {{ item }} by filename (info@theothersolution.nl)
- Pass admin kubeconfig (sdodson@redhat.com)
- typo correction (i.am.emilio@gmail.com)
- no longer creates cns security group when number of cns is 0
  (i.am.emilio@gmail.com)

* Fri Sep 28 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.7.0
- Add OpenStack pre-requisites check for various features (tzumainn@redhat.com)
- [openstack] Add configuration note for all-in-one and DNS (pep@redhat.com)
- Remove oreg_auth_credentials_replace from inventory (sdodson@redhat.com)
- test/ci: ensure AWS instances have public hostname (vrutkovs@redhat.com)

* Thu Sep 27 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.6.0
- Bug 1554293 - logging-eventrouter event not formatted correctly in
  Elasticsearch when using MUX (nhosoi@redhat.com)
- Add a new dockerfile to use in CI (vrutkovs@redhat.com)
- Add new package which contains test playbooks (vrutkovs@redhat.com)

* Wed Sep 26 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.5.0
- test/ci: set expirationDate flag for CI namespace garbage collector
  (vrutkovs@redhat.com)
- Refactored Calico and updated playbooks to reflect self-hosted Calico
  installs only (mleung975@gmail.com)
- Enable IAM roles for EC2s in AWS (mazzystr@gmail.com)
- Fix for recent az changes. (kwoodson@redhat.com)
- cluster-monitoring: Bump cluster monitoring operator in origin
  (fbranczyk@gmail.com)
- Added capability to fix static addresses to openshift_ovirt provider vms
  (jparrill@redhat.com)

* Mon Sep 24 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.4.0
- Reload tuned service when node-config.yaml has changed.
  (jmencak@users.noreply.github.com)

* Fri Sep 21 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.3.0
- GlusterFS: Fix registry playbook PV creation (jarrpa@redhat.com)
- Only create OpenStack router if both router and subnet are undefined
  (tzumainn@redhat.com)

* Fri Sep 21 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.2.0
- 

* Fri Sep 21 2018 AOS Automation Release Team <aos-team-art@redhat.com> 4.0.0-0.1.0
- Don't re-deploy node system containers when deploying auth credentials
  (sdodson@redhat.com)
- etcdv2 remove: avoid using failed_when (vrutkovs@redhat.com)
- Bump Data Grid to version 1.1.1 (osni.oliveira@redhat.com)
- remove unix prefix from crio path (sjenning@redhat.com)
- adding container.yaml (adammhaile@gmail.com)
- Fix openstack nsupdate record (tzumainn@redhat.com)
- Always set openstack node private ip (tzumainn@redhat.com)
- lib_utils_oo_oreg_image preserve path component (jkupfere@redhat.com)
- Add unit test for oo_oreg_image filter (mgugino@redhat.com)
- Update installer_checkpoint plugin to handle empty stats (rteague@redhat.com)
- Fix etcd scaleup playbook (rteague@redhat.com)
- registry auth: fix check that node_oreg_auth_credentials_stat exists
  (vrutkovs@redhat.com)
- Fix openshift_additional_registry_credentials comparison
  (vrutkovs@redhat.com)
- Ensure glusterfs host groups are correct for registry play
  (mgugino@redhat.com)
- move OpenStack network fact gathering from prereqs to provision tasks
  (tzumainn@redhat.com)
- Ensure atomic hosts prepull node image during pre-upgrade
  (mgugino@redhat.com)
- Make cloud-user SSH key maintenance more reliable (ironcladlou@gmail.com)
- Simplify match filter when looking for sync annotations (vrutkovs@redhat.com)
- Merge upgrade_control_plane playbooks back into one (vrutkovs@redhat.com)
- test ci: add an option to terminate VMs instead of stopping
  (vrutkovs@redhat.com)
- Update main.yml (sheldyakov@tutu.ru)
- Remove duplicate words (lxia@redhat.com)
- Remove traces of containerized install (vrutkovs@redhat.com)
- Move the cluster-cidr assignment to the correct configs (mleung975@gmail.com)
- Ensure dnsmasq is restarted during upgrades (mgugino@redhat.com)
- Don't install NM on atomic systems (vrutkovs@redhat.com)
- openshift-prometheus: remove deprecated prometheus stack install
  (pgier@redhat.com)
- GCP upgrade: don't exclude nodes with tag_ocp-bootstrap (vrutkovs@redhat.com)
- GCP upgrade: don't exclude nodes with tag_ocp-bootstrap (vrutkovs@redhat.com)
- Hash the registry hostname to generate unique secret names
  (sdodson@redhat.com)
- Add retries around api service discovery (sdodson@redhat.com)
- Ensure that recycler pod definition is deployed during upgrade
  (sdodson@redhat.com)
- Change upgrade playbooks to use 4.0 (vrutkovs@redhat.com)
- Add 3 retries around all image stream create/replace (sdodson@redhat.com)
- Fix wrong doc default value of logging (teleyic@gmail.com)
- test/ci: setup network manager (vrutkovs@redhat.com)
- Update uninstall_masters play to deal with standalone instances
  (mazzystr@gmail.com)
- Fix broken package list on fedora (mgugino@redhat.com)
- certificate_expiry: gather facts so ansible_date_time is defined
  (sdodson@redhat.com)
- Fix volume recycler configuration on upgrade (sdodson@redhat.com)
- openshift_storage_nfs_lvm: fix with_sequence (jfchevrette@gmail.com)
- Removing launch.yml. (kwoodson@redhat.com)
- Wait for sync DS to set annotations on all available nodes
  (vrutkovs@redhat.com)
- sync annotations: expected number of annotations should be a number of items
  (vrutkovs@redhat.com)
- reduce number of openstack heat retries (tzumainn@redhat.com)
- Fix openstack parameter checks (tzumainn@redhat.com)
- Add a wait for aggregated APIs when restarting control plane
  (sdodson@redhat.com)
- Update openshift ca redeploy to use correct node client-ca
  (rteague@redhat.com)
- Enable monitoring of openshift-metering via cluster monitoring
  (chance.zibolski@coreos.com)
- Refactor csr approval for client certs ignore ready (mgugino@redhat.com)
- reducing /sys/fs/selinux/avc/cache_threshold to 8192 instead of 65535
  (elvirkuric@gmail.com)
- Add preview operators to OLM Catalog (cordell.evan@gmail.com)
- Collect provider facts only if cloudprovider is set (vrutkovs@redhat.com)
- - s3 variables check as part of importing the s3 tasks itself.
  (sarumuga@redhat.com)
- Add proper liveness and readiness checks for Calico 3.2 (mleung975@gmail.com)
- Move controller args back to template (hekumar@redhat.com)
- Retry our etcd health check (sdodson@redhat.com)
- Set gquota on slash filesystem (mazzystr@gmail.com)
- docker_creds: rename image_name to test_image (sdodson@redhat.com)
- cluster-monitoring: Fix regex_replace to remove image tag
  (fbranczyk@gmail.com)
- fix arguments to controller (hekumar@redhat.com)
- Update recyler to lsm_registry_url (hekumar@redhat.com)
- cutting 4.0 (aos-team-art@redhat.com)
- Use oreg_url rather than hardcoding path (hekumar@redhat.com)
- Formatting fixes on olm and catalog operators (cordell.evan@gmail.com)
- Update rh-operators catalog to latest (cordell.evan@gmail.com)
- Update OLM CRDs to latest (cordell.evan@gmail.com)
- Proper DNS for the subnet created (e.minguez@gmail.com)
- Set etcd facts necessary for etcd scaleup (rteague@redhat.com)
- Revert "Don't fetch provider openshift_facts if openshift_cloud_provider_kind
  is not set" (roignac@gmail.com)
- cluster-monitoring: Remove version tag for passing image repos
  (fbranczyk@gmail.com)
- Fixes: BZ1618547 disable keep ns on error in ASB to prevent resource
  starvation (jmontleo@redhat.com)
- Add openshift_additional_registry_credentials (sdodson@redhat.com)
- docker_creds: Add tls_verify parameter (sdodson@redhat.com)
- Avoid S3 deployment check (sarumuga@redhat.com)
- Filter openshift_cloudprovider_openstack_blockstorage_ignore_volume_az to
  bool (alberto.rodriguez.peon@cern.ch)
- Add playbook to migrate node imageConfig.format (mgugino@redhat.com)
- docker_creds: Use bool for test_login param (sdodson@redhat.com)
- Run the kube-proxy once per cluster for Calico (mleung975@gmail.com)
- Provide version information (hekumar@redhat.com)
- Annotate nodes with md5sum of the applied config (vrutkovs@redhat.com)
- Add a pod template for recycler pod (hekumar@redhat.com)
- Bump repo constants to support 4.0 RPMs (ccoleman@redhat.com)
- Add calico-pull-secret (mleung975@gmail.com)
- Add separate Calico etcd (mleung975@gmail.com)
- Use true/false instead of yes/no (alberto.rodriguez.peon@cern.ch)
- Allow to configure BlockStorage.ignore-volume-az for Openstack Cloud Provider
  (alberto.rodriguez.peon@cern.ch)

* Tue Sep 11 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.35.0
- cluster-monitoring: Fix incorrect handling of conditional PVCs
  (fbranczyk@gmail.com)
- fix alertmanager example in OLM prometheus operator (cordell.evan@gmail.com)
- GlusterFS: Tweak groups for external config (jarrpa@redhat.com)
- Fix kuryr support for custom OpenStack network and subnet
  (ltomasbo@redhat.com)
- Add missing ClusterRole for OLM (cordell.evan@gmail.com)
- GlusterFS: Fix heketi_pod check (jarrpa@redhat.com)
- spec: remove roles/openshift_examples/lates symlink (vrutkovs@redhat.com)
- Prepare to split openshift-sdn out of the openshift binary
  (ccoleman@redhat.com)
- SDN check: Ignore errors from `oc version` (miciah.masters@gmail.com)

* Sun Sep 09 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.34.0
- 

* Sat Sep 08 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.33.0
- Install rh-operators catalog (cordell.evan@gmail.com)
- olm: add openshift_facts dependency (sdodson@redhat.com)
- fix ca cert deploy for 3.10. addresses
  https://bugzilla.redhat.com/show_bug.cgi?id=1585978 (judd@newgoliath.com)
- Add oc_get_nodes to debug csr output (mgugino@redhat.com)
- Check for migrated status (vrutkovs@redhat.com)
- Run on first etcd only (vrutkovs@redhat.com)
- Add playbooks to remove etcdv2 data (vrutkovs@redhat.com)
- Update rh-operators catalog (cordell.evan@gmail.com)
- don't bind to cluster-admin for OLM (cordell.evan@gmail.com)
- put olm deployments in the right namespace (cordell.evan@gmail.com)
- add main.yaml for olm task (cordell.evan@gmail.com)

* Fri Sep 07 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.32.0
- 

* Fri Sep 07 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.31.0
- 

* Fri Sep 07 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.30.0
- Remove configmap check during upgrades (rteague@redhat.com)
- Add extra debug info to csr module (mgugino@redhat.com)
- Revert ensure gquota set on slash filesystem (mazzystr@gmail.com)
- Don't fetch provider facts if openshift_cloud_provider_kind is not set
  (vrutkovs@redhat.com)
- Remove unused openshift_openstack_app_floating_ip (tomas@sedovic.cz)
- Allow custom OpenStack network and subnet (tomas@sedovic.cz)
- Fixup PR #8671 (tomas@sedovic.cz)
- Squash PR 8671 (i.am.emilio@gmail.com)

* Thu Sep 06 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.29.0
- cluster-monitoring: Fix repo/docs URL (fbranczyk@gmail.com)
- cluster-monitoring: Make PVCs optional (fbranczyk@gmail.com)
- Fix issue with cockpit package list (rteague@redhat.com)
- GlusterFS: External uninstall (jarrpa@redhat.com)
- GlusterFS: Ignore external nodes (jarrpa@redhat.com)
- openshifT_aws: removed subnet naming (mwoodson@redhat.com)
- openshift-aws: updating the subnet querying (mwoodson@redhat.com)
- Use first_master_client_binary from hostvars[groups.oo_first_master.0]
  (nakayamakenjiro@gmail.com)
- Do not stop Opensvswitch #9895 (yasensim@gmail.com)
- add OWNERS file for OLM (jpeeler@redhat.com)
- Add OLM to component upgrades (jpeeler@redhat.com)
- Refactor image health checks (mgugino@redhat.com)
- OLM images: use quay for origin (cordell.evan@gmail.com)
- NSX-T fixes #8134 and fixes NSX #8015, PR #8016 (yasensim@gmail.com)
- update olm images to use openshift registry instead of quay
  (cordell.evan@gmail.com)

* Wed Sep 05 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.28.0
- Switch openshift_crio_enable_docker_gc default to False (rteague@redhat.com)
- Add default node groups to support running cri-o runtime (rteague@redhat.com)
- Rework test CI (vrutkovs@redhat.com)

* Wed Sep 05 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.27.0
- Fixing a typo s/Cound/Could/g noticed with an error getting CSR's approved
  (roxenham@redhat.com)
- Add namespaced servicebrokers, serviceclasses and serviceplans to
  admin/edit/view ClusterRoles (marko.luksa@gmail.com)
- Update sync DS after control plane upgrade (vrutkovs@redhat.com)
- Fix incorrect reference to idp['name'] (vrutkovs@redhat.com)
- Add support for ak/orgid at uninstall/scale (e.minguez@gmail.com)
- Configure a list of etcd cipher suites via `etcd_cipher_suites`
  (vrutkovs@redhat.com)
- GlusterFS: Fix registry.yml playbook (jarrpa@redhat.com)

* Tue Sep 04 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.26.0
- Fix etcdctl aliases on etcd hosts (vrutkovs@redhat.com)
- Removing azure publishing tooling. (kwoodson@redhat.com)
- repair container_runtime_extra_storage var values
  (46245+jirib@users.noreply.github.com)
- Convert all remaining registry.access.redhat.com to registry.redhat.io
  (sdodson@redhat.com)
- Update packages in gold image and unsubscribe (e.minguez@gmail.com)
- Configure repositories if RHEL (e.minguez@gmail.com)
- Update openshift_master.py (crmarquesjc@gmail.com)
- Update the value of 'openshift_grafana_prometheus_serviceaccount' Fix
  openshift_grafana prometheus serviceaccount default value  in README,The
  default value is 'promethus','promethus' missed a letter, and there should be
  an e after the h,so it should be 'prometheus' (3168582@qq.com)
- kube_proxy_and_dns: add role that runs standalone kube-proxy + DNS
  (dcbw@redhat.com)
- Don't reset os_firewall_use_firewalld if iptables is inactive during upgrade
  (vrutkovs@redhat.com)
- crio: Don't use file locking (mrunalp@gmail.com)
- Forcing full cluster restart to treat dcs as set (ewolinet@redhat.com)
- Ensure gquota set on slash filesystem (mazzystr@gmail.com)
- Use correct container CLI for docker or cri-o (rteague@redhat.com)
- openshift-prometheus: improve uninstall process (pgier@redhat.com)
- Install NetworkManager on OpenStack (tomas@sedovic.cz)
- Fix incorrect formatting for ca file (vrutkovs@redhat.com)
- Refactor with_items usage with Ansible package module (rteague@redhat.com)
- Move openshift_crio_pause_image to openshift_facts (rteague@redhat.com)
- Update deprecated crio.sock (rteague@redhat.com)
- Remove docker excluder from image prep packages (rteague@redhat.com)
- Support ak/orgid and user/password (e.minguez@gmail.com)
- Fix ASG tagging (mazzystr@gmail.com)
- Fix loop item (cwilkers@redhat.com)
- Ensure sebool container_manage_cgroup on upgrade (mgugino@redhat.com)
- issue #9820 (rcook@redhat.com)
- Add support for ak/orgid for RHEL (e.minguez@gmail.com)
- Enable context selector on console upgrade (spadgett@redhat.com)
- Resolves openshift_release openshift_version conversion for AWS plays
  (mazzystr@gmail.com)
- Add extensions to tasks_from: directives (rteague@redhat.com)
- Remove version_gte_3_10, version_gte_3_11, content_version
  (sdodson@redhat.com)
- Control plane static pods (apiserver, etcd, controller-manager) must get
  highest priority class system-node-critical. Priority admission plugin was
  incorrectly assigning system-cluster-critical to these pods.
  (avesh.ncsu@gmail.com)
- Add retry to openstack heat stack create (tzumainn@redhat.com)
- fix error in cnx conditional regex (derekmcquay@gmail.com)
- Get cluster resources for SDN check in health.yml (miciah.masters@gmail.com)
- Update OLM roles to include resource names (cordell.evan@gmail.com)
- Update example prometheus object to include securityContext field
  (cordell.evan@gmail.com)
- Update aggregated edit role to include verbs (cordell.evan@gmail.com)
- Add mkfs_opts to extra_storage_setup.yml (mail@jkroepke.de)
- Revert "Revert "logging configure fluent to merge_json_log""
  (jcantril@redhat.com)
- bug 1597282. Quote selector to make it valid json (jcantril@redhat.com)
- Don't strip working set in Prometheus (sross@redhat.com)

* Tue Aug 28 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.25.0
- Fix etcd helper function template error (sdodson@redhat.com)
- Remove openshift_is_bootstrapped variable (rteague@redhat.com)
- Fix server csr while loop oc_csr_approve (mgugino@redhat.com)
- Add %%{?dist} back into specfile release (sdodson@redhat.com)
- Prefix identity provider's CA files with identity provider names
  (vrutkovs@redhat.com)
- Dissalow custom CA file path for providers with CA path (vrutkovs@redhat.com)
- Add support for ak/orgid (e.minguez@gmail.com)
- make azure load balancer creation parameters as options (weshi@redhat.com)
- small typo in comment for vpc (emailscottcollier@gmail.com)
- Add networkmanager check to sanity checks (mgugino@redhat.com)
- Ensure default StorageClass reclaimPolicy is set to nil instead of
  emptystring when reclaim_policy undefined (mawong@redhat.com)
- Add failed_when to 'Remove the image stream tag' tasks (mgugino@redhat.com)
- Ensure master image is pre-pulled on upgrade (mgugino@redhat.com)
- Updating logging eventrouter image name to match ose naming pattern
  (ewolinet@redhat.com)
- Rename task name in role rhel_repos (mazzystr@gmail.com)
- Update the naming of openshift on rhv to ovirt (sradco@redhat.com)
- Unify cluster-monitoring install variables (fbranczyk@gmail.com)
- Fix aws elb dictionary fact for dns (mgugino@redhat.com)
- Cleanup upgrades - control plane + registry_auth (mgugino@redhat.com)
- Update pause image value in crio.conf after upgrade (umohnani@redhat.com)
- node kubelet args fail instead of warn (mgugino@redhat.com)

* Mon Aug 27 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.24.0
- openshift-prometheus: change node_exporter service port to 9102
  (pgier@redhat.com)
- Revert "openshift-prometheus: change node_exporter service port to 9101"
  (pgier@redhat.com)

* Sun Aug 26 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.23.0
- Commit to enable standalone master instances in aws (mazzystr@gmail.com)
- SDN check: Expand openshift_client_binary variable (miciah.masters@gmail.com)
- Don't set reclaim policy to empty string (mawong@redhat.com)
- Add support to static pods for etcd helpers (sdodson@redhat.com)
- Creating a priority class for cluster-logging fluentd and configuring fluentd
  to use it (ewolinet@redhat.com)
- Refactor csr approvals: oc_csr_approve (mgugino@redhat.com)
- Change aws launch_config & autoscale group name to contain deployment serial
  (mazzystr@gmail.com)
- Move filters (mateus.caruccio@getupcloud.com)
- Overwrite grafana datasource and dashboards (mateus.caruccio@getupcloud.com)
- Dont fail when datasource or dashboard already exists
  (mateus.caruccio@getupcloud.com)

* Thu Aug 23 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.22.0
- Log driver for JSON should be json-file (umohnani@redhat.com)
- cluster-monitoring: Add port definition to cluster-monitoring-operator
  (fbranczyk@gmail.com)
- cluster-monitoring: conditionally render proxy settings
  (sergiusz.urbaniak@gmail.com)
- Reorder master install tasks (rteague@redhat.com)
- openshift-control-plane: check whether the sync pods are ready before
  selecting nodes (pgier@redhat.com)

* Thu Aug 23 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.21.0
- if the cluster's arch is power (ppc64le) don't install default catalog.
  create v3.11 imagestreams, quickstart, and db-templates that support ppc64le
  (jeyoung@redhat.com)
- GlusterFS: Run kernel_modules.yml once on all nodes (jarrpa@redhat.com)
- Replace deprecated ec2_ami_find module with ec2_ami_facts
  (mazzystr@gmail.com)
- Allow override set scheme (mazzystr@gmail.com)
- Remove old code related to Atomic Enterprise changes (rteague@redhat.com)
- python-scandir was renamed in EPEL (vrutkovs@redhat.com)
- openshift-prometheus: change node_exporter service port to 9101
  (pgier@redhat.com)
- Commit to remove openshift_master_cluster_hostname override
  (mazzystr@gmail.com)
- Change aws launch_config & autoscale group name to contain deployment serial
  (mazzystr@gmail.com)
- Master services are gone in 3.10 (vrutkovs@redhat.com)

* Tue Aug 21 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.20.0
- Pass region to AWS az lookup (cewong@redhat.com)
- SDN check: Use openshift_client_binary (miciah.masters@gmail.com)
- RHV Provider Role and Playbooks (cwilkers@redhat.com)
- Fix backcompat with OpenStack inventory (tomas@sedovic.cz)
- update v3.9 to v3.11 used in the example hosts (gpei@redhat.com)
- GlusterFS: Remove domain from heketi URL (jarrpa@redhat.com)
- Bug 1615787 - Blacklist broker-apb (david.j.zager@gmail.com)
- openshift-metering: Update playbook instructions (chance.zibolski@coreos.com)
- openshift-metering: Update role to use new metering CRD group and schemas and
  images helm operator image (chance.zibolski@coreos.com)
- openshift-metering: Update role to allow creating routes
  (chance.zibolski@coreos.com)
- Removing unnecessary fail task (ewolinet@redhat.com)
- Remove correct duplicated SCC check (vrutkovs@redhat.com)
- Revert "Remove duplicated bootstrapped SCC check" (vrutkovs@redhat.com)
- Revert "Skip base package check for openshift_ca role" (roignac@gmail.com)
- Adding file rollover size and max count policies (ewolinet@redhat.com)
- Rework node initialization procedure to prepull images earlier
  (vrutkovs@redhat.com)
- [RHPAM-1241] - Include RHPAM templates in OpenShift release
  (fspolti@redhat.com)
- Cleanup old sanitize inventory warnings (mgugino@redhat.com)
- Override configmap directly on the install role
  (alberto.rodriguez.peon@cern.ch)
- Correct typo in config variable (AlbertoPeon@users.noreply.github.com)
- Allow to override full Ansible Service Broker config map
  (alberto.rodriguez.peon@cern.ch)
- Changed sample inventory to reflect vars used in heat_stack.yaml.j2
  (dluong@redhat.com)
- Add kuryr namespace isolation support (ltomasbo@redhat.com)

* Mon Aug 20 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.19.0
- 

* Sun Aug 19 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.18.0
- Require Ansible 2.6.2 (rteague@redhat.com)
- Remove 3.10 upgrade playbooks (rteague@redhat.com)
- Use openshift_image_tag for registry-console upgrade (rteague@redhat.com)
- Clean up GCP disks during deprovision (ironcladlou@gmail.com)
- Skip base package check for openshift_ca role (vrutkovs@redhat.com)
- Update search string for registry console (mgugino@redhat.com)
- Revert "Set correct vars for registry console" (gugino.michael@yahoo.com)
- service-catalog: use K8s NamespaceLifecycle admission controller
  (jaboyd@redhat.com)
- remove name from tag (m.judeikis@gmail.com)
- Update sanity_checks.py (cwilkers@redhat.com)
- Provide better error message for json sanity check (cwilkers@redhat.com)
- Remove asb-user-access cluster-role when uninstalling ASB
  (jmontleo@redhat.com)
- Increase maximum number of open file descriptors for dnsmasq
  (ichavero@redhat.com)

* Thu Aug 16 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.17.0
- Update for Bugzilla 1580256 (mazzystr@gmail.com)
- Remove duplicated bootstrapped SCC check (vrutkovs@redhat.com)
- cluster_monitoring_operator: update ClusterRole (lserven@gmail.com)
- Default CFME nodeselector should be a list of str, not a dict
  (vrutkovs@redhat.com)
- Added support for ak when registering hosts (e.minguez@gmail.com)
- Fix audit config interpolation (denis@gladkikh.email)
- SDN check: Ignore node's canonical name (miciah.masters@gmail.com)
- fix 1616278. Modify the default logging namespace (jcantril@redhat.com)
- The file name has changed to heketi_get_key.yml (mbruzek@gmail.com)
- Bug 1615275. Regenerate session_secret if it can't be used with oauth-proxy
  (asherkho@redhat.com)
- Set correct vars for registry console (vrutkovs@redhat.com)
- Updating to only iterate over oo_nodes_to_config list for
  oo_elasticsearch_nodes (ewolinet@redhat.com)
- The l_glusterfs_count is a string need to cast to int for comparison.
  (mbruzek@gmail.com)
- Specify external URL for Prometheus (pat2man@gmail.com)
- Remove unused/broken node cert plays (mgugino@redhat.com)

* Wed Aug 15 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.16.0
- remove the olm project (jiazha@redhat.com)
- fix ASB ClusterServiceBroker removal (jmontleo@redhat.com)
- Cleanup logging and metrics deprecations (mgugino@redhat.com)
- Adding default value for openshift_logging_storage_kind (ewolinet@redhat.com)
- change default sc nam (davis.phillips@gmail.com)
- update the commands to restart master api and controller
  (siva_teja.areti@nokia.com)
- fixing image defaults for logging (ewolinet@redhat.com)
- node restart: check that all vars are defined (vrutkovs@redhat.com)
- Revert "loopback_cluster_name: use api_hostname" (roignac@gmail.com)
- CFME: set default value for openshift_hosted_infra_selector
  (vrutkovs@redhat.com)
- vgchange before vgremove update. (sarumuga@redhat.com)
- To avoid I/O errors, carry out vg deactivate (using vgchange -an) and dmsetup
  remove device. (sarumuga@redhat.com)

* Tue Aug 14 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.15.0
- Update old documentation links (mchappel@redhat.com)
- Replace OpenShift Enterprise references with OpenShift Container Platform
  (mchappel@redhat.com)
- cluster-monitoring: pass through no_proxy setting
  (sergiusz.urbaniak@gmail.com)
- Add CentoOS Origin repo for 310 release (dani_comnea@yahoo.com)
- cluster-monitoring: Fix OCP image names (fbranczyk@gmail.com)
- Update documentation links, docs.openshift.org -> docs.okd.io
  (vrutkovs@redhat.com)
- Require -hyperkube RPMs instead of -master (vrutkovs@redhat.com)
- [uninstall] Remove hyperkube package (norito.agetsuma@gmail.com)
- Don't require etcd RPM to be installable on masters (vrutkovs@redhat.com)
- Don't require fast-datapath channel on RHEL (vrutkovs@redhat.com)
- No longer require SDN to be installed on nodes (vrutkovs@redhat.com)
- Update release artifacts for OLM (cordell.evan@gmail.com)
- GlusterFS: Upgrade playbook (jarrpa@redhat.com)
- Ensure docker package always installed (mgugino@redhat.com)
- re-order and required values (rcook@redhat.com)
- Update route53 dns tasks (mgugino@redhat.com)
- Refactor registry-console template and vars (mgugino@redhat.com)
- Fix the ansible-service-broker URL (jmontleo@redhat.com)
- [bz1552516] set the external url of prometheus (pgier@redhat.com)
- Update console branding and doc URL for OKD (spadgett@redhat.com)
- SCC recouncilation has to run with older oc, before node upgrade
  (vrutkovs@redhat.com)
- Switch to oc set env, since oc env is now removed (maszulik@redhat.com)
- Add functionality for AWS DNS framework and route53 provider
  (mazzystr@gmail.com)
- matching the name values (rcook@redhat.com)
- openshift_cluster_monitoring_operator: Fix enterprise images
  (fbranczyk@gmail.com)
- adding parameters to allow for load balancer creation (rcook@redhat.com)
- Limiting additional fact collection to non-masters since we already collect
  that information for masters (ewolinet@redhat.com)
- Remove unnecessary passlib check (jkr@adorsys.de)

* Sun Aug 12 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.14.0
- Revert "Remove several unused vars" (sdodson@redhat.com)
- Making the app nodes an optional return. (mbruzek@gmail.com)
- 'Wait for node to be ready' task should check that all vars are defined
  (vrutkovs@redhat.com)
- Ensure kernel-modules not installed on atomic (mgugino@redhat.com)
- Remove extra namespaces field on configmap (dymurray@redhat.com)
- Adding min-port to dnsmasq configuration. (rhowe@redhat.com)
- pull in origin imagestream+template updates (bparees@redhat.com)
- Revert "openshift_loadbalancer: remove unused vars" (vrutkovs@redhat.com)
- Remove node CSR approval from upgrade in 3.11 (rteague@redhat.com)
- loopback_cluster_name: use api_hostname (vrutkovs@redhat.com)
- Add quotes to node selector (rteague@redhat.com)
- Bug 1543129 - Add configuration option for ASB local registry namespaces
  (dymurray@redhat.com)
- Omit resetting openshift_logging_elasticsearch_pvc_dynamic if volume is NFS
  (vrutkovs@redhat.com)
- Set claimRef for logging PVC when NFS volume is created previously
  (vrutkovs@redhat.com)
- Fix prometheus annotations typo (vrutkovs@redhat.com)

* Thu Aug 09 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.13.0
- SDN check: Fix parsing time stamp's time zone (miciah.masters@gmail.com)

* Thu Aug 09 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.12.0
- add equals to quoted skopeo argument (sjenning@redhat.com)
- Fix missing input_image name error. (kwoodson@redhat.com)
- excluders cannot be run on Atomic (vrutkovs@redhat.com)
- Add new line in openshift_node defaults (vrutkovs@redhat.com)
- Remove openshift_node_use_persistentlocalvolumes (vrutkovs@redhat.com)
- Remove openshift_node_image_config_latest (vrutkovs@redhat.com)
- Remove openshift_node_use_<sdn> vars (vrutkovs@redhat.com)
- Remove openshift_set_node_ip (vrutkovs@redhat.com)
- Remove openshift_node_proxy_mode (vrutkovs@redhat.com)
- Remove openshift_master_node_labels (vrutkovs@redhat.com)
- Remove openshift_manage_node_is_master (vrutkovs@redhat.com)
- openshift_loadbalancer: remove unused vars (vrutkovs@redhat.com)
- openshift_hosted: remove openshift_push_via_dns flag (vrutkovs@redhat.com)
- openshift_hosted: remove ununsed vars (vrutkovs@redhat.com)
- openshift_facts: remove unused vars (vrutkovs@redhat.com)
- openshift_expand_partition: remove unused vars (vrutkovs@redhat.com)
- openshift_examples: remove unused vars (vrutkovs@redhat.com)
- docker-gc: remove unused var (vrutkovs@redhat.com)
- Remove unused vars from control_plane role (vrutkovs@redhat.com)
- Remove unused vars in etcd role (vrutkovs@redhat.com)
- Be more accuracy for getting def_route_int and def_route_ip
  (bysnupy@hotmail.com)
- Remove master env migration module (mgugino@redhat.com)
- Bump OLM version to 0.6.0 (cordell.evan@gmail.com)
- nuage specific changes for eVDF and some fixes (siva_teja.areti@nokia.com)
- Moving file to the image to fix error. (kwoodson@redhat.com)
- cluster-monitoring: pass through http(s) proxy settings
  (sergiusz.urbaniak@gmail.com)
- Fix openshift_openstack: Add public API Record (akrzos@redhat.com)
- add OSA 3.11 repos for pre-release (m.judeikis@gmail.com)
- Renames CRI-O pause_image to openshift_crio_pause_image.
  (jtudelag@redhat.com)
- pylint: disable travis error (vrutkovs@redhat.com)
- Adding image info to /etc/origin/image.yml on Azure (kwoodson@redhat.com)
- Refactor glusterfs for scaleup (mgugino@redhat.com)
- Quote registry credentials for skopeo (mgugino@redhat.com)
- Commit to enable AWS multi avail zone (mazzystr@gmail.com)
- rollback node ports (m.judeikis@gmail.com)
- Output cert check file to more sensible location (mgugino@redhat.com)
- Bug 1611841 - Allow customizing admin console certificates
  (spadgett@redhat.com)
- Additional cleanup of v1beta1 rbac.authorization (sdodson@redhat.com)
- Fix glusterfs cluster check when condition (mgugino@redhat.com)
- Ensure skopeo and atomic are installed in crt role (mgugino@redhat.com)
- Ensure that monitoring operator has nodes to run (vrutkovs@redhat.com)
- Don't get file checksum, attributes and mime type in stat module calls
  (vrutkovs@redhat.com)
- Bug 1611840 - Correctly set console replicas (spadgett@redhat.com)
- BZ-1608216 Set timeoutSeconds for readinessProbe on Cassandra RCs
  (ruben.vp8510@gmail.com)
- openshift_metering: Add options to use RDS & S3 integrations
  (chance.zibolski@coreos.com)
- add conditional clauses for handling cnx versions (derekmcquay@gmail.com)
- roles/openshift_metering: Fix typo in readme (chance.zibolski@coreos.com)
- Remove exclude-bootstrapped logic (mgugino@redhat.com)
- updating doc for SSL cert (dcritch@redhat.com)
- apply the container_runtime for calico (derekmcquay@gmail.com)
- Enable console picker (spadgett@redhat.com)
- Version_compare filter was renamed to version (vrutkovs@redhat.com)
- Avoid using deprecated syntax for filters in OLM (vrutkovs@redhat.com)
- fix bug 1608269 (jiazha@redhat.com)
- oc_obj should correctly identify  'results': [{}] as 'Object not found'
  (mchappel@redhat.com)
- router-redeploy: don't check that annotations are missing
  (vrutkovs@redhat.com)
- Update Calico versions to the latest (v3.1.3) (mleung975@gmail.com)
- Always ensure master config has proper url upgrade (mgugino@redhat.com)
- Move metrics-server out of openshift-monitoring NS (sross@redhat.com)
- Don't collect node facts on master - these are set during bootstrap
  (vrutkovs@redhat.com)
- Don't set OAUTH_CLIENT_ID in console OAuth secret (spadgett@redhat.com)
- Drop --confirm from migrate storage invocation (maszulik@redhat.com)
- Adding support for an SSL certificate signed by the OpenStack cluster
  (dcritch@redhat.com)

* Thu Aug 02 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.11.0
- Reorganized OpenStack cloud provider documentation (tzumainn@redhat.com)
- Add doc note that kuryr requires openstack cloud provider
  (tzumainn@redhat.com)
- Beginning deprecation of INSTANCE_RAM var in favor of downwardAPI provided
  mem limit vol mount (ewolinet@redhat.com)
- Adding documentation in hosts.example (jcallen@redhat.com)
- Fix ASB user and password defaults (jmontleo@redhat.com)
- Add a license parameter to gcloud command (jcallen@redhat.com)
- adding unmount task below the backup task (bysnupy@hotmail.com)
- Bug 1610224 - Unable to find container log in Elasticsearch when using cri-o
  (rmeggins@redhat.com)
- Added OpenStack security group requirements section (tzumainn@redhat.com)
- Add containerized glusterfs cluster health check (mgugino@redhat.com)
- Allow user to specify local openstack.conf (tzumainn@redhat.com)
- Avoid to call install_node_exporter task during uninstallation.
  (gbsalinetti@extraordy.com)
- Add bool filter to all instances of openshift_use_crio (rteague@redhat.com)
- Cleanup node bootstrap / scaleup code (mgugino@redhat.com)
- Allow shared_non_ops as kibana index mode (farandac@redhat.com)
- AWS: reboot instance before sealing (jchaloup@redhat.com)
- Fix docker reg auth bugs (mgugino@redhat.com)
- Clarified scaling docs, combining master/infra/app sections
  (tzumainn@redhat.com)
- ignore failing dns clean errors when running openstack uninstall playbook
  (tzumainn@redhat.com)
- Updating how we get node names for logging hosts to build sysctl for
  (ewolinet@redhat.com)
- Allow disabling Network Manager managed dns (arun.neelicattu@gmail.com)

* Fri Jul 27 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.10.0
- Disable yum-cron by default on GCP (ccoleman@redhat.com)
- Revert "logging configure fluent to merge_json_log" (jcantril@redhat.com)
- logging configure fluent to merge_json_log (jcantril@redhat.com)
- How to deploy the cluster autoscaler (jchaloup@redhat.com)
- Switch to openshift-node-config in prep for removing openshift start node
  (ccoleman@redhat.com)
- Fix glusterfs storageclass heketi url (mgugino@redhat.com)
- Disable papr on pull requests (sdodson@redhat.com)
- Fedora: Install kernel-modules (mgugino@redhat.com)
- Allow to autoname scale group instances (jchaloup@redhat.com)
- Add cert expiry check to upgrades (mgugino@redhat.com)
- handle symlinks in openshift-ansible container image (jdiaz@redhat.com)
- Add FeatureGates for NamespacedServiceBrokers (jaboyd@redhat.com)
- When the node process is down, don't exit (ccoleman@redhat.com)
- Avoid undefined variable glusterfs_heketi_user_key (sdodson@redhat.com)
- Default openshift_is_atomic to false for openshift_repos.
  (kwoodson@redhat.com)
- Added node selector option for CFME role and fixed formatting issues
  (dluong@redhat.com)
- Remove sections of kuryr documentation that tell user to disable registry
  creation (tzumainn@redhat.com)
- Add step to remove all k8s_ containers (mgugino@redhat.com)
- Add RollingUpdate strategy to dockergc deployment config (rteague@redhat.com)
- Support tabs in resolv.conf (vrutkovs@redhat.com)
- Add boolean to uninstall for docker (mgugino@redhat.com)
- Remove evaluations if group vars are defined or not
  (nakayamakenjiro@gmail.com)
- Add OpenStack node scaleup (tomas@sedovic.cz)
- Run DNS and RHN tasks on new masters only (tomas@sedovic.cz)
- Add the OpenStack master scaleup playbook (tomas@sedovic.cz)

* Mon Jul 23 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.9.0
- Fix order for invoking the hostpath storage task for registry
  (ngompa@datto.com)

* Mon Jul 23 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.8.0
- metrics-server: fix a typo in installer path (vrutkovs@redhat.com)
- installer_checkpoint: use .get to avoid warnings printed in 2.6
  (vrutkovs@redhat.com)
- add firewall rules for node exporter (m.judeikis@gmail.com)
- Add rc code to docker_creds module (mgugino@redhat.com)
- Cope with OpenShift returning no value when an environment variable is an
  empty string (mchappel@redhat.com)
- catalog: add RBAC rules for namespaced brokers (jpeeler@redhat.com)
- allow NFS to be used for registry without marking cluster unsupported
  (bparees@redhat.com)
- Adapt role to latest version of cluster-monitoring-operator
  (fbranczyk@gmail.com)
- Support specifying the rolebinding name (mchappel@redhat.com)
- update imagestreams from origin (bparees@redhat.com)
- AWS: use vpc name instead of cluster id when creating security groups
  (cewong@redhat.com)
- Set log-path = ~/openshift-ansible.log (sdodson@redhat.com)
- Add OLM install scripts (cordell.evan@gmail.com)
- Update the OpenStack Cinder PV example (tomas@sedovic.cz)

* Thu Jul 19 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.7.0
- adding 3.11 tito releaser (aos-team-art@redhat.com)
- Remove alternative oreg vars and update logic (mgugino@redhat.com)

* Thu Jul 19 2018 AOS Automation Release Team <aos-team-art@redhat.com> 3.11.0-0.6.0
- Refactor vars in container-runtime/private (vrutkovs@redhat.com)
- Remove openshift_docker_is_node_or_master - all masters and etcd hosts are
  now nodes (vrutkovs@redhat.com)
- Fix cpu_limit check in eventrouter template (vrutkovs@redhat.com)
- Wait for existing nodes to go Ready before approval (sdodson@redhat.com)
- Fix sanity checks for oreg_auth_user and oreg_auth_password
  (sdodson@redhat.com)
- Remove extra atomic checks (mgugino@redhat.com)
- Remove l_default_container_storage_hosts var (vrutkovs@redhat.com)
- Remove mentions of oo_hosts_containerized_managed_true group
  (vrutkovs@redhat.com)
- only sync actual resource files (bparees@redhat.com)
- update the default oauth-proxy image for logging (jcantril@redhat.com)
- glusterfs: bind created volume to the claim (vrutkovs@redhat.com)
- Adds openshift_fs_inotify_max_user_instances to the node tuned profile.
  (jtudelag@redhat.com)
- use local reference policy for dotnet imagestreams (bparees@redhat.com)
- use local ref policy for all xpaas imagestreams (bparees@redhat.com)
- Adding aggregate rule for new user authorization (smhurley00@gmail.com)
- switch imagestreams to registry.redhat.io (bparees@redhat.com)
- Rename console logoImageName -> branding (spadgett@redhat.com)
- Add scaleup playbook and docs for OpenStack (tomas@sedovic.cz)
- Fix the Neutron DNS docs (tomas@sedovic.cz)
- Uses cluster-wide settings for registry URL and credentials as default values
  for ASB. (mhrivnak@redhat.com)
- Add playbook to update reg-auth credentials (mgugino@redhat.com)
- CLOUD-2699 remove EAP 7.0 templates (ken@zaptillion.net)
- Reconfigure admin console after certificates were redeployed
  (spadgett@redhat.com)
- Add max-size to docker log opts (umohnani@redhat.com)
- Various openshift-cluster-autoscaler changes (amcdermo@redhat.com)
- Remove Get heketi route tasks (nakayamakenjiro@gmail.com)
- generate_pv_pvcs_list: set claimRef for NFS volumes (vrutkovs@redhat.com)
- Fix storageclass setting for NFS (vrutkovs@redhat.com)
- Add support for OpenStack internal DNS (tomas@sedovic.cz)
- oreg url fix (m.judeikis@gmail.com)
- Use glusterfs_name and glusterfs_namespace for heketi url
  (nakayamakenjiro@gmail.com)
- Use service name for heketi url (nakayamakenjiro@gmail.com)
- Update sdn, sdn-ovs, sync, fluentd, descheduler to have system-cluster/node-
  critical priority classes. (avesh.ncsu@gmail.com)
- Install metrics-server pre-upgrade, if metrics (sross@redhat.com)
- Split metrics-server into its own playbook/role (sross@redhat.com)
- bug 1590920. Bump fluent default memory to 756M (jcantril@redhat.com)
- documentation regarding creating and using a static inventory
  (tzumainn@redhat.com)
- Allow openstack inventory.py to output a static inventory
  (tzumainn@redhat.com)
- Update docker registry auth to idempotent (mgugino@redhat.com)
- Force rebuild of config when upgrading to es5 (ewolinet@redhat.com)
- Replace node.js proxy with oauth-proxy (jkarasek@redhat.com)
- Addressing tox failures (ewolinet@redhat.com)
- sdn: don't blow away all existing CNI plugins or config (dcbw@redhat.com)
- Add openshift_docker_gc role to upgrade path (rteague@redhat.com)
- PAPR: install new requirements during upgrade (vrutkovs@redhat.com)
- Remove ec2_group - available upstream (vrutkovs@redhat.com)
- Remove rpm_q - not used (vrutkovs@redhat.com)
- Defining a default for logging_elasticsearch_rollout_override var in es
  handler (ewolinet@redhat.com)
- Only gather hosts when installing logging, otherwise remove sysctl file from
  all (ewolinet@redhat.com)
- Updating to require es node selectors for es5 install, only create sysctl
  files for nodes es will run on and clean up sysctl files when uninstalling
  logging (ewolinet@redhat.com)
- Exclude existing masters from node list for CSR approval during node and
  master scaleup. (abutcher@redhat.com)
- Fixup various TODO sections of code (mgugino@redhat.com)
- Add check for oreg_password by default (mgugino@redhat.com)
- Setup logrotate on nodes once (vrutkovs@redhat.com)
- Add openshift_metering role and playbook (chance.zibolski@coreos.com)
- Remove callback plugin, artifact of a quick installer (vrutkovs@redhat.com)
- Update README (vrutkovs@redhat.com)
- Fix version requirements (vrutkovs@redhat.com)
- Fixing missing _es_version variable (ewolinet@redhat.com)
- action_plugin_test: add necessary vars to support unittests in ansible 2.6
  (vrutkovs@redhat.com)
- ASB migrate: impove result checking (vrutkovs@redhat.com)
- Use ansible 2.6 (vrutkovs@redhat.com)
- Remove old service files before masking them (sdodson@redhat.com)
- switch to registry.redhat.io for infra images (bparees@redhat.com)
- Fix to shebang in bootstrap script (mazzystr@gmail.com)
- Do not delete IAM cert if explicitely requested (jchaloup@redhat.com)
- Ensure nodes created by a scale group have a Name tag (amcdermo@redhat.com)
- gcp: add custom repo when building base image (runcom@redhat.com)
- Sync Fuse console templates (antonin@stefanutti.fr)
- Remove unused node config (mgugino@redhat.com)
- Remove system container bits from etcd (mgugino@redhat.com)
- Allow installs of Node Problem Detector during upgrades (joesmith@redhat.com)
- Clean cloud-init path (mazzystr@gmail.com)
- Add atomic package to base and debug package lists
  (nakayamakenjiro@gmail.com)
- make logging rely on a single SG index (jcantril@redhat.com)
- Accept client certs from node, system:admin, and bootstrap SA
  (sdodson@redhat.com)
- Make openshift_control_plane/check_master_api_is_ready.yml generic
  (sdodson@redhat.com)
- Install OpenShift admin console (spadgett@redhat.com)
- Add a components public playbook (sdodson@redhat.com)
- Wait for API availability before migrating storage, add retries
  (sdodson@redhat.com)
- Uninstall playbook respects openshift_use_openshift_sdn.
  (jtudelag@redhat.com)
- Suppress unexpected error caused by non-English locale during CRI-O
  installation (bysnupy@hotmail.com)
- google-cloud-sdk is x86_64 only (sdodson@redhat.com)
- Add SDN health check (miciah.masters@gmail.com)
- [RHDM-662] - Update RHDM templates on OCP and OSO (fspolti@redhat.com)
- [RHDM-662] - Update RHDM templates on OCP and OSO (fspolti@redhat.com)
- Add simonpasquier to the OWNERS file for prometheus installer
  (pgier@redhat.com)
- hardcode flexvolume path on atomic hosts (hekumar@redhat.com)
- add EAP CD 13 to OS 3.10 (ken@zaptillion.net)
- Allow the 9k-10k port range for Prometheus (spasquie@redhat.com)
- Use OPENSHIFT_CLUSTER env in OpenStack uninstall (tomas@sedovic.cz)
- Azure: update create_and_publish_offer to match new offer/SKUs
  (jminter@redhat.com)
- Add EAP CD 13 imagestream and templates. (ken@zaptillion.net)
- Fix scalegroup upgrades so don't have to delete ASG's. (mwoodson@redhat.com)
- prometheus: upgrade prometheus to 2.3.1 (pgier@redhat.com)
- prometheus: upgrade alertmanager to 0.15.0 (pgier@redhat.com)
- prometheus: upgrade node_exporter to 0.16.0 (pgier@redhat.com)
- add node get-node-logs script (m.judeikis@gmail.com)
- Dedicated etcd nodes should not be added to oo_nodes_to_upgrade
  (vrutkovs@redhat.com)
- Don't upgrade nodes which only have dedicated etcd (vrutkovs@redhat.com)
- fix metrics become syntax (eduardas@redhat.com)
- standalone etcds: make sure etcd facts are set before applying etcd config
  (vrutkovs@redhat.com)
- additional changes to remove discovery plugin from logging
  (jcantril@redhat.com)
- Convert rbac v1beta to v1 (sdodson@redhat.com)
- Increate lbaas_activation_timeout for kuryr-controller (ltomasbo@redhat.com)
- Change multipath prio from const to alua (jarrpa@redhat.com)
- Certificates signed by admins should be approved (ccoleman@redhat.com)
- change become syntax (m.judeikis@gmail.com)
- Migrate old master env files to new location (mgugino@redhat.com)
- Make sure that we use rslave mount propagation (hekumar@redhat.com)
- Update ansible code to preseve path on non-atomic hosts (hekumar@redhat.com)
- Add kubelet-plugins to allowed locations (hekumar@redhat.com)
- Mount kubelet plugins inside controller (hekumar@redhat.com)
- Fix volume location in containarized installs (hekumar@redhat.com)
- updating link to Origin install documentation for latest
  (collins.christopher@gmail.com)
- PAPR: tee update log in a separate file so that it won't be truncated
  (vrutkovs@redhat.com)
- Make fs_inotify_max_user_watches configurable. (avesh.ncsu@gmail.com)
- change heketi logic (m.judeikis@gmail.com)
- Mark ready nodes as accepted during oc_adm_csr approval.
  (abutcher@redhat.com)
- Remove the extra OpenStack network tasks (tomas@sedovic.cz)
- Add infra secgroup rules to the flat secgrp rules (ltomasbo@redhat.com)
- Stop throwing exception except ValueError (nakayamakenjiro@gmail.com)
- Add unit test for validate_json_format_vars (nakayamakenjiro@gmail.com)
- Validate json variable in sanity check (nakayamakenjiro@gmail.com)
- create an imagestream import secret for importing samples
  (bparees@redhat.com)
- Use openshift_is_atomic fact from delegated host (vrutkovs@redhat.com)
- Update etcd pod to 3.2.22 (sdodson@redhat.com)
- Add build_image playbook for OpenStack (tomas@sedovic.cz)
- Enable extended validation of routes by default (miciah.masters@gmail.com)
- Configure node proxy settings on bootstrapped nodes (vrutkovs@redhat.com)
- Bind the node-proxier role to the SDN SA (sross@redhat.com)
- Copying acs-engine output to know location. (kwoodson@redhat.com)
- Disable the wifi collector in node_exporter (spasquie@redhat.com)
- etcd: add clientAuth to server usage (rphillips@redhat.com)
- Bug 1589134- Namespace the CRD variable to prevent collision
  (fabian@fabianism.us)
- Allowing for build artifacts to persist. (kwoodson@redhat.com)
- Gather master facts to make sure cluster_hostname gets appended to no_proxy
  list on nodes (vrutkovs@redhat.com)
- Get acs-engine from new CI namespace (kargakis@protonmail.ch)
- Add Data Grid 7.2 to OpenShift Cloud Platform (remerson@redhat.com)
- Discourage use of openshift_docker_additional_registries (sdodson@redhat.com)
- Ensure SkyDNS is enabled with Kuryr SDN (ltomasbo@redhat.com)
- Make regex for the openshift_pkg_version simpler (nakayamakenjiro@gmail.com)
- Add unit tests for check_pkg_version_format and check_release_format
  (nakayamakenjiro@gmail.com)
- Add format check of openshift_pkg_version and openshift_release
  (nakayamakenjiro@gmail.com)
- Fix openshift_logging on Python3 (christoffer.reijer@basalt.se)
- Correct tests used as filters (rteague@redhat.com)
- Only dump oreg_url when value is defined. (kwoodson@redhat.com)
- openshift-logging use headless service for node discovery
  (jcantril@redhat.com)
- Variablizing vm size for azure. (kwoodson@redhat.com)
- Add a debug statement to the image build to dump tag information.
  (kwoodson@redhat.com)
- Fix openshift_node_config_name in bootstrap.yml. (abutcher@redhat.com)
- Move os_sdn_network_plugin_name into openshift_facts (sdodson@redhat.com)
- Update routers that are defined in openshift_hosted_routers
  (sdodson@redhat.com)
- Clarify example for osm_etcd_image (rteague@redhat.com)
- Bump grafana version (mrsiano@gmail.com)
- Increase watch_retry_timeout for kuryr-daemon (mdulko@redhat.com)
- Find router pods with fully qualified prefixes during upgrade
  (sdodson@redhat.com)
- Grafana: convert grafana_service_targetport in annotations
  (vrutkovs@redhat.com)
- bump xpaas to 1.4.14 (rcernich@redhat.com)
- Deploy grafana if openshift_hosted_grafana_deploy is set
  (vrutkovs@redhat.com)
- Add configmap-generator templates (simaishi@redhat.com)
- Adding owners file for openshift_logging_defaults role (ewolinet@redhat.com)
- Change metrics-server project to "openshift-monitoring" (amcdermo@redhat.com)
- Unify openshift_metrics_server image to standard format (amcdermo@redhat.com)
- Remove openshift_version_gte_3_9 conditions (amcdermo@redhat.com)
- Revert "Revert "Add metrics-server to openshift-metrics playbook""
  (amcdermo@redhat.com)
- Remove haproxy from node package set (sdodson@redhat.com)
- Reconfigure web console after certificates were redeployed
  (vrutkovs@redhat.com)
- azure: disable waagent data disk management (jminter@redhat.com)
- Bug 1558689 - Add iproute to Dockerfile.rhel7 (rteague@redhat.com)
- configure imagePolicyConfig:allowedRegistriesForImport (miminar@redhat.com)
- Deprecate openshift_node_kubelet_args and openshift_node_labels
  (vrutkovs@redhat.com)
- "Fixed ns_update var check" (erj826@bu.edu)
- check_htpasswd_provider: throw error if openshift_master_identity_providers
  is not parsed into a list (vrutkovs@redhat.com)
- no_proxy: use 'append' to properly add a string to a list
  (vrutkovs@redhat.com)
- Update Kuryr CNI template to 3.11 (mdulko@redhat.com)
- change from none to len of the string (davis.phillips@gmail.com)
- manage_node: don't add extra labels to infra/compute/master nodes
  (vrutkovs@redhat.com)
- Maybe the symlink is slightly off? (sdodson@redhat.com)
- openshift_aws: enabled different instance type to be used
  (mwoodson@redhat.com)
- Persist oreg_url in node image (kargakis@protonmail.ch)
- default_storage: configure rolebindings for azure-file storage backend
  (arun.neelicattu@gmail.com)
- default_storage: allow configuring mountOptions and reclaimPolicy
  (arun.neelicattu@gmail.com)
- lib_openshift/oc_storageclass: support mountOptions and reclaimPolicy
  (arun.neelicattu@gmail.com)
- Add node_group_checks to openshift_node_group.yml (rteague@redhat.com)
- Fully qualify all openshift/origin and openshift3/ose images
  (sdodson@redhat.com)
- Change the order of template_var calls in check_htpasswd_provider
  (vrutkovs@redhat.com)
- Set UID,fsGroup and Linux options to cassandra RC's (ruben.vp8510@gmail.com)
- Removing var openshift_logging_es5_techpreview and multi-version structures
  in logging roles (ewolinet@redhat.com)
- Sync grafana deployment. to openshift-monitoring. (mrsiano@gmail.com)
- Set `openshift_node_group_name` for the CNS nodes (tomas@sedovic.cz)
- Revert "Migrate hawkular metrics to a new namespace" (ruben.vp8510@gmail.com)
- Add doc link to check_for_config (adellape@redhat.com)
- Fix invalid openshift_master_audit_config in hosts.example
  (vrutkovs@redhat.com)
- Record etcd static pod version only if master-exec has stdout
  (vrutkovs@redhat.com)
- Revert update to 3.10 registry console template (rteague@redhat.com)
- Fix registry gluster storage variable (bliemli@users.noreply.github.com)
- Add openshift_master_cluster_hostname to no_proxy list (vrutkovs@redhat.com)
- Remove umount /var/lib/docker as docker-storage-setup --reset umount it
  (nakayamakenjiro@gmail.com)
- Fix wrong path to docker storage (nakayamakenjiro@gmail.com)
- Clean up docker-storage in a reliable mannger (nakayamakenjiro@gmail.com)
- bug 1575546. Fix logging eventrouter cpu requests (jcantril@redhat.com)
- PAPR: set docker log driver to journald so that journal artifacts contain
  docker logs too (vrutkovs@redhat.com)
- PAPR: upgrade from 3.10 branch (vrutkovs@redhat.com)
- Fixed add_container_provider.yaml so it uses openshift_management_project
  variable name instead of set name (dluong@redhat.com)
- Add openshift-node entry-point playbooks (rteague@redhat.com)
- Update README.md (SaravanaStorageNetwork@users.noreply.github.com)
- Update README.md (SaravanaStorageNetwork@users.noreply.github.com)
- Updating node group mappings to use an openshift specific tag.
  (kwoodson@redhat.com)
- Add extensions to included task file directives (rteague@redhat.com)
- upgrade: storage migrations should use 'until' to properly retry migrations
  (vrutkovs@redhat.com)
- upgrade: init facts on nodes so that NO_PROXY would include nodes
  (vrutkovs@redhat.com)
- bug 1575903. Default ES memory to 8G (jcantril@redhat.com)
- Appease yamllint (tomas@sedovic.cz)
- Fix nsupdate with allinone (tomas@sedovic.cz)
- master config: join bootstrap settings and sync DS tasks
  (vrutkovs@redhat.com)
- Add prometheus port annotation for Grafana service (pat2man@gmail.com)
- add missing backticks (tzumainn@redhat.com)
- Use ansible systemd module to check service status
  (nakayamakenjiro@gmail.com)
- Fix OpenStack all-in-one cluster deployment (tomas@sedovic.cz)
- Confirm iptables service status by checking command status
  (nakayamakenjiro@gmail.com)
- Makes redeploy-registry-certificates consistent with
  openshift_hosted_manage_registry. (jtudelag@redhat.com)
- Allow for overriding of the elb names to support shorter endings for the
  names (staebler@redhat.com)
- When: openshift_use_kuryr --> all instances updated (i.am.emilio@gmail.com)
- no longer checks if default(false) == true, casts to int
  (i.am.emilio@gmail.com)
- Enable container_manage_crgroup sebool (sdodson@redhat.com)
- Get Kuryr Services checks openshift_use_kuryr==true before starting
  (i.am.emilio@gmail.com)
- Fix S3 storage class path (sarumuga@redhat.com)
- add openstack docs about swift/ceph rados gw backed registry
  (tzumainn@redhat.com)
- Add support for subnet per namespace kuryr feature (ltomasbo@redhat.com)
- [RHPAM-859] - Include RHPAM templates in OpenShift release
  (fspolti@redhat.com)
- Add Prometheus scrape config for openshift-logging (lukas.vlcek@gmail.com)
- Adding sslcacert to additional repos (craig.munro@gmail.com)
- Update glusterfs README about uninstall playbook (sarumuga@redhat.com)

* Fri Jun 15 2018 Scott Dodson <sdodson@redhat.com> 3.11.0-0.1.0
- Initial 3.11 support (sdodson@redhat.com)
- bump to 3.11 (tbielawa@redhat.com)
- Branch for v3.11 (ccoleman@redhat.com)
- Standardize master restart (rteague@redhat.com)
- Enable monitoring to scrape across namespaces (ironcladlou@gmail.com)
- Fix to pass quoted unsafe strings (with characters like *,<,%%) correctly to
  kubelet (avesh.ncsu@gmail.com)
- Bug 1584609 - Update iptablesSyncPeriod in node-config.yaml
  (rteague@redhat.com)
- Bug 1591186 - Skip version and sanity checks for openshift_node_group.yml
  (rteague@redhat.com)
- registry-console: limit pods to masters (vrutkovs@redhat.com)
- Align node startup async tasks with the ExecStartTimeout value
  (sdodson@redhat.com)
- bug 1572493. Update default logging NS in openshift_health_checker
  (jcantril@redhat.com)
- Fix minor indentation (rteague@redhat.com)
- azure: pass image_name into tasks/create_blob_from_vm.yml
  (jminter@redhat.com)
- azure: tag image as valid=true, not valid=True (jminter@redhat.com)
- azure: don't try to print deployment failure message when there isn't one
  (jminter@redhat.com)
- Azure: use empty dict if input image has no tags (pschiffe@redhat.com)
- No code in openshift-ansible should be using CONFIG_FILE
  (ccoleman@redhat.com)
- Add support for hostpath persistent volume definitions (dmsimard@redhat.com)
- Revert "Make SDN read config file from sysconfig" (ccoleman@redhat.com)
- Sync daemonset should start after node configmaps are created to avoid race
  conditions (vrutkovs@redhat.com)
- Switch papr to use our new composite groups (sdodson@redhat.com)
- fix typo to leave only one (wjiang@redhat.com)
- Fix hostname check failure message (mgugino@redhat.com)
- Add retries to SCC check on upgrade (rteague@redhat.com)
- mount host signature lookaside configuration (bparees@redhat.com)
- checks for . (erj826@bu.edu)
- Adding etcd image variables to fix azure deployments. (kwoodson@redhat.com)
- Add master-infra and all-in-one node-configs (sdodson@redhat.com)
- Fix the docs, add additional .parr file description (teleyic@gmail.com)
- Move openshift_node_group to private play (mgugino@redhat.com)
- Don't restart dnsmasq during upgrade (rteague@redhat.com)
- Fix ansible_service_broker role, needs openshift_facts (rteague@redhat.com)
- Migrate HPA scale target refs in storage migration (sross@redhat.com)
- fixes (sdodson@redhat.com)
- Add a bit of detail about how to get configmaps during upgrade
  (sdodson@redhat.com)
- Deploy shim scripts based on the runtime in use (sdodson@redhat.com)
- Upgrade cri-o (sdodson@redhat.com)
- Fix quoting (sdodson@redhat.com)
- roles: openshift_control_plane: move docker scripts to crictl
  (runcom@redhat.com)
- Install cri-tools even when crio isn't in use (sdodson@redhat.com)
- suggestions (sdodson@redhat.com)
- GlusterFS: Add GlusterFS hosts to openshift-hosted/config.yml playbook
  (jarrpa@redhat.com)
- Add some openshift_node_group and openshift_node_group_name docs
  (sdodson@redhat.com)
- Fix sanity_checks typos (mgugino@redhat.com)
- Upgrade router and registry only when these are managed (vrutkovs@redhat.com)
- [WIP] Azure: calculate input image for base and node image
  (pschiffe@redhat.com)
- Migrate hawkular metrics to a new namespace (ruben.vp8510@gmail.com)
- Set openshift_node_group_name for AWS hosts. (abutcher@redhat.com)
- Device_type is deprecated for block devices. Use volume_type instead.
  (abutcher@redhat.com)
- Fix flaky use of `oc process` (ironcladlou@gmail.com)
- Bug 1589015 - Switch to rolling deployment for web console
  (spadgett@redhat.com)
- Move openshift_master_manage_htpasswd into openshift_facts
  (sdodson@redhat.com)
- Bug 1586197 - Increase async timeout (rteague@redhat.com)
- Make the number of service catalog retries configurable (dyasny@gmail.com)
- Remove default selector from sample inventory (tomas@sedovic.cz)
- Check for node-group configmaps during upgrades (mgugino@redhat.com)
- Fix the flake8 and pylint errors (tomas@sedovic.cz)
- Add kuryr label examples to the sample inventory (tomas@sedovic.cz)
- Remove podman from install it creates problems (sdodson@redhat.com)
- Set openshift_node_group_name in OpenStack inventory (tomas@sedovic.cz)
- [WIP] azure - do not tag node images as valid automatically
  (pschiffe@redhat.com)
- Add placeholder for openshift_node_group play (mgugino@redhat.com)
- Check for undefined node_output.results (sdodson@redhat.com)
- Updating fluentd label and wait to be in a single shell rather than running a
  script from /tmp (ewolinet@redhat.com)
- Add Luis Tomas to Kuryr and OpenStack owners (tomas@sedovic.cz)
- add task to import_role (davis.phillips@gmail.com)
- remove svc creation and master config from base tasks in vsphere cloud
  provider (davis.phillips@gmail.com)
- azure: add no_log: true to acs-engine deploy task (jminter@redhat.com)
- allow node config sync controller to handle multiple node labels
  (jminter@redhat.com)
- Fix multimaster OpenStack deployment failure (tomas@sedovic.cz)
- Force openshift_node_group_name for all nodes (mgugino@redhat.com)
- Update ansible_service_broker_node_selector to new version
  (mgugino@redhat.com)
- azure: always build images using ssd-backed VM (jminter@redhat.com)
- azure: ensure cloud provider config is laid down in bootstrap node config
  (jminter@redhat.com)
- Ensure repos only run during prerequisites.yml (mgugino@redhat.com)
- dockergc: change image name to ose-control-plane (gscrivan@redhat.com)
- Remove openshift_dns_ip configuration, not valid in 3.10 (sdodson@redhat.com)
- Do not force-terminate etcd (kargakis@protonmail.ch)
- typo (faust64@gmail.com)
- Remove unused registry-console's imagestream (nakayamakenjiro@gmail.com)
- Ensure packages are latest (sdodson@redhat.com)
- Install cri-tools and podman (sdodson@redhat.com)
- Generalized storage setup for nodes (cwilkers@redhat.com)
- azure: format data disk for docker use (jminter@redhat.com)
- update azure OWNERS (jminter@redhat.com)
- Added container_manage_cgroup in order for systemd to run in pods due to
  update in selinux policy (dluong@redhat.com)

* Wed Jun 06 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.63.0
- Bug 1586366 - Use include_tasks for dynamic task file includes
  (rteague@redhat.com)
- Make prometheus use persistent storage by default (ironcladlou@gmail.com)
- Make Kuryr connect to OpenShift API through LB (mdulko@redhat.com)

* Wed Jun 06 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.61.0
- Apply app label to console replica sets and pods (spadgett@redhat.com)
- Only look for etcd pod on etcd hosts that are colocated w/ master
  (sdodson@redhat.com)
- include tcpdump in azure images (jminter@redhat.com)
- Add a prerequisite check for the nsupdate var (tomas@sedovic.cz)
- Add examples to the documentation (tomas@sedovic.cz)
- Allow empty openshift_openstack_clusterid (tomas@sedovic.cz)
- Update the DNS documentation (tomas@sedovic.cz)
- Decouple the zone from the full cluster dns name (tomas@sedovic.cz)
- Add option to pass OpenStack CA cert to Kuryr (mdulko@redhat.com)

* Tue Jun 05 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.60.0
- 

* Tue Jun 05 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.59.0
- Don't verify java-1.8.0-openjdk (sdodson@redhat.com)
- Stage cri-o packages (sdodson@redhat.com)
- Upgrade cri-o during node upgrade (sdodson@redhat.com)
- Wait up to 10 minutes on image pulls (sdodson@redhat.com)
- Bug 1585648- Set timeout for ASB migration job (workaround for
  kubernetes/kubernetes#62382) (fabian@fabianism.us)
- Revert "Remove unused imagestream of registry-console" (sdodson@redhat.com)
- crio-network: fix definition for systemd (gscrivan@redhat.com)
- container_runtime: do not depend on iptables when using firewalld
  (arun.neelicattu@gmail.com)

* Fri Jun 01 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.58.0
- Fix dockergc images (sdodson@redhat.com)
- iSCSI: Start multipathd (jarrpa@redhat.com)
- cri-o: If defaulting to openshift_release prefix it with v
  (sdodson@redhat.com)
- Updating kibana proxy image to match reg url pattern of other components
  (ewolinet@redhat.com)
- Increase the delay between checking for image pull success
  (sdodson@redhat.com)
- Initialise repos before installing packages (tomas@sedovic.cz)
- fix typo for component (wjiang@redhat.com)
- fix descheduler image version typo (wjiang@redhat.com)
- Splitting output over using stdout_lines due to name formatting
  (ewolinet@redhat.com)
- Adding a placeholder for etcd_ip. (kwoodson@redhat.com)
- Updating logic when we are scaling up to skip health checks
  (ewolinet@redhat.com)

* Fri Jun 01 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.57.0
- Ensure that vsphere is configured for master services
  (davis.phillips@gmail.com)
- Refactor gluster image to use oreg_url (mgugino@redhat.com)
- Approve node CSRs during node upgrade (vrutkovs@redhat.com)
- Update Prometheus to scrape the router metrics (spasquie@redhat.com)
- Avoid kuryr healthcheck ports collision (ltomasbo@redhat.com)

* Thu May 31 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.56.0
- Replace csr 'accepted' field with '{server,client}_accepted' fields and wait
  for server and client requests to be approved. (abutcher@redhat.com)
- added certain vars to openshift_node_group/vars/main.yml
  (mwoodson@redhat.com)
- Remove openshift_web_console_image_name and related (mgugino@redhat.com)
- Refactor etcd_image to support oreg_url (mgugino@redhat.com)
- Bug 1584285 - remove extra space from hostSubnetLength (bleanhar@redhat.com)
- fixed node label bug (mwoodson@redhat.com)
- Skip prepull status check when etcd is being scaled up (vrutkovs@redhat.com)
- Add openshift_facts dependency to TSB role (rteague@redhat.com)
- Clean oc caches after openshift APIs have registered (vrutkovs@redhat.com)
- Wait for Openshift APIs to register themselves (vrutkovs@redhat.com)
- Add steps to debug control plane pods state if components didn't come up
  (vrutkovs@redhat.com)
- Update etcd pod liveness check params (vrutkovs@redhat.com)
- Wait for all control plane pods to become ready (vrutkovs@redhat.com)
- Revert deletion of imagestream and point it from deploymentconfig
  (nakayamakenjiro@gmail.com)
- Add sanity checks for removed component image variables (mgugino@redhat.com)
- Refactor various components to utilize oreg_url (mgugino@redhat.com)
- Port 10256 must be open for service load balancers to work
  (ccoleman@redhat.com)
- Change file permissions on console serving cert (spadgett@redhat.com)
- Remove unused imagestream of registry-console (nakayamakenjiro@gmail.com)
- sync: don't match the script PID when attempting to kill kubelet
  (vrutkovs@redhat.com)
- Create default project nodeSelector for NPD to run on all nodes (including
  masters) (joesmith@redhat.com)
- Ensure public net id is configured for Kuryr SDN (ltomasbo@redhat.com)
- Prometheus nodeselector defaults to hosted nodeselector (vrutkovs@redhat.com)

* Tue May 29 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.54.0
- cluster_monitoring_operator: Wait for CRD to be created (ealfassa@redhat.com)
- Fix master-config.yaml typo (sdodson@redhat.com)
- Drop OVS from package version check (vrutkovs@redhat.com)
- Prepull etcd image (vrutkovs@redhat.com)
- prepull: set async to 0 so that task wouldn't block others
  (vrutkovs@redhat.com)
- Fix wrong command suggestion for oc adm policy reconcile-sccs
  (nakayamakenjiro@gmail.com)
- Update openshift.json acsengine file with unstable for master.
  (kwoodson@redhat.com)
- Specify all node packages and versions for upgrade (rteague@redhat.com)
- Enable metrics scraping of availability apps (ironcladlou@gmail.com)

* Fri May 25 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.53.0
- Use registry short name rather than fqdn (sdodson@redhat.com)
- Upgrade to cluster-monitoring-operator:v0.0.4 (ironcladlou@gmail.com)
- Improve the wording when we block SCC reconciliation (sdodson@redhat.com)
- azure: tag working resource groups with "now", so that they will be pruned if
  necessary (jminter@redhat.com)
- Refactor logging image strings (mgugino@redhat.com)
- master config: remove PodPreset (vrutkovs@redhat.com)

* Fri May 25 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.52.0
- Set imagePolicyConfig.internalRegistryHostname (sdodson@redhat.com)
- docker: Fixup graph directory labels after docker starts (mrunalp@gmail.com)
- fixed volume-config bug; this wasn't being applied appropriately
  (mwoodson@redhat.com)
- Upgrade to cluster-monitoring-operator:v0.0.3 (ironcladlou@gmail.com)
- Revert "openshift_monitor_availability: use oc_obj and oc_process"
  (vrutkovs@redhat.com)
- openshift_monitor_availability: use oc_obj and oc_process
  (vrutkovs@redhat.com)
- Remove insights from origin node image build. (kwoodson@redhat.com)
- Cleaned up openshift_node_group; fixed the labels; added a playbook to invoke
  just the openshift_node_group (mwoodson@redhat.com)

* Wed May 23 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.51.0
- Adding publish to the oo_azure module. (kwoodson@redhat.com)
- Add master IPs to no proxy list so that liveness checks would pass
  (vrutkovs@redhat.com)
- Fix master scaleup play init_fact hosts (mgugino@redhat.com)
- etcd: use etcdctl cluster-health cmd for liveness probe (vrutkovs@redhat.com)
- Package pre-downloads should cause failure if required packages can not be
  found (tbielawa@redhat.com)
- Correct conditional for cloud provider (rteague@redhat.com)
- Quote openshift_release in example inventory. (abutcher@redhat.com)
- Maintaining the same user for removing temp dir (ewolinet@redhat.com)
- Default openshift_use_openshift_sdn to True in openshift_facts
  (vrutkovs@redhat.com)
- Refactor template_service_broker_image (mgugino@redhat.com)
- Cleanup ansible_service_broker_image (mgugino@redhat.com)
- Unify openshift_service_catalog image to standard format (mgugino@redhat.com)
- Pre-pull images before starting API and controller (vrutkovs@redhat.com)
- Install python-docker in prerequisites (vrutkovs@redhat.com)
- Run registry migrations when openshift_hosted_manage_registry
  (vrutkovs@redhat.com)
- Redeploy docker-registry during upgrade only if dc exists
  (vrutkovs@redhat.com)
- etcd runtime: system container can be etcd too (vrutkovs@redhat.com)
- update to oo_glusterfs_to_config as other hosts already configured with NTP.
  (sarumuga@redhat.com)
- bug 1581052: specify the namespace (jiazha@redhat.com)
- Document the openshift_node_port_range variable (dani_comnea@yahoo.com)
- Adding checks to make sure we dont fail if .failed doesnt exist
  (ewolinet@redhat.com)
- Remove old openshift binaries from containerized upgragde
  (mgugino@redhat.com)
- Fix hosts.example openshift_master_oauth_templates (mgugino@redhat.com)
- include base_package playbook in glusterfs config and registry playbooks by
  means of variables. This way NTP will be set using timedatectl in all the
  nodes. (sarumuga@redhat.com)
- Consolidate image diciontaries and strings (mgugino@redhat.com)
- Changing what we check for with is_upgrade set_fact in curator main
  (ewolinet@redhat.com)
- add volume config generation (sjenning@redhat.com)
- Ensure sanity checks are run during upgrade (mgugino@redhat.com)
- Update lib_openshift doc strings to reflect module name (mgugino@redhat.com)
- NTP service is a pre-requisite for glusterfs. Ensure it is enabled and
  started in host. (sarumuga@redhat.com)
- Add openshift_openstack_heat_template_version option (tzumainn@redhat.com)

* Mon May 21 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.50.0
- 

* Mon May 21 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.49.0
- Adding strace and insights-client (kwoodson@redhat.com)
- Updating process for doing a rolling and full cluster upgrades
  (ewolinet@redhat.com)
- fix  The error was: KeyError: 'userNames' (jcantril@redhat.com)
- catalog:  add -cluster-id-configmap-namespace=kube-service-catalog flag
  (jaboyd@redhat.com)
- Specify service port for Prometheus scraping (lukas.vlcek@gmail.com)
- avoid drop_colomun in query. (mrsiano@gmail.com)

* Fri May 18 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.48.0
- API liveness probe: set timeout to 10 sec to prevent API restart if the
  system is busy (vrutkovs@redhat.com)
- removing dnsmasq-node.conf.j2 since nothing is referencing it.
  (kwoodson@redhat.com)
- Fixup SELinux permissions for docker when using a different graph path
  (mrunalp@gmail.com)
- bug 1579723: use ansible_service_broker_dashboard_redirector_route in ASB
  configmap (jiazha@redhat.com)
- RPM is currently the only way to install CRIO (vrutkovs@redhat.com)
- Mention openshift_crio_only in hosts.example (vrutkovs@redhat.com)
- openshift_checks: ignore docker_storage check if only CRIO is used
  (vrutkovs@redhat.com)
- Bug 1579269 - Updating the CRD resource names for migration.
  (smhurley00@gmail.com)
- Adding image publishing capability to azure playbooks. (kwoodson@redhat.com)
- Update Jinja tests used as filters (rteague@redhat.com)
- Add patch to installer image (sdodson@redhat.com)
- Enable monitoring upgrades (ironcladlou@gmail.com)
- Adding support for node images on 3.10 for azure. (kwoodson@redhat.com)
- ASB nodeselector needs to be converted to json to avoid possible python
  unicode issues (vrutkovs@redhat.com)
- Revert "Install node-dnsmasq configuration file" (sdodson@redhat.com)
- Force creating hard- and softlinks (vrutkovs@redhat.com)
- Add default value to openshift_reconcile_sccs_reject_change
  (nakayamakenjiro@gmail.com)
- Stop upgrade when existing sccs will be changed (nakayamakenjiro@gmail.com)
- fix descheduler pod should be critical pod (wjiang@redhat.com)
- pass cluster cidr to proxy (dan@projectcalico.org)
- Fix unwanted removal of openshift.fact file (mgugino@redhat.com)
- Implicitly create node's IST in Kuryr's namespace (mdulko@redhat.com)
- openshift-node: sync script with origin (gscrivan@redhat.com)
- oc_system_container: remove existing service file (vrutkovs@redhat.com)
- Remove correct files when converting to master configs to static
  (vrutkovs@redhat.com)
- PARP: make sure FQDN matches internal IP (vrutkovs@redhat.com)
- PAPR: rename upgrade tasks (vrutkovs@redhat.com)
- PAPR: run upgrade from 3.9 branch (vrutkovs@redhat.com)
- Add new key and remove deprecated key for master network conf
  (mgugino@redhat.com)
- Remove double_upgrade bits (mgugino@redhat.com)
- Add static cluster id label to alerts (ironcladlou@gmail.com)
- Fixes #7009: Hardcoded namespace default in lib_openshift/oc_adm_router
  (jkr@adorsys.de)
- Update requirements.txt (lukasz.gogolin@gmail.com)
- Bug 1561485- get now returns empty instead of error when the namespace is
  missing (fabian@fabianism.us)
- Update generate_pv_pvcs_list.py (davis.phillips@gmail.com)
- add support for vsphere-volume registry and other services
  (davis.phillips@gmail.com)

* Tue May 15 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.47.0
- Updating fluentd docker container mount path (ewolinet@redhat.com)

* Tue May 15 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.46.0
- source azure credentials file (jminter@redhat.com)
- Copy files from openshift_master_generated_config_dir instead using hardlinks
  (mail@jkroepke.de)
- Skip "At least one master is schedulable" when no masters are set in
  oo_masters_to_config (vrutkovs@redhat.com)

* Tue May 15 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.44.0
- Conditionally use upgraded version of Calico for different versions
  (mleung975@gmail.com)

* Mon May 14 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.43.0
- Fix path annotation for the Prometheus (lukas.vlcek@gmail.com)

* Mon May 14 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.42.0
- Don't validate registry certificates when registry is disabled
  (sdodson@redhat.com)
- Node system container no longer depends on master services
  (sdodson@redhat.com)
- Install node-dnsmasq configuration file (vrutkovs@redhat.com)
- repoquery: Omit exclude lines when ignoring excluders
  (mbarnes@fedoraproject.org)
- PAPR: make ansible output verbose and drop ansible.log (vrutkovs@redhat.com)
- PAPR: human-readable output (vrutkovs@redhat.com)
- PAPR: set debug_level (vrutkovs@redhat.com)
- PAPR: always upload systemd logs, use verbose output and split systemd logs
  (vrutkovs@redhat.com)
- Kuryr: Copy CNI plugins as DaemonSet initContainer (mdulko@redhat.com)

* Fri May 11 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.41.0
- 

* Fri May 11 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.40.0
- Readd crio registry variables (mgugino@redhat.com)
- Add in crio pause image code back (umohnani@redhat.com)
- azure: revoke sas url before deleting resource group (jminter@redhat.com)
- Replace and refactor openshift_is_containerized in places
  (mgugino@redhat.com)
- Remove kuryr leftovers before removing the stack (ltomasbo@redhat.com)
- Fix crio pause image syntax (umohnani@redhat.com)
- Using existing nodeselectors for logging components as more sane defaults
  (ewolinet@redhat.com)
- Update playbooks/adhoc/uninstall.yml
  (29396710+drmagel@users.noreply.github.com)
- Remove duplicate slurp of session_secrets (mgugino@redhat.com)
- Cleanup systemcontainer bits (mgugino@redhat.com)
- Add critical pod annotation so that descheduler does not evict itself or does
  not get evicted by others. (avagarwa@redhat.com)
- Make SDN read config file from sysconfig (vrutkovs@redhat.com)
- Don't remove node-config yaml when bootstrapping (vrutkovs@redhat.com)
- Fix undefined variable for existing network config (mgugino@redhat.com)
- Remove containerized lb support (mgugino@redhat.com)
- Fix hard-coded version in master config imageConfig.format
  (mgugino@redhat.com)
- Switch from public subnet id to network id at kuryr (ltomasbo@redhat.com)
- Fixes #8316 - upgrade from 3.9 w/o ASB to 3.10 with ASB fails
  (jmontleo@redhat.com)
- Ensure we're running with admin kubeconfig in several locations
  (sdodson@redhat.com)
- Update cri-o pause image and pause command (umohnani@redhat.com)

* Thu May 10 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.39.0
- Fix tox (sdodson@redhat.com)
- Remove debugging code from #8304 (sdodson@redhat.com)
- Fix upgrade containerized to bootstrap (mgugino@redhat.com)
- Remove bootstrap boolean from gcp provision (mgugino@redhat.com)
- Fix and simplify Installer Checkpoint (rteague@redhat.com)

* Wed May 09 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.38.0
- Ensure existing network facts are set (mgugino@redhat.com)
- Fix etcd runtime detection (sdodson@redhat.com)
- Update cloudforms templates to be in sync with
  roles/openshift_management/files/templates/cloudforms (simaishi@redhat.com)
- Update to CloudForms 4.6.2 templates (simaishi@redhat.com)
- azure: append .vhd to name of blobs written during image build process. Azure
  publishing portal requires input blob names to end in .vhd.
  (jminter@redhat.com)
- Azure: rollback module usage to support ansible 2.4 (jminter@redhat.com)
- Azure: add playbook (kwoodson@redhat.com)
- Fix other configuration for node... (diego.abelenda@camptocamp.com)
- Enable missing feature-gate for VolumeScheduling (also use already defined
  feature-gate entry for node config) (diego.abelenda@camptocamp.com)
- Use local variable instead of global one in template
  (diego.abelenda@camptocamp.com)
- Fix openshift_facts migrated_facts (mgugino@redhat.com)
- Add the EAP CD imagestream to 3.10 (ken@zaptillion.net)
- Bug 1575508 - typo in file name during a rename. (smhurley00@gmail.com)
- Modify rights to allow serviceaccount to change SELinux context of volumes
  (diego.abelenda@camptocamp.com)
- Update daemonset to follow changes in openshift storage example:
  (diego.abelenda@camptocamp.com)
- Add example for local persistent storage image and path
  (diego.abelenda@camptocamp.com)
- Correct Undefined variable (diego.abelenda@camptocamp.com)
- Parametrize provisionner image (diego.abelenda@camptocamp.com)
- Remove redundant default value definition (diego.abelenda@camptocamp.com)
- Copy pasted too fast, "item" variable is not defined outside mkdir loop
  (diego.abelenda@camptocamp.com)
- Parametrize the path for local storage (diego.abelenda@camptocamp.com)
- Add default to False to avoid error when variable is not defined
  (diego.abelenda@camptocamp.com)
- Add possibility to enable Persistent Local Storage using Ansible
  (diego.abelenda@camptocamp.com)
- add run_once for create secret task in calico_master role
  (zhang.lei.fly@gmail.com)
- Convert SDN master facts to openshift_facts defaults (rteague@redhat.com)
- Check console ready replicas instead of curling service (spadgett@redhat.com)
- Remove vendored docker_container module (vrutkovs@redhat.com)
- Compatible with the new prometheus-node-exporter (mmascia@redhat.com)
- Move openshift-checks before node bootstrapping (rteague@redhat.com)

* Mon May 07 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.37.0
- fix (sdodson@redhat.com)
- Configure NetworkManager to ignore calico interfaces (dan@projectcalico.org)

* Mon May 07 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.36.0
- Remove non-bootstrap code (mgugino@redhat.com)

* Sun May 06 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.35.0
- 

* Fri May 04 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.34.0
- Remove outdated api/controllers settings in - /etc/sysconfig
  (vrutkovs@redhat.com)
- Mask and disable etcd service and remove etcd system container
  (vrutkovs@redhat.com)
- Setup node in system container when updating 3.9 to 3.10
  (vrutkovs@redhat.com)
- service catalog: update for v0.1.16 (jaboyd@redhat.com)

* Fri May 04 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.33.0
- Updating to remove annotations from namespace rather than project
  (ewolinet@redhat.com)
- Fix papr.sh target branch for rebase (mgugino@redhat.com)
- Convert etcd to static pods on upgrade (mgugino@redhat.com)
- Resurrect scale group upgrade (rteague@redhat.com)
- docker_image_availability: bz 1570479 (lmeyer@redhat.com)
- PAPR: try to rebase on the latest code (vrutkovs@redhat.com)
- Annotating fluentd pods for promethrus scraping (ewolinet@redhat.com)
- Excluding the eventrouter component when looking for namespaces logging is
  installed in (ewolinet@redhat.com)
- Cleanup master related plays and variables (mgugino@redhat.com)
- bump xpaas to 1.4.12 (rcernich@redhat.com)
- Rework Openshift CLI image pulling (vrutkovs@redhat.com)
- Remove certificates_to_synchronize filter module (rteague@redhat.com)
- Remove clusterNetworkCIDR/hostSubnetLength from default config
  (jtanenba@redhat.com)
- Add support for adding an additional trusted CA (sdodson@redhat.com)
- no_negcache set to default (cdigiovanni@gmail.com)
- azure: add metadata server IP to no_proxy list (mfojtik@redhat.com)
- Fix issue with dnsmasq not caching NXDOMAIN (cdigiovanni@drwholdings.com)
- adding permisions for different resource names (smhurley00@gmail.com)
- Bug 1566924 - Renaming CRDs (smhurley00@gmail.com)
- GlusterFS: Fix setting heketi route (jarrpa@redhat.com)
- Move Node Problem Detector to its own ns, make the ns hard-coded
  (joesmith@redhat.com)
- cadvisor metrics are missing due to worng kubernetes version.
  (mrsiano@gmail.com)
- Fix alert name typo (ironcladlou@gmail.com)
- override cluster default node selector with empty project selector
  (fabian@fabianism.us)
- Bug 1571385- Node selector on pod rather than DC (fabian@fabianism.us)
- Remove system_container image from openshift_cli (mgugino@redhat.com)

* Tue May 01 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.32.0
- Fix redeploy cert for openshift registry (mgugino@redhat.com)
- Remove old content (sdodson@redhat.com)
- Remove older playbooks (sdodson@redhat.com)
- Re-add etcd rpm install path for external etcd (mgugino@redhat.com)
- Remove orphaned byo 3.9 upgrade playbooks (rteague@redhat.com)
- Add templating check in failed_when conditions (rteague@redhat.com)
- Workaround ansible/ansible #39558 (sdodson@redhat.com)
- router - depricate -expose-metrics --metrics-image (pcameron@redhat.com)
- Remove dynamic include in logging_fluentd role (mgugino@redhat.com)
- Add master config filepath checking (mgugino@redhat.com)
- README: add a note about ansible 2.5 version (vrutkovs@redhat.com)
- uninstall node group: fix deprecated syntax (vrutkovs@redhat.com)
- setup.py: exclude ymls which start with a dot (vrutkovs@redhat.com)
- setup.py: revert safe_load_all change (vrutkovs@redhat.com)
- Flush ansible handlers before running restart service tasks in contiv
  (zhang.lei.fly@gmail.com)
- sdn: fix OOM issues with ovs-vswitchd on many-core machines (dcbw@redhat.com)
- etcd scaleup: removed openshift_master_facts role; seems uncessary
  (mwoodson@redhat.com)
- Add auto-heal role and playbooks (jhernand@redhat.com)
- Getting intersection of __default_ops_projects and all projects currently
  installed for case where we reuse installation into logging namespace and
  openshift-logging isnt available (ewolinet@redhat.com)
- sync examples (bparees@redhat.com)
- Remove unused v39 upgrade (mgugino@redhat.com)
- dnsmasq - increase dns-forward-max, cache-size (pcameron@redhat.com)

* Sat Apr 28 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.31.0
- Remove openshift-ansible-catalog-console.js (sdodson@redhat.com)
- Add EAP CD to v3.10 (ken@zaptillion.net)
- Change filename to file in htpasswd auth (mgugino@redhat.com)
- Allow Prometheus scraping of availability namespace (ironcladlou@gmail.com)
- Update etcd restart command (rteague@redhat.com)
- Enable kuryr pool driver selection (ltomasbo@redhat.com)
- Set a lower default TTL for GCP DNS records (ccoleman@redhat.com)
- bug 1568361. Modify persistent directory for logs (jcantril@redhat.com)
- control plane components derived from static pods must be marked critical
  (decarr@redhat.com)

* Thu Apr 26 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.30.0
- missing default variables cause curator to fail (jkarasek@redhat.com)
- Add prerequisites.yml to papr.sh script (mgugino@redhat.com)
- Cert check: verify bootstrap config and skip certs, if it doesn't have
  client-certificate-data (vrutkovs@redhat.com)
- Fail when unable to fetch expected security groups. (abutcher@redhat.com)
- Remove openshift_master_config_dir variable (mgugino@redhat.com)
- Remove openshift_clock role (mgugino@redhat.com)
- install: verify that at least one master is schedulable (vrutkovs@redhat.com)
- Revert "Don't always update dbus but do restart dbus if dnsmasq changed"
  (roignac@gmail.com)
- pre upgrade: fix typo (vrutkovs@redhat.com)

* Wed Apr 25 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.29.0
- Add Alertmanager configuration (ironcladlou@gmail.com)
- Fix a few remaining image expansions (sdodson@redhat.com)
- add critical pod annotation to fluent to avoid eviction (jcantril@redhat.com)
- Update all catalog RBAC to use upstream API (jpeeler@redhat.com)
- update jinja for template (dymurray@redhat.com)
- Fix BZ 1570922. (mrsiano@gmail.com)
- Removing the extra closing parentheses. (mbruzek@gmail.com)
- Add sanity_check for removing filepath and migrate htpasswd
  (mgugino@redhat.com)
- Add max-time option to curl to avoid long running ansible
  (nakayamakenjiro@gmail.com)
- openstack: pylint fix short var name (antonisp@celebdor.com)
- Set the master cluster hostname under OpenStack (tomas@sedovic.cz)
- Replace stdout with content (nakayamakenjiro@gmail.com)
- Add no_proxy to verify to check .svc (nakayamakenjiro@gmail.com)
- Bug 1562783 - Fix egress router setup (rpenta@redhat.com)
- Bug 1538560 - [RFE]rename the project name mux-undefined (nhosoi@redhat.com)
- Fix more indentation issues (contact@seandawson.info)
- Fix oc_version oc_short to report '3.10' (jupierce@redhat.com)
- Add EAP CD to v3.9 and v3.10 (ken@zaptillion.net)
- Add missing attribute on htpasswd object (mgugino@redhat.com)
- Cleanup stale version bits (mgugino@redhat.com)
- Fix defaults (dymurray@redhat.com)
- Add jinja blocks (dymurray@redhat.com)
- Add remove task for route (dymurray@redhat.com)
- Add conditional for route (dymurray@redhat.com)
- Bug 1569220 - Add dashboard redirector feature (dymurray@redhat.com)
- openstack: Do not use layer2 mode for Octavia LB (antonisp@celebdor.com)
- openstack: don't check for kuryr AND lbaas (celebdor@gmail.com)
- openstack: make master direct Octavia compatible (antonisp@celebdor.com)
- openstack: Make LBaaSv2 backend configurable (antonisp@celebdor.com)
- openstack/kuryr: expose origin API on 443 for pods (antonisp@celebdor.com)
- Make Kuryr healthchecks probes optional (ltomasbo@redhat.com)
- Fix method name that was too long (sean.dawson@environment.gov.au)
- Fix linting issues (sean.dawson@environment.gov.au)
- Integrate Node Problem Detector into install (joesmith@redhat.com)
- Add libsemanage-python to base packages prerequisites (tdecacqu@redhat.com)
- Remove meta openshift_etcd role (mgugino@redhat.com)
- Adding missing deprecated var openshift_hosted_metrics_public_url and its
  mapped var (ewolinet@redhat.com)
- Update Cluster Monitoring Operator role docs (ironcladlou@gmail.com)
- Allowing ability to specify a logging namespace and override check to install
  in two different namespaces (ewolinet@redhat.com)
- Allowing way to provide ops and non ops certs for their locations for fluentd
  (ewolinet@redhat.com)
- Forward infra elb port 80 to instance port 80. (abutcher@redhat.com)
- Updating to use existing logging facts over role defaults if available
  (ewolinet@redhat.com)
- Add documentation about subports management for kuryr (ltomasbo@redhat.com)
- Add trailing newline (sean.dawson@environment.gov.au)
- Update unit tests to test sc changes (sean.dawson@environment.gov.au)
- Allow fully qualified provisioner names (sean.dawson@environment.gov.au)

* Mon Apr 23 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.28.0
- master-restart: wait for container to stop before proceeding
  (vrutkovs@redhat.com)
- Remove meta role openshift_etcd_client_certificates (mgugino@redhat.com)
- Add debug level for descheduler role. (avagarwa@redhat.com)
- Add registry checks to v3.10 upgrade (agladkov@redhat.com)
- Set cli image to origin-node / ose-node (sdodson@redhat.com)
- Add a new monitoring availability component (ironcladlou@gmail.com)
- Check and fix registry serviceaccount (agladkov@redhat.com)
- Remove legacy env variables from the registry deploymentconfig if present
  (agladkov@redhat.com)
- spec: own playbooks/common/openshift-master (vrutkovs@redhat.com)
- spec: own inventory dir (vrutkovs@redhat.com)

* Sat Apr 21 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.27.0
- Update minimal hosts.localhost (rteague@redhat.com)
- Ensure /opt/cni/bin exists when running a node in a system container
  (vrutkovs@redhat.com)
- Set default number of registry replicas to 1 (vrutkovs@redhat.com)
- Fix references to openshift_master_api_port (mgugino@redhat.com)
- Remove unused l_openshift_version_check_hosts (mgugino@redhat.com)
- Hardcode htpasswd auth provider filename (mgugino@redhat.com)

* Fri Apr 20 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.26.0
- docker rootdir is different when installing crio (sjenning@redhat.com)
- Use `inventory_hostname` not `openshift_hostname` (tomas@sedovic.cz)
- Set OpenStack VM hostname to the entry in Nova (tomas@sedovic.cz)

* Thu Apr 19 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.25.0
- remove stray LCs on deprovision (jdiaz@redhat.com)

* Thu Apr 19 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.24.0
- Correct default sdn_mtu setting (rteague@redhat.com)
- Fix docker client-ca.crt symlink (sdodson@redhat.com)
- oc_adm_csr - return timeout on other failures (sdodson@redhat.com)
- Append clusterid to default iam role and policy names. (abutcher@redhat.com)
- Allow overriding master/node iam role and policy. (abutcher@redhat.com)

* Thu Apr 19 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.23.0
- Adjust Kuryr CNI definitions for new Docker image (mdulko@redhat.com)
- Update installation/uninstallation/upgrade of descheduler component.
  (avagarwa@redhat.com)
- Provide backup_ext functionality keeping backwards compatibility.
  (kwoodson@redhat.com)
- Add OWNERS files (sdodson@redhat.com)
- Fixing indentation for topology keyfor antiaffinity rules
  (ewolinet@redhat.com)
- Cert check: skip missing entries when a list of certs to check is assembled
  (vrutkovs@redhat.com)
- Create docker cert dir for our registry (sdodson@redhat.com)
- Fix up node and control-plane images (sdodson@redhat.com)
- Revert "crio: Fixup docker SELinux permissions" (sdodson@redhat.com)
- Output useful logs in CI on failure (wk.cvs.github@sydorenko.org.ua)
- [BZ 1567251] make cassandra snapshots configurable (john.sanda@gmail.com)
- Remove etcd_version (vrutkovs@redhat.com)
- cluster_monitoring_operator: Bump to the latest build (ealfassa@redhat.com)
- Update the docker-registry CA symlink on nodes during upgrade
  (ccoleman@redhat.com)
- Bug 1567767 - openshift_logging : Run JKS generation script failed
  (rmeggins@redhat.com)
- Fix wrong handler name masters (mgugino@redhat.com)
- Remove all references to prometheus storage via NFS (sdodson@redhat.com)
- HACK: disable service catalog for HA and update PAPR tests
  (vrutkovs@redhat.com)
- Fix undefined var in openstack dns record setting (tomas@sedovic.cz)
- Add bootstrap and join to node scaleup (tomas@sedovic.cz)
- upgrade: verify API server is accessible before masters upgrade
  (vrutkovs@redhat.com)
- Properly detect etcd version in static pod (vrutkovs@redhat.com)
- No need to stop etcd service on bootstrapped nodes (vrutkovs@redhat.com)
- Rework etcd backup and cmd during upgrade (vrutkovs@redhat.com)
- Use nodename when waiting for node to be ready (vrutkovs@redhat.com)
- Copy master-exec script (vrutkovs@redhat.com)
- Upgrade: don't check master service status for bootstrapped nodes
  (vrutkovs@redhat.com)
- PAPR: check HA install and minor update on all-in-one cluster
  (vrutkovs@redhat.com)
- Remove deprecated networkPluginName from node config template
  (nakayamakenjiro@gmail.com)
- Updating to use preferred only for logging components and removing infra pod
  concept (ewolinet@redhat.com)
- Update queris. (mrsiano@gmail.com)
- Add support for kuryr-controller and kuryr-cni health checks
  (ltomasbo@redhat.com)
- Remove iam_cert23 and use upstream iam_cert. (abutcher@redhat.com)
- Adding anti affinity configurations for ES and kibana pods
  (ewolinet@redhat.com)
- Opening additional ports for CNS block in heat template.
  (jmencak@users.noreply.github.com)
- catalog: use configmap for leader election lock (jpeeler@redhat.com)

* Mon Apr 16 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.22.0
- Don't always update dbus but do restart dbus if dnsmasq changed
  (sdodson@redhat.com)
- Label all-in-one cluster as compute=true (vrutkovs@redhat.com)
- Support azure for management storage class (arun.neelicattu@gmail.com)
- Add storage class defaults for azure (arun.neelicattu@gmail.com)
- Create cloud config when using azure provider (arun.neelicattu@gmail.com)
- Create default storage class when using azure cloud provider
  (arun.neelicattu@gmail.com)
- Support azure cloud provider in facts (arun.neelicattu@gmail.com)
- remove all remaining variable quotation (david_hocky@comcast.com)
- [BZ 1564857] fix image name (john.sanda@gmail.com)
- always add es and es-ops hostname to the es server cert (rmeggins@redhat.com)
- remove manually created ssl cert, use service-cert instead, use default
  service endpoint scrape (jaboyd@redhat.com)
- cluster_monitoring_operator: Don't use cluster-admin role
  (ealfassa@redhat.com)
- fix certificate auth on containerized etcd (david_hocky@comcast.com)
- Allow node-exporter port through GCP firewall (ironcladlou@gmail.com)
- Wipe filesystem metadata from CNS block devices.
  (jmencak@users.noreply.github.com)
- Removing heat template outputs for stack scalability.
  (jmencak@users.noreply.github.com)
- Ensure user provides sane values for openshift_release (mgugino@redhat.com)
- bug 1535300. Default logging namespace to openshift-logging
  (jcantril@redhat.com)
- Set the pid_max value only when lower than certain threshold.
  (jmencak@users.noreply.github.com)
- cluster_monitoring: Bump operator version and adjust related config
  (IndenML@gmail.com)
- Correct link to README.md in openshift-cluster/upgrades for v3.9
  (amcdermo@redhat.com)
- Specify the namespace for better idempotent (bysnupy@hotmail.com)

* Thu Apr 12 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.21.0
- fixed typo, caused unknown char error (asaf@sysbind.co.il)
- Fix missing close parenthesis (iacopo.rozzo@amadeus.com)
- Fix registry x509 SAN omit placeholder (mgugino@redhat.com)
- Revert docker-rhel-push-plugin (mgugino@redhat.com)
- upgrade prometheus 2.1.0 -> 2.2.1 (pgier@redhat.com)
- Only install docker-rhel-push-plugin on enterprise (mgugino@redhat.com)
- Don't block on node start when bootstrapping (ccoleman@redhat.com)
- Cert verification: add more certs to verify (vrutkovs@redhat.com)
- Remove obsolete openshift_docker_disable_push_dockerhub (mgugino@redhat.com)
- Openshift facts: ensure 'disable-attach-detach-reconcile-sync' contains a
  list value (vrutkovs@redhat.com)

* Wed Apr 11 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.20.0
- Upgrade to 3.10 with static pods (ccoleman@redhat.com)
- Update PR docs and link to current bot commands. (abutcher@redhat.com)
- Add oo_etcd_to_config to service_catalog init (mgugino@redhat.com)
- Add missing package docker-rhel-push-plugin (mgugino@redhat.com)
- Add nfs storage_kind check to sanity_checks (mgugino@redhat.com)
- Add openshift-descheduler project. (avagarwa@redhat.com)
- wait_for_pod: wait for deployment to be Complete (vrutkovs@redhat.com)
- Fix OpenStack playbooks on clouds without Cinder (tomas@sedovic.cz)

* Tue Apr 10 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.19.0
- Update dbus before installing dnsmasq (sdodson@redhat.com)
- Removing clear_facts from 3.10 upgrade (rteague@redhat.com)

* Tue Apr 10 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.18.0
- Add missing 'is' in when condiditon for slurp (mgugino@redhat.com)
- Prefix the node-problem-detector with the system: (jchaloup@redhat.com)
- Fix wrong reference to user policy. (mrsiano@gmail.com)
- Change include_ to import_ where possible (mgugino@redhat.com)
- Remove extra ansible.cfg (sdodson@redhat.com)
- Remove utils unit tests (sdodson@redhat.com)
- Remove atomic-openshift-utils (sdodson@redhat.com)
- Switch Node Problem Detector to only pull IfNotPresent, make it configurable
  (joesmith@redhat.com)
- Fix generate_session_secrets (mgugino@redhat.com)
- Update default var to set imagePullPolicy: Always (dymurray@redhat.com)
- Update ASB configmap to set namespace (dymurray@redhat.com)
- Add option to create Cinder registry volume (tomas@sedovic.cz)
- Add the OpenStack load balancer deployment options (tomas@sedovic.cz)
- GlusterFS: enable modprobe in pods that manage bricks (ndevos@redhat.com)
- Calico fixes (dan@projectcalico.org)
- Cleanup node role tasks (mgugino@redhat.com)
- Change set imagepullpolicy to allow for offline install (esauer@redhat.com)
- Update console liveness probe (spadgett@redhat.com)
- Remove unused task-file import (mgugino@redhat.com)
- Remove dead code from openshift_facts (mgugino@redhat.com)
- PAPR: install ASB after CRD backend is used (vrutkovs@redhat.com)
- PARP: Store ansible log file separately (vrutkovs@redhat.com)
- PAPR: remove bootstrap vars to be as close to default as possible
  (vrutkovs@redhat.com)
- Remove some pointless usages of openshift_facts (mgugino@redhat.com)
- catalog: create service and ssl certs for controller manager
  (jaboyd@redhat.com)
- Revert "Add metrics-server to openshift-metrics playbook"
  (amcdermo@redhat.com)
- Remove wire_aggregator and fix runtime config (ccoleman@redhat.com)
- ScheduledJob -> CronJob (vrutkovs@redhat.com)
- Fix path to expiry check playbook (vrutkovs@redhat.com)
- Use 'oc create secret' syntax instead of deprecated 'oc secrets new-sslauth'
  (vrutkovs@redhat.com)
- reorg provision playbooks (tzumainn@redhat.com)
- disable adc reconciler sync for aws (hekumar@redhat.com)

* Fri Apr 06 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.16.0
- Use long form of "scc" resource type in logging facts (hansmi@vshn.ch)
- Add CL role and playbook for Node Problem Detector (joesmith@redhat.com)
- Remove unused/obsolete items from openshift_master_facts (mgugino@redhat.com)
- Allow no sdn's to be specified in sanity checks (mgugino@redhat.com)
- Fix session secrets file and remove old facts (mgugino@redhat.com)
- master: set DEBUG_LOGLEVEL based on openshift_master_debug_level
  (dcbw@redhat.com)
- Refactor openshift_version setting (mgugino@redhat.com)
- Ensure legacy inventories continue to work for infra nodes
  (ccoleman@redhat.com)
- Updating for es5.x image naming and removing restriction for origin only for
  tech preview (ewolinet@redhat.com)
- Implement descheduler cluster lifecycle role and playbook.
  (avagarwa@redhat.com)
- Add resources and migration for new default CRD backend for ASB
  (fabian@fabianism.us)
- GlusterFS: Use custom StorageClass for S3 (jarrpa@redhat.com)
- GlusterFS: Fix missing parameter for registry PVC (jarrpa@redhat.com)
- Fix undefined variable in session secrets (mgugino@redhat.com)
- Updating default image tags to be only vX.Y for origin installs
  (ewolinet@redhat.com)
- Don't install etcd on bootstrapped hosts (vrutkovs@redhat.com)
- When bootstrapping automatically sync node config (ccoleman@redhat.com)
- Fixing crlnumber file missing (bedin@redhat.com)
- Use consistent config location in web console debugging (ccoleman@redhat.com)
- Refactor session authentication secrets (mgugino@redhat.com)
- [1558689] Add iproute to origin-ansible image (rteague@redhat.com)
- catalog: turn on async bindings by default (jpeeler@redhat.com)
- [1561247] Add kubeconfig to openshift_bootstrap_autoapprover
  (rteague@redhat.com)
- Add an ansible role to install OpenShift monitoring platform
  (ealfassa@redhat.com)
- Documents new node upgrade hooks. (jtudelag@redhat.com)
- Skip oc_adm_csr when no bootstrapping is required on GCP
  (ccoleman@redhat.com)
- deploy k8s job for applying hawkular-metrics schema (john.sanda@gmail.com)
- use new filter name for AWS availability zones (jdiaz@redhat.com)
- Fix node upgrade hooks (sdodson@redhat.com)
- Switch the master to always run with bootstrapping on (ccoleman@redhat.com)
- Removing non-null default for cpu_limit for es (ewolinet@redhat.com)
- GlusterFS: Collapse versioned files and directories (jarrpa@redhat.com)
- Fix GCP master haproxy install check (ccoleman@redhat.com)
- crio: don't configure openshift-sdn when disabled (phemmer@chewy.com)
- PAPR - Don't install ASB, do install TSB (sdodson@redhat.com)
- Ensure etcd.conf variables are updated during upgrade (rteague@redhat.com)
- Update deprecated etcd vars in openshfit_cert_expiry (rteague@redhat.com)
- PAPR: don't install TSB on Atomic (vrutkovs@redhat.com)
- Removing hardcoding of configmap_namespace for patching (ewolinet@redhat.com)
- Remove openshift_etcd_facts role (mgugino@redhat.com)
- Cert check playbooks: remove become (vrutkovs@redhat.com)
- Fix s3 image as rhgs3/rhgs-s3-server-rhel7 (sarumuga@redhat.com)
- Upgrade Prometheus AlertManager to v0.14.0 (pasquier.simon@gmail.com)
- Remove etcd_hosts and etcd_urls from openshift_facts (mgugino@redhat.com)
- Convert node-related roles from include_tasks to import_tasks
  (mgugino@redhat.com)
- Bug 1557516- ASB now scheduled on infra nodes (fabian@fabianism.us)
- remove duplicate time import (fabian@fabianism.us)
- fix import (fabian@fabianism.us)
- rebuild dependent modules (fabian@fabianism.us)
- Bug 1555426- yedit now appends an ISO8601 formatted datetime string to file
  backups (fabian@fabianism.us)
- Don't remove pvs when uninstalling openshift_management (ncarboni@redhat.com)
- dockergc: use oc rather than openshift for ex subcommand
  (sjenning@redhat.com)
- Updating default image versions to match curator (ewolinet@redhat.com)
- OpenShift Reference Component Docs (rteague@redhat.com)
- Fix typo in hawkular-cassandra RC (juanlu@redhat.com)
- Adds node hooks: pre, mid and post update hook. (jtudelag@redhat.com)
- Adjusting the default PVC size of MUX file buffer
  (openshift_logging_mux_file_buffer_pvc_size) to the default MUX file buffer
  size (openshift_logging_mux_file_buffer_limit == 2Gi). (nhosoi@redhat.com)

* Tue Mar 27 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.15.0
- Remove etcd_migrate and embedded2external (mgugino@redhat.com)
- Master: change openshift_node include_tasks to import_tasks
  (mgugino@redhat.com)
- Use consistent image references and split out node sync (ccoleman@redhat.com)
- Remove complex version logic and fix f27 build (ccoleman@redhat.com)
- CSR approval should ignore errors when retrying (ccoleman@redhat.com)

* Mon Mar 26 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.14.0
- Split the provision.yml playbook for more flexibility.
  (jmencak@users.noreply.github.com)
- Ensure master-logs works for both origin and enterprise (ccoleman@redhat.com)
- Master components should not have configurable labels (ccoleman@redhat.com)
- Remove duplicated index (thanhha.work@gmail.com)
- Revert "Use region and zone labels added by cloudprovider for scheduling"
  (iacopo.rozzo@amadeus.com)
- Replacing -v with -p for template parameters in oc_process
  (asherkho@redhat.com)
- ensure common_secgrp is used in all server groups (tzumainn@redhat.com)
- package_version check: stop looking for docker (lmeyer@redhat.com)
- minor updates to cleanup secgrp rules (tzumainn@redhat.com)
- Configure dnsmasq before waiting for node (sedgar@redhat.com)
- parameterized flat and master/etcd/node secgroup rules (tzumainn@redhat.com)
- parameterized common openstack secgroup rules (tzumainn@redhat.com)
- fix the ELASTICSEARCH_URL for kibana (jcantril@redhat.com)
- Updating default run hour and minute for curator (ewolinet@redhat.com)
- add in password auth for logging proxy (jcantril@redhat.com)
- Bumping up the default wait time for ES node to be yellow or green, made it
  configurable for larger clusters (ewolinet@redhat.com)
- Make ports pool the default when deploying with kuryr (ltomasbo@redhat.com)
- Allow for using an external openvswitch (flaper87@gmail.com)
- fixing the mounts for the daemonset config to have non subpath mount
  (mwoodson@redhat.com)
- Remove openshift_management beta acknowledement (rteague@redhat.com)
- Add metrics-server to openshift-metrics playbook (amcdermo@redhat.com)
- Limit Prometheus discovery to relevant namespaces (pasquier.simon@gmail.com)
- Don't verify node exporter is running (zgalor@redhat.com)
- roles/openshift-prometheus: fix failing prometheus service discovery scrapes
  (pgier@redhat.com)
- upgrade prometheus v2.0.0 -> v2.1.0 (pgier@redhat.com)
- Use region and zone labels added by cloudprovider for scheduling
  (iacopo.rozzo@amadeus.com)
- Remove deployment_type parameter from default predicates and priorities
  lookup as it was removed from the lookup plugin (iacopo.rozzo@amadeus.com)
- use openshift_image_tag default for prometheus_node_exporter image
  (aweiteka@redhat.com)

* Tue Mar 20 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.13.0
- EFS Provisioner: switch OCP tag to latest (vrutkovs@redhat.com)

* Mon Mar 19 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.12.0
- Bump pyOpenSSL to 17.5.0 (rteague@redhat.com)

* Sat Mar 17 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.11.0
- 

* Fri Mar 16 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.10.0
- Bug 1553576 - Change the self_hostname to ${hostname} in openshift-ansible
  (nhosoi@redhat.com)

* Thu Mar 15 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.9.0
- Use oreg_url for node and master images (ccoleman@redhat.com)
- Label master nodes with openshift-infra=apiserver (jpeeler@redhat.com)

* Thu Mar 15 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.8.0
- Enabling multi vif pool drivers (ltomasbo@redhat.com)
- Update the examples directory for v3.10 (cdaley@redhat.com)
- Pop etcd_port from local_facts file (mgugino@redhat.com)
- Allowing means to provide custom es config entries with
  openshift_logging_es_config (ewolinet@redhat.com)
- GlusterFS - Invoke oc binary with the admin.kubeconfig token rather than
  default token from $HOME/.kube/config (“dani_comnea@yahoo.com”)
- Break up components installs into separate playbooks (staebler@redhat.com)

* Wed Mar 14 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.7.0
- Bug 1548641- Correct arguments to yedit (fabian@fabianism.us)
- Bug 1554828- Nodes are now labeled compute after other labels have been
  applied (fabian@fabianism.us)
- Actually link to the Kuryr docs (tomas@sedovic.cz)
- Link to the Kuryr docs (tomas@sedovic.cz)
- Add link to the Kuryr port pool docs (tomas@sedovic.cz)
- Add Kuryr documentation (tomas@sedovic.cz)

* Wed Mar 14 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.6.0
- Bug 1548541- Conditional for applying defaultNodeSelector now valid
  (fabian@fabianism.us)
- Add support to pre-create subports at each trunk (ltomasbo@redhat.com)
- Fix missing slash in oreg_host (rteague@redhat.com)
- [RHDM-354] - Add RHDM 7.0 GA templates and image streams to Openshift service
  catalog (fspolti@redhat.com)
- Fix references to oc client (mgugino@redhat.com)
- Enable epel-testing repo for ansible-2.4.3 until it goes live
  (sdodson@redhat.com)
- GlusterFS: Add HEKETI_IGNORE_STALE_OPERATIONS to templates
  (jarrpa@redhat.com)
- Replace ${version} with openshift_image_tag (ccoleman@redhat.com)
- Update f27-atomic build to pull images (ccoleman@redhat.com)
- Use internalRegistryHostname when bootstrapping (ccoleman@redhat.com)
- In master bootstrapping mode, use the new openshift_control_plane role
  (ccoleman@redhat.com)
- Add a local bootstrap-node-config.yml on all bootstrap nodes
  (ccoleman@redhat.com)
- Switch to bootstrap script as a default var (ccoleman@redhat.com)
- Prepare the node for dynamic bootstrapping (ccoleman@redhat.com)
- Use an etcd static pod when master bootstrapping is set (ccoleman@redhat.com)
- Add new openshift_control_plane and openshift_sdn roles (ccoleman@redhat.com)
- Changing python regex method from match to search due to variable content
  structure (ewolinet@redhat.com)
- Adding missed line change (ewolinet@redhat.com)
- Ensure that the aggregator is configured during all control plane upgrades
  (sdodson@redhat.com)
- Correctly escape the variable value for regex searching when building patch
  (ewolinet@redhat.com)
- [grafana] Use service account token instead of hardcoded user
  (pep@redhat.com)
- [grafana] Fix wrong references to service account (pep@redhat.com)
- Revert delete tsb upgrade (mgugino@redhat.com)
- crio: Fixup docker SELinux permissions (mrunalp@gmail.com)
- GlusterFS: Don't copy non-existant topology file (jarrpa@redhat.com)
- Require Ansible 2.4.3 (rteague@redhat.com)
- Update roles and playbooks to split cri-o install types (smilner@redhat.com)
- openshift_node: Remove hardcoded cri-o node labels (smilner@redhat.com)
- docker_gc: map the r_docker_gc_node_selectors to pairs (vrutkovs@redhat.com)
- [wip] system containers: ensure Atomic won't reset permissions for
  etcd_data_dir (vrutkovs@redhat.com)
- docker-gc: use openshift_client_binary to support Atomic
  (vrutkovs@redhat.com)
- Bug 1548641- upgrade now properly sets labels and selectors
  (fabian@fabianism.us)
- updated uninstall section (tzumainn@redhat.com)
- re-formatted cinder sections (tzumainn@redhat.com)
- minor formatting (tzumainn@redhat.com)
- updated DNS section to match updated formatting; cleaned up openstack
  configuration section (tzumainn@redhat.com)
- removed dangling link to scale documenation (tzumainn@redhat.com)
- Added subsection regarding OS-specific dependencies (tzumainn@redhat.com)
- remove dangling reference to control-host-image (tzumainn@redhat.com)
- Add section about OPENSHIFT_CLUSTER env variable (tzumainn@redhat.com)
- fixed link (tzumainn@redhat.com)
- Separated post-install doc from README; additional cleanup
  (tzumainn@redhat.com)
- Re-organized OpenStack documentation (tzumainn@redhat.com)
- TSB upgrade remove and reinstall (mgugino@redhat.com)
- Add .default to no_proxy list for ASB. (derekwhatley@gmail.com)
- Updating how the whitelist works -- changing from removing the lines which
  can cause issues when patching lines near the whitelist line to changing the
  current source line to match the new souce line (ewolinet@redhat.com)
- Use variables for docker_gc image (rteague@redhat.com)
- Remove force cache during node upgrade install (mgugino@redhat.com)
- Bug 1550148 - Don't use undefined openshift_version in
  openshift_sanitize_inventory (spadgett@redhat.com)
- Refactor openshift.common.deployment_type (mgugino@redhat.com)
- firewall: allow access to DNS for flannel network (vrutkovs@redhat.com)
- Update curator to use k8s cronjob (jkarasek@redhat.com)
- Remove unused openshift_upgrade_config (mgugino@redhat.com)
- Convert calico to self-hosted install (djosborne10@gmail.com)
- Switch the default network mode to ovs-networkpolicy (ccoleman@redhat.com)
- Allow rcpbind for CNS block in cns-secgrp (openshift_openstack).
  (jmencak@redhat.com)
- Change default grafana ns to openshift-grafana (pep@redhat.com)
- Only run no_log on task that scrapes all inventory variables
  (sdodson@redhat.com)
- Bug 1549220 - configmap still exist after running uninstall playbook for
  logging (nhosoi@redhat.com)
- Fix grafana role node selector check (pep@redhat.com)
- cri-o: configure oci-umount with CRI-O paths (gscrivan@redhat.com)
- added note about any_errors_fatal for ansible.cfg (tzumainn@redhat.com)
- add missing evaluate_groups (tzumainn@redhat.com)
- change to better coding style (wmeng@redhat.com)
- removed cleanup comment (tzumainn@redhat.com)
- corrected rhel unsubscribe role (tzumainn@redhat.com)
- Add openstack uninstall playbook (tzumainn@redhat.com)
- add any_errors_fatal to openstack install playbook (tzumainn@redhat.com)
- add any_errors_fatal to openstack playbooks (tzumainn@redhat.com)
- cockpit-ui: Make it optional (sjr@redhat.com)
- only annotate ops project for ops kibana when using ops (jcantril@redhat.com)

* Wed Mar 07 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.4.0
- During master upgrade reset loopback config (sdodson@redhat.com)

* Wed Mar 07 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.3.0
- 

* Wed Mar 07 2018 Justin Pierce <jupierce@redhat.com> 3.10.0-0.2.0
- Add wait_for_pods to upgrade for hosted components (mgugino@redhat.com)
- Refactor openshift.common.version to openshift_current_version
  (mgugino@redhat.com)
- Fix the DNS server name issue for OpenStack (tomas@sedovic.cz)
- Fix hosted registry upgrade bug (mgugino@redhat.com)
- Remove redeploy after the roll has executed. (kwoodson@redhat.com)
- ansible-quite: set callback_plugins path (vrutkovs@redhat.com)
- Make broker pods run correct versions on upgrade (jpeeler@redhat.com)
- enable iscsid on start and add rpcbind dependencies (m.judeikis@gmail.com)
- fix bz 1550271: restore mpath defaults config (hchen@redhat.com)
- Ensure removed web console extension variables are not set
  (spadgett@redhat.com)
- openstack: set a default when no API LB is needed (antonisp@celebdor.com)
- openshift on openstack: fix non kuryr non API LB (antonisp@celebdor.com)
- kuryr: fix linting tests (antonisp@celebdor.com)
- kuryr: fix API LB and DNS access (tomas@sedovic.cz)
- update LB ports iff the provider is haproxy (antonisp@celebdor.com)
- kuryr: Use openshift-infra namespace (antonisp@celebdor.com)
- kuryr: required pub subnet configuration option (antonisp@celebdor.com)
- sanity_checks: add missing kuryr net_plugin (antonisp@celebdor.com)
- kuryr: Make controller and CNI image configurable (antonisp@celebdor.com)
- Check openstack kuryr prerequisites (antonisp@celebdor.com)
- Kuryr var generation in OSt dynamic inventory (antonisp@celebdor.com)
- kuryr: move to new binding_driver setting config (antonisp@celebdor.com)
- Add s3 and block uninstall sections as well. (sarumuga@redhat.com)
- Temporarily fix Dockerfile until we can find a replacement package
  (ccoleman@redhat.com)
- Bug 1550148 - Fail install if console port does not match API server port
  (spadgett@redhat.com)
- Master scheduler upgrade cleanup (mgugino@redhat.com)
- Add proxy env vars to ASB DC. (derekwhatley@gmail.com)
- Correcting a typo: idle_timout -> idle_timeout (bmorriso@redhat.com)
- docker_image_availability: encode error message (vrutkovs@redhat.com)
- Fix the gluster-s3 pod label used in gluster-s3 service.
  (sarumuga@redhat.com)
- etcd scaleup: use r_etcd_common_etcdctl_command instead of binary path
  (vrutkovs@redhat.com)
- Change default etcd port to 2379 (jpeeler@redhat.com)
- Fixing evaluating if ops deployment needs to skip health check, removing
  logic for determining version, fixing pod check for elasticsearch to get
  running version (ewolinet@redhat.com)
- oc_obj: fail in state=list when return code != 0. (abutcher@redhat.com)
- Fix for gluster-s3 pvc check count. (sarumuga@redhat.com)
- Allow for using an external openvswitch (flaper87@gmail.com)
- Fix rhgs-s3 image name (sarumuga@redhat.com)
- Prometheus reader in continuing to #7064 using the right prometheus sa, with
  view privileges. (mrsiano@gmail.com)
- ansible-quiet.cfg: Don't set callback_plugins path (vrutkovs@redhat.com)
- Add support for instance_ids to ELB provisioner (bmorriso@redhat.com)
- Remove RBAC console template (spadgett@redhat.com)
- crio: Add schedulable check for dockergc-ds (smilner@redhat.com)
- Move common master upgrade playbooks to openshift-master (rteague@redhat.com)
- crio: docker_gc on by default (smilner@redhat.com)
- add stack update case for dry run (tzumainn@redhat.com)
- [bz 1508561] default to secure registry and update certificates
  (kwoodson@redhat.com)
- [BZ 1513706] make concurrenyLimit of heapster's hawkular sink configurable
  (john.sanda@gmail.com)
- Fix redeploy router from openshift_hosted refactor. (kwoodson@redhat.com)
- add stack dry run check (tzumainn@redhat.com)
- prometheus retention 3d (aweiteka@redhat.com)
- add liveness probe for config reload (aweiteka@redhat.com)
- Add kuryr-kubernetes external lock_path * Lock path is now configurable to
  run cni daemon without error. (esevan.park@samsung.com)
- Add openstack stack failures list if stack fails to create
  (tzumainn@redhat.com)
- Add Heat template validation (tzumainn@redhat.com)
- Clarify node system container service unit (mgugino@redhat.com)

* Wed Feb 28 2018 Scott Dodson <sdodson@redhat.com> 3.10.0-0.1.0
- Adding 3.10 releaser (jupierce@redhat.com)
- Add inventory docs for gcp variables (mgugino@redhat.com)
- Add prometheus node-exporter (aweiteka@redhat.com)
- hosts.example: use 3.9 versions in sample inventory file
  (vrutkovs@redhat.com)
- upgrade: skip restart during double upgrade (vrutkovs@redhat.com)
- gcp: Move provisioning of SSH key into separate task
  (chance.zibolski@coreos.com)
- fix when logging metrics user is modified (jcantril@redhat.com)
- bug 1537857. Additional logging proxy metrics fixes (jcantril@redhat.com)
- changed logic due to failures in CI (davis.phillips@gmail.com)
- ntpd/chronyd will now be started before node/master services
  (fabian@fabianism.us)
- Add service catalog components to upgrade (mgugino@redhat.com)
- Add registry GCS storage to hosts.example (sdodson@redhat.com)
- Remove no_log: True from openshift_version calls (sdodson@redhat.com)
- docker: support ADDTL_MOUNTS (gscrivan@redhat.com)
- refactor grafana role (m.judeikis@gmail.com)
- Remove v3_8 upgrade playbooks (vrutkovs@redhat.com)
- Dump verbose curl output and API logs when API doesn't become available.
  (abutcher@redhat.com)
- Start master API in parallel on all masters. (abutcher@redhat.com)
- Update glusterfs-template:  - Add GB_LOGDIR  - failureThreshold as 50 secs
  (sarumuga@redhat.com)
- Don't upgrade master nodes during double upgrade (vrutkovs@redhat.com)
- Don't upgrade nodes for OCP 3.8 (vrutkovs@redhat.com)
- sanity_checks: warn that some OCP versions cannot be installed
  (vrutkovs@redhat.com)
- repo_query: always include package_name in results (vrutkovs@redhat.com)
- Update upgrade README and add 3.7.x -> 3.9.x entry (vrutkovs@redhat.com)
- Remove unused tasks upgrade_facts in openshift_master (mgugino@redhat.com)
- Remove set_fact usage from web-console role (mgugino@redhat.com)
- Retrieve node list from API when testing for nodes with selector.
  (abutcher@redhat.com)
- Update controller port to match containerPort (jpeeler@redhat.com)
- Fix way openshift_openstack_nodes_to_remove parameter is parsed in template
  (tzumainn@redhat.com)
- logging: update README about cri-o (jwozniak@redhat.com)
- Bug 1536651 - logging-mux not working in 3.7.z when logging installed with
  openshift_logging_use_mux=true (nhosoi@redhat.com)
- vsphere svc fix upgrade and datastore fix (davis.phillips@gmail.com)
- logging: allow fluentd to determine cri-o (jwozniak@redhat.com)
- add generic image-and-flavor check that verifies existence and compatibility
  (tzumainn@redhat.com)

* Sun Feb 25 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.53.0
- 

* Sun Feb 25 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.52.0
- Move journald setup to node tasks from master (nakayamakenjiro@gmail.com)
- [BZ 1497408] delete config map, dameon set, and cluster role
  (john.sanda@gmail.com)
- Fix aggregator relative paths (mgugino@redhat.com)
- Fix package tasks ordering in OpenStack playbooks (tomas@sedovic.cz)
- Change openshift_release to openshift_upgrade_target in upgrade
  (mgugino@redhat.com)
- Normalize times we wait on pods to 10s * 60retries (sdodson@redhat.com)
- start_api_server: service catalog healthcheck doesn't require proxy
  (vrutkovs@redhat.com)
- Changing default of openshift_logging_public_master_url to use
  openshift_master_cluster_public_hostname if available (ewolinet@redhat.com)
- Sync v3.8 content (sdodson@redhat.com)
- Sync v3.7 content (sdodson@redhat.com)
- Sync v3.9 content (sdodson@redhat.com)
- Allow branch specific pulls from origin (sdodson@redhat.com)
- Fixing bz1540467 docker-registry env var migration. Adding ability to oc_edit
  complex array style edits. (kwoodson@redhat.com)
- [1537872] Adding seboolean for virt_use_samba (kwoodson@redhat.com)
- Making patching a local_action and ensuring we become:false for local_actions
  (ewolinet@redhat.com)
- Cast string to dict in lib_utils_oo_dict_to_keqv_list (mgugino@redhat.com)
- refine condition for doing ami fetching (jdiaz@redhat.com)
- Add field_selector parameter to oc_obj. (abutcher@redhat.com)
- GlusterFS: Check for groups in template file (jarrpa@redhat.com)
- Updating AMI copying tags to no longer default to parent AMI.
  (kwoodson@redhat.com)
- Remove NoVolumeNodeConflict from 3.9+ (sdodson@redhat.com)

* Fri Feb 23 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.51.0
- 

* Thu Feb 22 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.50.0
- Fix upgrade verify_upgrade_targets (mgugino@redhat.com)
- Ensure wire-aggregator run on 3.7 upgrades (mgugino@redhat.com)
- Add no_log to prevent printing AWS creds (sedgar@redhat.com)
- added ci inventory and groups for containerized (mgugino@redhat.com)

* Thu Feb 22 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.48.0
- Fix openshift_hosted_registry_storage_glusterfs_path (mgugino@redhat.com)
- Revert openshift_portal_net (mgugino@redhat.com)
- skip search for an ami if openshift_aws_ami_map provides one
  (jdiaz@redhat.com)
- Adding node autoapprover. (kwoodson@redhat.com)
- Adding ability to state absent array items with index/curr_value.
  (kwoodson@redhat.com)
- Change image location to CF 4.6 GA from Beta (simaishi@redhat.com)
- Update templates to mount the configmap into the directory the new image
  expects (simaishi@redhat.com)
- Fix for support multi-cluster heketi's topology (chinacoolhacker@gmail.com)

* Tue Feb 20 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.47.0
- Update API healthz check to use uri module (mkhan@redhat.com)
- fixed an oo_filter plugin lib_utils_oo_has_no_matching_selector to do set
  comparison (mwoodson@redhat.com)
- Grafana roles updates. (mrsiano@gmail.com)
- add deprovision playbook for cluster-operator infrastructure
  (jdiaz@redhat.com)
- Add tox test to check for invalid playbook include (rteague@redhat.com)
- Change openshift.common.hostname to inventory_hostname (mgugino@redhat.com)
- Fix openshift-webconsole version check (mgugino@redhat.com)
- add master deprovisioning (jdiaz@redhat.com)
- Adding file locking to yedit. (kwoodson@redhat.com)
- Log troubleshooting info when console install fails (spadgett@redhat.com)
- CRI-O: use /var/run/crio/crio.sock for >=3.9 (gscrivan@redhat.com)
- Fix pvc template by replacing None by lowercase none (toj315@gmail.com)
- GlusterFS: Fix uninstall regression (jarrpa@redhat.com)
- Add prometheus reader role for lightweight privileges. (mrsiano@gmail.com)
- docker_image_availability: encode error message (vrutkovs@redhat.com)
- Tweak things based on feedback (sdodson@redhat.com)
- Update example inventory to drive required hostgroups to the top
  (sdodson@redhat.com)

* Mon Feb 19 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.46.0
- Tolerate OVS 2.6 in 3.10 as well (sdodson@redhat.com)
- hosts.example: openshift_dns_ip should be node-specific (vrutkovs@redhat.com)
- Add target mount for gluster block (m.judeikis@gmail.com)
- Allow for overriding hosted registry_url variables (rteague@redhat.com)
- Link to etcd v3 migration docs rather than suggesting dangerous things
  (sdodson@redhat.com)
- Run openshift_version for image prep (mgugino@redhat.com)
- Remove redundant openshift_hosted_registry_network_default
  (mgugino@redhat.com)
- Correct the usage of bool and str (ghuang@redhat.com)
- kernel module loading fix (m.judeikis@gmail.com)
- add steps in bootstrap playbook to handle updating aws.conf file
  (jdiaz@redhat.com)
- Add cloud config variables to the sample inventory (nelluri@redhat.com)
- Run init/facts for docker upgrade (mgugino@redhat.com)
- quick installer: remove UPGRADE_MAPPINGS (vrutkovs@redhat.com)
- Update quick installer to support 3.9 and 3.8 (vrutkovs@redhat.com)
- Updating deprecation variable check to use a module for cleaner output and
  use run_once to limit to one host. Add flag to skip dep check if desired
  (ewolinet@redhat.com)
- Patch only if the file exists, otherwise we should copy the file in
  (ewolinet@redhat.com)
- Add vsphere section for openshift_node_kubelet_args_dict (ghuang@redhat.com)
- Correctly comparing against the current configmap when making es configmap
  patches (ewolinet@redhat.com)
- add uninstall playbooks for compute/infra scale groups (jdiaz@redhat.com)
- Adding ability to pass content and create files from content.
  (kwoodson@redhat.com)
- Bug 1541946- waiting for master reboot now works behind bastion
  (fabian@fabianism.us)

* Thu Feb 15 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.45.0
-

* Thu Feb 15 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.44.0
-

* Thu Feb 15 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.43.0
- Changing conditional_set_fact from module to action_plugin since it does not
  need to access hosts to be effective and to reduce playbook output
  (ewolinet@redhat.com)
- Revert "Bug 1512825 - add mux pod failed for Serial number 02 has already
  been issued" (mkhan@redhat.com)
- Fix metadata access in OpenStack inventory (tomas@sedovic.cz)
- Adding ability to yedit json files. (kwoodson@redhat.com)
- Simplify double upgrade version logic (mgugino@redhat.com)
- Whenever we create a new es node ignore health checks, changing prometheus pw
  gen for increased secret idempotency (ewolinet@redhat.com)
- oc_adm_csr: Add fail_on_timeout parameter which causes module to fail when
  timeout was reached. (abutcher@redhat.com)
- Adding missing template (ewolinet@redhat.com)
- Move installation of packages before container_runtime to ensure bind mounts
  are avaialable. (kwoodson@redhat.com)
- Use curl --noproxy option for internal apiserver access (takayoshi@gmail.com)
- Revert openshift_version to previous state (mgugino@redhat.com)
- Add openshift_gcp_multizone bool (mgugino@redhat.com)
- Invert logic to decide when to re-deploy certs (sdodson@redhat.com)
- etcd_scaleup: use inventory_hostname when etcd ca host is being picked
  (vrutkovs@redhat.com)
- Fix docker_upgrade variable (mgugino@redhat.com)
- Fix gcp variable warnings (mgugino@redhat.com)
- Disable console install when not 3.9 or newer (spadgett@redhat.com)
- Fix etcd scaleup plays (mgugino@redhat.com)
- Add playbook to install components for cluster operator (cewong@redhat.com)
- Remove cluster_facts.yml from the install.yml (tomas@sedovic.cz)
- Allow for blank StorageClass in PVC creation (jarrpa@redhat.com)
- Add service catalog to be upgraded (jpeeler@redhat.com)
- Remove node start from bootstrap.yml. (abutcher@redhat.com)
- Restart systemd-hostnamed before restarting NetworkManager in node user-data.
  (abutcher@redhat.com)
- additional mounts: specify 'type' in container_runtime_crio_additional_mounts
  (vrutkovs@redhat.com)
- Fix openshift_openstack_provision_user_commands (bdobreli@redhat.com)
- origin-dns: make sure cluster.local DNS server is listed first
  (vrutkovs@redhat.com)
- Fix OpenStack playbooks (tomas@sedovic.cz)
- Backport changes for glusterfs, heketi, s3 and block templates
  (sarumuga@redhat.com)
- Fix indentation to make yamllint happy (vrutkovs@redhat.com)
- Use r_etcd_common_etcdctl_command instead of hardcoded binary name to support
  containerized upgrade (vrutkovs@redhat.com)
- Verify that requested services have schedulable nodes matching the selectors
  (vrutkovs@redhat.com)
- Normalize the time we wait for pods to 5s * 60 retries (sdodson@redhat.com)
- Pause for console rollout (spadgett@redhat.com)
- Fix wording (bdobreli@redhat.com)
- Fix cloud init runcmd templating (bdobreli@redhat.com)
- Note ignored Heat user data changes for openstack (bdobreli@redhat.com)
- Clarify the ansible playbook vs cloud-init (bdobreli@redhat.com)
- Fix openstack cloud-init runcmd templating (bdobreli@redhat.com)
- [openstack] custom user commands for cloud-init (bdobreli@redhat.com)
- Limit host scope during plays (mgugino@redhat.com)
- Fix upgrade-control plane post_control_plane.yml (mgugino@redhat.com)
- erase data only if variable is set. fix block indentatation
  (sarumuga@redhat.com)
- uninstall playbook for GlusterFS (sarumuga@redhat.com)
- Removing prefix and replacing with cidr, pool_start and pool_end variables.
  (mbruzek@gmail.com)
- Make node start options configurable (celebdor@gmail.com)
- Support master node high availability (jihoon.o@samsung.com)

* Fri Feb 09 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.42.0
- xPaaS v1.4.8 for v3.7 (sdodson@redhat.com)
- xPaaS v1.4.8-1 for v3.8 (sdodson@redhat.com)
- xPaaS v1.4.8-1 for v3.9 (sdodson@redhat.com)
- Bump xpaas version (sdodson@redhat.com)
- Bug 1524805- CFME example now works disconnected (fabian@fabianism.us)
- Only try to yaml.load a file if it ends in .yml or .yaml in logging facts
  (ewolinet@redhat.com)
- Set default image tag to openshift_image_tag for services
  (vrutkovs@redhat.com)
- Redeploy router certificates during upgrade only when secure.
  (kwoodson@redhat.com)
- GlusterFS: Fix block StorageClass heketi route (jarrpa@redhat.com)
- changed oc to {{ openshift_client_binary }} (datarace101@gmail.com)
- Use v3.9 web-console image for now (sdodson@redhat.com)
- Adding ability to provide additional mounts to crio system container.
  (kwoodson@redhat.com)
- Remove spaces introduced at the start of the line
  (geoff.newson@googlemail.com)
- Changing the check for the number of etcd nodes (geoff.newson@gmail.com)
- aws ami: make it so the tags from the orinal AMI are used with the newly
  created AMI (mwoodson@redhat.com)
- Setup docker excluder if requested before container_runtime is installed
  (vrutkovs@redhat.com)
- openshift_node: Remove master from aws node building (smilner@redhat.com)
- Use wait_for_connection to validate ssh transport is alive
  (sdodson@redhat.com)
- Bug 1541625- properly cast provided ip address to unicode
  (fabian@fabianism.us)
- Add base package installation to upgrade playbooks (rteague@redhat.com)
- 3.9 upgrade: fix typos in restart masters procedure (vrutkovs@redhat.com)
- quick installer: disable broken test_get_hosts_to_run_on6 test
  (vrutkovs@redhat.com)
- Quick installer: run prerequistes first and update path to main playbook
  (vrutkovs@redhat.com)
- Fix uninstall using openshift_prometheus_state=absent (zgalor@redhat.com)
- Detect config changes in console liveness probe (spadgett@redhat.com)
- Fix master and node system container variables (mgugino@redhat.com)
- Correct the list of certificates checked in openshift_master_certificates
  s.t. masters do not incorrectly report that master certs are missing.
  (abutcher@redhat.com)
- tag fix without ose- (rcook@redhat.com)
- lib_utils_oo_collect: Allow filtering on dot separated keys.
  (abutcher@redhat.com)
- Determine which etcd host is the etcd_ca_host rather than assume it is the
  first host in the etcd host group. (abutcher@redhat.com)
- Attempt to back up generated certificates on every etcd host.
  (abutcher@redhat.com)
- Remove pre upgrade verification step re: etcd ca host. (abutcher@redhat.com)
- Revert "GlusterFS: Remove image option from heketi command" (hansmi@vshn.ch)

* Wed Feb 07 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.41.0
- Allow OVS 2.7 in OCP 3.10 (sdodson@redhat.com)
- GlusterFS: Minor documentation update (jarrpa@redhat.com)
- Make sure to include upgrade_pre when upgrading master nodes
  (sdodson@redhat.com)

* Wed Feb 07 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.40.0
- health checks: tolerate ovs 2.9 (lmeyer@redhat.com)
- Fix docker rpm upgrade install task wording (mgugino@redhat.com)
- Initial support for 3.10 (sdodson@redhat.com)
- add deprovisioning for ELB (and IAM certs) (jdiaz@redhat.com)
- [6632] fix indentation of terminationGracePeriodSeconds var
  (jsanda@redhat.com)

* Tue Feb 06 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.39.0
- Update code to not fail when rc != 0 (kwoodson@redhat.com)
- Upgrades: pass openshift_manage_node_is_master to master nodes during upgrade
  (vrutkovs@redhat.com)
- Updates to configure monitoring container. (kwoodson@redhat.com)
- Move cert SAN update logic to openshift-etcd (rteague@redhat.com)
- Swapping container order for es pod (ewolinet@redhat.com)
- Adding support for ES 5.x tech preview opt in (ewolinet@redhat.com)
- bug 1540799: openshift_prometheus: update alertmanager config file flag
  (pgier@redhat.com)
- parameterize various master scale group bits (jdiaz@redhat.com)
- Use rollout instead of deploy (deprecated) (rteague@redhat.com)
- cri-o: export variables defined in crio-network (gscrivan@redhat.com)

* Mon Feb 05 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.38.0
- Moving upgrade sg playbook to 3.9 (kwoodson@redhat.com)
- remove openshift_upgrade_{pre,post}_storage_migration_enabled from
  failed_when (nakayamakenjiro@gmail.com)
- Fix version handling in 3.8/3.9 control plane upgrades (rteague@redhat.com)
- add S3 bucket cleanup (jdiaz@redhat.com)
- dynamic inventory bug when group exists but its empty (m.judeikis@gmail.com)
- dynamic inventory bug when group exists but its empty (m.judeikis@gmail.com)
- Parameterize user and disable_root options in cloud config
  (nelluri@redhat.com)
- Fix softlinks broken by d3fefc32a727fe3c13159c4e9fe4399f35b487a8
  (Klaas-@users.noreply.github.com)

* Fri Feb 02 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.37.0
- Don't use 'omit' for package module (vrutkovs@redhat.com)
- Adding requirements for logging and metrics (ewolinet@redhat.com)
- Disable master controllers before upgrade and re-enable those when restart
  mode is system (vrutkovs@redhat.com)
- upgrade: run upgrade_control_plane and upgrade_nodes playbooks during full
  upgrade (vrutkovs@redhat.com)

* Fri Feb 02 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.36.0
- Add missing tasks file (sdodson@redhat.com)
- Upgrade to migrate to using push to DNS for registries. (kwoodson@redhat.com)
- Adding defaults for the gcp variables to fix an undefined ansible exception.
  (kwoodson@redhat.com)
- Fix vsphere sanitization (sdodson@redhat.com)
- Set a default for required vsphere variable (sdodson@redhat.com)
- Add python2-crypto package (ccoleman@redhat.com)
- hosts.example: clarify usage of openshift_master_cluster_public_hostname
  (vrutkovs@redhat.com)
- Conditionally create pvcs for metrics depending on whether or not it already
  exists (ewolinet@redhat.com)
- Update hosts examples with a note about scheduling on masters
  (vrutkovs@redhat.com)
- Fixing file write issue. (kwoodson@redhat.com)
- Only perform console configmap ops when >= 3.9 (sdodson@redhat.com)
- Remove playbooks/adhoc/openshift_hosted_logging_efk.yaml (sdodson@redhat.com)
- upgrades: use openshift_version as a regexp when checking
  openshift.common.version (vrutkovs@redhat.com)
- Don't update master-config.yaml with logging/metrics urls >= 3.9
  (sdodson@redhat.com)
- Make master schedulable (vrutkovs@redhat.com)
- Re-add openshift_aws_elb_cert_arn. (abutcher@redhat.com)
- Ignore openshift_pkg_version during 3.8 upgrade (rteague@redhat.com)
- bug 1537857. Fix retrieving prometheus metrics (jcantril@redhat.com)
- Remove master_ha bool checks (mgugino@redhat.com)
- Don't restart docker when re-deploying node certificates (sdodson@redhat.com)
- vsphere storage default add (davis.phillips@gmail.com)

* Wed Jan 31 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.35.0
- add glusterblock support for ansible (m.judeikis@gmail.com)
- Add a bare minimum localhost hosts file (sdodson@redhat.com)
- copy etcd client certificates for nuage openshift monitor
  (siva_teja.areti@nokia.com)
- fix hostvars parameter name (tzumainn@redhat.com)
- remove mountpoint parameter (tzumainn@redhat.com)
- flake cleanup (tzumainn@redhat.com)
- code simplification and lint cleanup (tzumainn@redhat.com)
- Symlink kubectl to oc instead of openshift (mfojtik@redhat.com)
- Rework provisioners vars to support different prefix/version for Origin/OSE
  (vrutkovs@redhat.com)
- add cinder mountpoint to inventory (tzumainn@redhat.com)
- allow setting of kibana env vars (jcantril@redhat.com)
- No longer compare with legacy hosted var (ewolinet@redhat.com)
- Preserving ES dc storage type unless overridden by inventory variable
  (ewolinet@redhat.com)
- Fix: e2e tests failing due to :1936/metrics unaccessible.
  (jmencak@redhat.com)

* Tue Jan 30 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.34.0
- docker_creds: decode docker_config for py3 only if its a string
  (vrutkovs@redhat.com)
- Removing ability to change default cassandra_pvc_prefix based on metrics
  volume name (ewolinet@redhat.com)
- Don't deploy the console if disabled or registry subtype (sdodson@redhat.com)
- [1538960] Correct ability to overried openshift_management_app_template
  (rteague@redhat.com)

* Tue Jan 30 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.33.0
-

* Tue Jan 30 2018 Justin Pierce <jupierce@redhat.com> 3.9.0-0.32.0
- Revert "Revert "use non-deprecated REGISTRY_OPENSHIFT_SERVER_ADDR variable to
  set the registry hostname"" (bparees@users.noreply.github.com)
- Rebase Prometheus example for new scrape endpoints and expose alert manager
  (m.judeikis@gmail.com)
- Revert "use non-deprecated REGISTRY_OPENSHIFT_SERVER_ADDR variable to set the
  registry hostname" (bparees@users.noreply.github.com)
- Bug 1539182: Detect if ClusterResourceOverrides enabled during console
  install (spadgett@redhat.com)
- Fix container_runtime variable typo (mgugino@redhat.com)
- Correct 3.7 to 3.9 upgrade openshift_image_tag (mgugino@redhat.com)
- Fix misaligned ports for sg,elb,api (mazzystr@gmail.com)
- Add GPG keys in the base image and don't install docker (ccoleman@redhat.com)
- Change catalog roles install to use aggregation (jpeeler@redhat.com)
- Make IP object a string (fabian@fabianism.us)
- Add kube service ipaddress to no_proxy list (sdodson@redhat.com)

* Sat Jan 27 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.31.0
- removed references to 'files' dir in spec file (dyocum@redhat.com)
- files in ansible roles do not need to have the path specified to them when
  referenced by a builtin module, i.e., copy: (dyocum@redhat.com)
- moving files to their correct <role>/files dir for the openshift_web_console
  and template_service_broker roles (dyocum@redhat.com)

* Fri Jan 26 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.30.0
- Removing dependency on the extra stroage device. (kwoodson@redhat.com)

* Fri Jan 26 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.29.0
- Add prometheus annotations to console service (spadgett@redhat.com)
- Add resource requests to console template (spadgett@redhat.com)
- ignore 'users' field in oc_group module (jdiaz@redhat.com)

* Fri Jan 26 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.28.0
- Updating deprecations to use callback plugin (ewolinet@redhat.com)
- Run console pods on the master (spadgett@redhat.com)

* Fri Jan 26 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.26.0
- docker_image_availability: containerized overrides (lmeyer@redhat.com)
- Remove old assetConfig from master-config.yaml (spadgett@redhat.com)
- Don't emit assetConfig on 3.9 (sdodson@redhat.com)

* Fri Jan 26 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.25.0
- [1502838] Correct certificate alt name parsing (rteague@redhat.com)
- sync imagestreams+templates from origin master for v3.9 (bparees@redhat.com)
- node: specify bind option to /root/.docker (gscrivan@redhat.com)
- [1530403] Improve etcd group error message (rteague@redhat.com)
- Only automatically restart if cluster is in yellow or green state
  (ewolinet@redhat.com)
- openshift_manage_node: Label nodes in one pass (vrutkovs@redhat.com)
- Redeploy etcd certificates during upgrade when etcd hostname not present in
  etcd serving cert SAN. (abutcher@redhat.com)
- Create swapoff module (mgugino@redhat.com)
- Label masters with node-role.kubernetes.io/master. This PR also sets these
  labels and scheduling status during upgrades (vrutkovs@redhat.com)
- [1537946] Correct conditional check for GlusterFS IPs (rteague@redhat.com)
- Remove unused node.lables from openshift_facts (mgugino@redhat.com)
- Change dnsmasq Requires to Wants.
  https://bugzilla.redhat.com/show_bug.cgi?id=1532960 (rchopra@redhat.com)
- Set a default for openshift_hosted_registry_storage_azure_blob_realm
  (sdodson@redhat.com)
- openshift_prometheus: remove block duration settings (pgier@redhat.com)

* Wed Jan 24 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.24.0
- Update CF 4.6 Beta templates in openshift_management directory
  (simaishi@redhat.com)
- installer: increase content width for commands, which may output URLs
  (vrutkovs@redhat.com)
- Only rollout console if config changed (spadgett@redhat.com)
- Protect master installed version during node upgrades (mgugino@redhat.com)
- [1506866] Update haproxy.cfg.j2 (rteague@redhat.com)
- Split control plane and component install in deploy_cluster
  (ccoleman@redhat.com)
- Add clusterResourceOverridesEnabled to console config (spadgett@redhat.com)
- [1537105] Add openshift_facts to flannel role (rteague@redhat.com)
- PyYAML is required by openshift_facts on nodes (ccoleman@redhat.com)
- Move origin-gce roles and playbooks into openshift-ansible
  (ccoleman@redhat.com)
- Directly select the ansible version (ccoleman@redhat.com)
- use non-deprecated REGISTRY_OPENSHIFT_SERVER_ADDR variable to set the
  registry hostname (bparees@redhat.com)
- update Dockerfile to add boto3 dependency (jdiaz@redhat.com)
- Lowercase node names when creating certificates (vrutkovs@redhat.com)
- NFS Storage: make sure openshift_hosted_*_storage_nfs_directory are quoted
  (vrutkovs@redhat.com)
- Fix etcd scaleup playbook (mgugino@redhat.com)
- Bug 1524805- ServiceCatalog now works disconnected (fabian@fabianism.us)
- [1506750] Ensure proper hostname check override (rteague@redhat.com)
- failed_when lists are implicitely ANDs, not ORs (vrutkovs@redhat.com)
- un-hardcode default subnet az (jdiaz@redhat.com)
- Ensure that node names are lowerecased before matching (sdodson@redhat.com)
- Bug 1534020 - Only set logging and metrics URLs if console config map exists
  (spadgett@redhat.com)
- Add templates to v3.9 (simaishi@redhat.com)
- Use Beta repo path (simaishi@redhat.com)
- CF 4.6 templates (simaishi@redhat.com)
- Add ability to mount volumes into system container nodes (mgugino@redhat.com)
- Fix to master-internal elb scheme (mazzystr@gmail.com)
- Allow 5 etcd hosts (sdodson@redhat.com)
- Remove unused symlink (sdodson@redhat.com)
- docker_creds: fix python3 exception (gscrivan@redhat.com)
- docker_creds: fix python3 exception (gscrivan@redhat.com)
- docker: use image from CentOS and Fedora registries (gscrivan@redhat.com)
- crio: use Docker and CentOS registries for the image (gscrivan@redhat.com)
- The provision_install file ends in yml not yaml! Ansible requirement
  clarification. (mbruzek@gmail.com)

* Tue Jan 23 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.23.0
- docker_image_availability: enable skopeo to use proxies (lmeyer@redhat.com)
- Install base_packages earlier (mgugino@redhat.com)
- allow uninstalling AWS objects created by prerequisite playbook
  (jdiaz@redhat.com)
- Bug 1536262: Default console and TSB node selector to
  openshift_hosted_infra_selector (spadgett@redhat.com)
- Migrate master-config.yaml asset config (spadgett@redhat.com)
- Fix master scaleup play (mgugino@redhat.com)
- use admin credentials for tsb install operations (bparees@redhat.com)
- Fix etcd-upgrade sanity checks (mgugino@redhat.com)
- Bug 1536253: Pass `--config` flag on oc commands when installing console
  (spadgett@redhat.com)
- Fix enterprise registry-console prefix (sdodson@redhat.com)
- [release-3.7] Fix enterprise registry console image prefix
  (sdodson@redhat.com)
- [release-3.6] Fix enterprise registry console image prefix
  (sdodson@redhat.com)
- Bug 1512825 - add mux pod failed for Serial number 02 has already been issued
  (nhosoi@redhat.com)
- Remove old console asset config (spadgett@redhat.com)
- Add support for Amazon EC2 C5 instance types (rteague@redhat.com)
- Fix provider network support at openstack playbook (ltomasbo@redhat.com)

* Fri Jan 19 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.22.0
- Fix OpenStack readme (tomas@sedovic.cz)
- Quick installer: deprecate upgrades (vrutkovs@redhat.com)
- Fix node scaleup plays (mgugino@redhat.com)
- Rollout console after template service broker install (spadgett@redhat.com)
- Use openshift_is_containerized instead of openshift_is_atomic when installing
  etcd (vrutkovs@redhat.com)
- Bug 1535947: Fix missing task in metrics, logging uninstall playbooks
  (spadgett@redhat.com)
- Make openshift_web_console_prefix defaults like other components
  (sdodson@redhat.com)
- Allow for firewalld on atomic host (sdodson@redhat.com)
- Drop the testing repo var from openstack readme (tomas@sedovic.cz)
- Add Azure to support openshift_cloudprovider_kind (wehe@redhat.com)
- bug 1523047. Annotate ops projects with an .operation prefix
  (jcantril@redhat.com)
- Pull openshift_image_tag from oo_masters_to_config rather oo_first_master.
  (abutcher@redhat.com)
- Ensure atomic_proxies are configured with docker (mgugino@redhat.com)
- Default install_result when reloading generated facts. (abutcher@redhat.com)
- health checks: update required pkg versions (lmeyer@redhat.com)
- health checks: factor out get_required_version (lmeyer@redhat.com)
- package_version check: reuse get_major_minor_version (lmeyer@redhat.com)
- Rework default TSB prefix and imagename to match other services
  (vrutkovs@redhat.com)
- Add new grafana playbook. (mrsiano@gmail.com)
- Remove duplication in node acceptance playbook and setup master groups so
  that we can use the first master's ansible_ssh_user when delegating.
  (abutcher@redhat.com)
- Setting default storage_class_names for when calling
  openshift_logging_elasticsearch role (ewolinet@redhat.com)
- adding check if secret auth is needed (shawn.hurley21@gmail.com)
- adding asb auth as a secret. (shawn.hurley21@gmail.com)
- Ensure we are running oc execs against running pods (ewolinet@redhat.com)
- Automatic profile setting for tuned 2.9 (jmencak@redhat.com)
- Fix flake8 errors in utils/test (vrutkovs@redhat.com)
- kibana checks: use six.moves instead of ImportError (vrutkovs@redhat.com)

* Wed Jan 17 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.21.0
- Add call to 3.8 playbook in 3.9 upgrade (sdodson@redhat.com)
- Remove 3.8 and 3.9 specific steps right now (sdodson@redhat.com)
- Exclude 3.9 packages during 3.8 upgrade (sdodson@redhat.com)
- fix typos (sdodson@redhat.com)
- Ensure openshift_client_binary is set (sdodson@redhat.com)
- Add init/main.yml to etc-upgrade (mgugino@redhat.com)
- Fix a typo in "Determine if growpart is installed" (vrutkovs@redhat.com)
- Check rc for commands with openshift_client_binary and failed_when
  (vrutkovs@redhat.com)
- Update console config for API changes (spadgett@redhat.com)
- include elasticsearch container name (jvallejo@redhat.com)
- openshift_checks: repair adhoc list-checks mode (lmeyer@redhat.com)
- Remove tuned-profiles from list of master packages upgraded
  (sdodson@redhat.com)
- Add missing task that got dropped in a refactor (sdodson@redhat.com)
- Web Console: use a different var for asset config (vrutkovs@redhat.com)
- Document the inventory change (tomas@sedovic.cz)
- Move the OpenStack dynamic inventory from sample (tomas@sedovic.cz)
- fix bug 1534271 (wmeng@redhat.com)
- Don't use from ansible.module_utils.six as its no longer available in Ansible
  2.4 (vrutkovs@redhat.com)
- Add console RBAC template (spadgett@redhat.com)
- Setup master groups in order to use the master group's ansible_ssh_user to
  pull bootstrap kubeconfig. (abutcher@redhat.com)
- adding ability to add network policy objects. (shawn.hurley21@gmail.com)
- add python2-boto3 package for centos-based origin-ansible container image
  (jdiaz@redhat.com)
- adding ability to interact with network resources. (shawn.hurley21@gmail.com)
- Adding .ini to inventory_ignore_extensions (bedin@redhat.com)

* Mon Jan 15 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.20.0
- Adjust openstack provider dependencies versions (bdobreli@redhat.com)
- Fix openstack provider playbook name in docs (bdobreli@redhat.com)
- Install web console on upgrade (spadgett@redhat.com)
- Add var for controller to enable async bindings (jpeeler@redhat.com)
- Add cluster-operator playbook directory. (abutcher@redhat.com)
- Move s3 & elb provisioning into their own playbooks s.t. they are applied
  outside of the openshift_aws master provisioning tasks. (abutcher@redhat.com)
- Update to AWS EC2 root vol size so that Health Check tasks pass
  (mazzystr@gmail.com)
- Configure Kuryr CNI daemon (mdulko@redhat.com)
- Clean up host-local IPAM data while nodes are drained (danw@redhat.com)

* Fri Jan 12 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.19.0
-

* Fri Jan 12 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.18.0
-

* Fri Jan 12 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.17.0
- Update latest image streams and templates (sdodson@redhat.com)
- Use webconsole.config.openshift.io/v1 API group (spadgett@redhat.com)
- Add missing v3.9 gluster templates (sdodson@redhat.com)
- Spelling and grammar changes to the advanced-configuration.md file.
  (mbruzek@gmail.com)
- Fixing openshift_hosted variable. (kwoodson@redhat.com)
- Update deployment and apiserver with new certs (jpeeler@redhat.com)
- Move more plugins to lib_utils (mgugino@redhat.com)
- Add the ability to specify a timeout for node drain operations
  (sdodson@redhat.com)
- Add defaults for openshift_pkg_version (mgugino@redhat.com)
- Fix typo in the advanced config docs (tomas@sedovic.cz)
- Write guide on setting up PVs with Cinder (tomas@sedovic.cz)
- Allow using server names in openstack dynamic inv (tomas@sedovic.cz)
- Specify the Cinder version in the inventory (tomas@sedovic.cz)
- Add documentation example (joel.pearson@gmail.com)
- Add blockstorage version for openstack (joel.pearson@gmail.com)
- logging: fix jinja filters to support py3 (vrutkovs@redhat.com)
- Ability to specify override tolerations via the buildconfig overrider
  (cdaley@redhat.com)
- Chmod temp dirs created on localhost (mgugino@redhat.com)
- Bug 1532787 - Add empty node selector to openshift-web-console namespace
  (spadgett@redhat.com)
- Remove become statements (mgugino@redhat.com)
- Bug 1527178 - installation of logging stack failed: Invalid version specified
  for Elasticsearch (nhosoi@redhat.com)
- Limit host group scope on control-plane upgrades (mgugino@redhat.com)
- Refactor version and move some checks into sanity_checks.py
  (mgugino@redhat.com)
- Updating tsb image names and template (ewolinet@redhat.com)
- Ensure that openshift_facts role is imported whenever we rely on
  openshift_client_binary (sdodson@redhat.com)
- Add key check for facts_for_clusterrolebindings (nakayamakenjiro@gmail.com)
- Update web console template (spadgett@redhat.com)
- Use openshift_node_use_openshift_sdn when doing a containerized node upgrade
  (vrutkovs@redhat.com)
- Add iptables save handler (ichavero@redhat.com)
- Fix: change import_role to include_role (mgugino@redhat.com)
- docker storage setup for ami building (jdiaz@redhat.com)
- ensure containerized bools are cast (mgugino@redhat.com)
- Properly cast crio boolean variables to bool (mgugino@redhat.com)
- Build containerized host group dynamically (mgugino@redhat.com)
- install base_packages on oo_all_hosts (mgugino@redhat.com)
- Add key existing check to collect facts for rolebidings
  (nakayamakenjiro@gmail.com)
- 3.9 upgrade: remove openshift.common.service_type (vrutkovs@redhat.com)
- container-engine: move registry_auth.yml before pull (gscrivan@redhat.com)
- Fix error in variable in comment (mscherer@users.noreply.github.com)
- Switch back to dynamic include_role in logging loops (sdodson@redhat.com)
- Use Contiv version 1.2.0 (flamingo@2thebatcave.com)
- Contiv multi-master and other fixes (flamingo@2thebatcave.com)
- Add missing dependency on openshift_facts (sdodson@redhat.com)
- upgrades: set openshift_client_binary fact when running on oo_first_master
  host (vrutkovs@redhat.com)
- Install web console server (spadgett@redhat.com)
- Remove become=no from various roles and tasks (mgugino@redhat.com)
- Don't overwrite node's systemd units for containerized install
  (vrutkovs@redhat.com)
- Migrate to import_role for static role inclusion (sdodson@redhat.com)
- docker_upgrade_check: skip repoquery calls on containerized setups
  (vrutkovs@redhat.com)
- Adding logic to disable and reenable external communication to ES during full
  restart (ewolinet@redhat.com)
- Provide example on how to use osm_etcd_image in a disconnected and
  containerized installation (tkarlsso@redhat.com)
- crio: create /etc/sysconfig/crio-storage (gscrivan@redhat.com)
- crio: configure proxy variables (gscrivan@redhat.com)
- Fix docker_image_availability checks (mgugino@redhat.com)
- Install node packages in one task instead of 3 (mgugino@redhat.com)
- Don't hardcode the network interface in the openshift_logging_mux role
  (nkinder@redhat.com)
- failure_summary: make sure msg is always a string (vrutkovs@redhat.com)
- Adding logic to do a full cluster restart if we are incrementing our major
  versions of ES (ewolinet@redhat.com)
- test_oc_scale: add more scale test cases (vrutkovs@redhat.com)
- test_oc_scale: fix test docstrings (vrutkovs@redhat.com)
- Import prerequisites.yml for OpenStack (tomas@sedovic.cz)
- Set the correct path to the openstack.conf file (tomas@sedovic.cz)
- Return a openshift_node_labels as a dict (tomas@sedovic.cz)
- Remove last of openshift_node role meta-depends (mgugino@redhat.com)
- OpenStack provisioning -- support cns. (jmencak@redhat.com)
- Fix yaml syntax error in the sample inventory (tomas@sedovic.cz)
- Adding ability to update ami drive size. (kwoodson@redhat.com)
- Add origin- prefix to ASB image (fabian@fabianism.us)
- lint issues (davis.phillips@gmail.com)
- add vsphere examples in hosts.example (davis.phillips@gmail.com)
- add template and vsphere.conf (davis.phillips@gmail.com)
- add vsphere cloud providers (davis.phillips@gmail.com)
- Fix wrong indentation (ichavero@redhat.com)
- Fix yaml indentation (ichavero@redhat.com)
- Add iptables rules for flannel (ichavero@redhat.com)

* Wed Jan 03 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.16.0
- Add gluster 3.9 templates (sdodson@redhat.com)
- Add in-tree CI scripts (mgugino@redhat.com)

* Wed Jan 03 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.15.0
-

* Wed Jan 03 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.14.0
- Cast openshift_docker_use_system_container to bool (mgugino@redhat.com)
- Correct kublet_args cloud-provider directories (mgugino@redhat.com)
- Updating logging_facts to be able to pull values from config maps yaml files,
  use diffs to keep custom changes, white list certain settings when creating
  diffs (ewolinet@redhat.com)
- Add docker auth credentials to system container install (mgugino@redhat.com)
- Move wait_for_pods to it's own play openshift_hosted (mgugino@redhat.com)
- Remove oauth_template bits from openshift_facts (mgugino@redhat.com)

* Tue Jan 02 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.13.0
- Bug 1527178 - installation of logging stack failed: Invalid version specified
  for Elasticsearch (nhosoi@redhat.com)
- Remove bootstrap.yml from main.yml in openshift_node role
  (mgugino@redhat.com)

* Tue Jan 02 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.12.0
-

* Mon Jan 01 2018 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.11.0
- aws: Fix misnamed variable in provisioning_vars.yml.example
  (mbarnes@fedoraproject.org)
- Fix container_runtime openshift_containerized_host_groups
  (mgugino@redhat.com)
- Remove references to deployment_type (mgugino@redhat.com)
- Must directly specify google-cloud-sdk version (ccoleman@redhat.com)
- daemonset config role. (kwoodson@redhat.com)
- Move validate_hosts to prerequisites.yml (mgugino@redhat.com)
- Move sanity_checks into custom action plugin (mgugino@redhat.com)
- Remove openshift.common.{is_atomic|is_containerized} (mgugino@redhat.com)
- Adding support for docker-storage-setup on overlay (kwoodson@redhat.com)
- Add gcloud to the installer image (ccoleman@redhat.com)
- Remove some small items from openshift_facts (mgugino@redhat.com)
- Relocate filter plugins to lib_utils (mgugino@redhat.com)
- Fix hosted_reg_router selectors (mgugino@redhat.com)
- set repos after registration: convert to match task -> import_role model.
  (markllama@gmail.com)
- Remove openshift_node_facts role (mgugino@redhat.com)
- Move node group tags to openshift_aws_{master,node}_group.
  (abutcher@redhat.com)
- Add CentOS-OpenShift-Origin37 repo template. (abutcher@redhat.com)
- Adding no_log to registry_auth. (kwoodson@redhat.com)
- Fix rhel_repos disable command (mazzystr@gmail.com)
- Fix rhel_subscribe boolean (mgugino@redhat.com)
- Move repo and subscribe to prerequisites (mgugino@redhat.com)
- Deprecate using Ansible tests as filters (rteague@redhat.com)
- Removing config trigger for ES DC, updating to use a handler to rollout ES at
  the end of a deployment, allowing for override with variable
  (ewolinet@redhat.com)
- openshift_logging_{fluentd,mux}_file_buffer_limit mismatch
  (nhosoi@redhat.com)
- Update version check to Ansible 2.4.1 (rteague@redhat.com)
- Remove openshift_node_facts part 1 (mgugino@redhat.com)
- Validate node hostname and IP address (rteague@redhat.com)
- Add missing openshift_service_type (mgugino@redhat.com)
- prevent TSB pods from spinning on inappropriate nodes (jminter@redhat.com)
- Add readiness probe to kuryr controller pod (ltomasbo@redhat.com)

* Thu Dec 14 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.10.0
- Bump requirements.txt to Ansible 2.4.1 (rteague@redhat.com)
- Commit to stabalize RHSM operations.  This code is derived from contrib
  (mazzystr@gmail.com)
- Contiv systemd fixes (flamingo@2thebatcave.com)
- Combine openshift_master/vars with defaults (mgugino@redhat.com)
- crio: change socket path to /var/run/crio/crio.sock (gscrivan@redhat.com)
- Remove version requirement from openvswitch package, since listed version got
  removed from repo (riffraff@hobbes.alephone.org)

* Thu Dec 14 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.9.0
- etcd: use Fedora /latest/ instead of hardcoding the version
  (gscrivan@redhat.com)
- docker: use Fedora /latest/ instead of hardcoding the version
  (gscrivan@redhat.com)
- upgrade node mark 2 (mgugino@redhat.com)
- Refactor node upgrade to include less serial tasks (mgugino@redhat.com)
- fix 1519808. Only annotate ops projects when openshift_logging_use_ops=true
  (jcantril@redhat.com)
- Ensure that clients are version bound (sdodson@redhat.com)
- Support for making glusterfs storage class a default one.
  (jmencak@redhat.com)
- Add support for storage classes to openshift_prometheus role.
  (jmencak@redhat.com)
- Do not escalate privileges in logging stack deployment task
  (iacopo.rozzo@amadeus.com)
- Multimaster openshift+contiv fixes (landillo@cisco.com)
- Sync latest image-streams and templates (alexandre.lossent@cern.ch)

* Tue Dec 12 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.8.0
- Remove empty openshift_hosted_facts role (mgugino@redhat.com)
- Refactor upgrade codepaths step 1 (mgugino@redhat.com)

* Tue Dec 12 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.7.0
- Remove bad openshift_examples symlink (rteague@redhat.com)
- Changing the node group format to a list. (kwoodson@redhat.com)
- Bump RPM version requirement (sdodson@redhat.com)
- Clarify version selection in README (mgugino@redhat.com)

* Tue Dec 12 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.6.0
- add openshift_master_api_port var to example inventory (jdiaz@redhat.com)
- Allow 2 sets of hostnames for openstack provider (bdobreli@redhat.com)

* Mon Dec 11 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.5.0
- Remove unneeded embedded etcd logic (mgugino@redhat.com)

* Mon Dec 11 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.4.0
- Copying upstream fix for ansible 2.4 ec2_group module. (kwoodson@redhat.com)
- Add missing dependencies on openshift_facts role (sdodson@redhat.com)

* Mon Dec 11 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.3.0
- remove integration tests from tox (lmeyer@redhat.com)
- correct ansible-playbook command syntax (jdiaz@redhat.com)
- Add openshift_facts to upgrade plays for service_type (mgugino@redhat.com)
- Check for openshift attribute before using it during CNS install.
  (jmencak@redhat.com)

* Mon Dec 11 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.2.0
- GlusterFS: Add playbook doc note (jarrpa@redhat.com)
- Fix openshift hosted registry rollout (rteague@redhat.com)
- Remove container_runtime from the openshift_version (sdodson@redhat.com)

* Fri Dec 08 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.9.0-0.1.0
- Cleanup byo references (rteague@redhat.com)
- openshift_node: reintroduce restart of CRI-O. (gscrivan@redhat.com)
- container-engine: skip openshift_docker_log_driver when it is False
  (gscrivan@redhat.com)
- container-engine: log-opts is a dictionary in the daemon.json file
  (gscrivan@redhat.com)
- openshift_version: add dependency to openshift_facts (gscrivan@redhat.com)
- openshift_version: define openshift_use_crio_only (gscrivan@redhat.com)
- openshift_version: add dependency to container_runtime (gscrivan@redhat.com)
- crio: define and use l_is_node_system_container (gscrivan@redhat.com)
- Update deprecation checks - include: (rteague@redhat.com)
- Add os_firewall to prerequisites.yml (mgugino@redhat.com)
- add 3.8 templates for gluster ep and svc (lmeyer@redhat.com)
- Remove openshift.common.service_type (mgugino@redhat.com)
- Remove unused openshift_env_structures and openshift_env (mgugino@redhat.com)
- Fix incorrect register name master registry auth (mgugino@redhat.com)
- Include Deprecation: Convert to import_playbook (rteague@redhat.com)
- add 3.8 templates for gluster ep and svc (m.judeikis@gmail.com)
- Remove all uses of openshift.common.admin_binary (sdodson@redhat.com)
- Implement container_runtime playbooks and changes (mgugino@redhat.com)
- Playbook Consolidation - byo/config.yml (rteague@redhat.com)
- openshift_logging_kibana: fix mixing paren (lmeyer@redhat.com)
- Fix ami building. (kwoodson@redhat.com)
- Include Deprecation: Convert to include_tasks (rteague@redhat.com)
- Add missing symlinks in openshift-logging (rteague@redhat.com)
- Fix generate_pv_pvcs_list plugin undef (mgugino@redhat.com)
- Playbook Consolidation - etcd Upgrade (rteague@redhat.com)
- bug 1519622. Disable rollback of ES DCs (jcantril@redhat.com)
- Remove all references to pacemaker (pcs, pcsd) and
  openshift.master.cluster_method. (abutcher@redhat.com)
- Remove entry point files no longer needed by CI (rteague@redhat.com)
- Don't check for the deployment_type (tomas@sedovic.cz)
- Get the correct value out of openshift_release (tomas@sedovic.cz)
- Fix oreg_auth_credentials_create register var (mgugino@redhat.com)
- Fix and cleanup not required dns bits (bdobreli@redhat.com)
- Fix hosted vars (mgugino@redhat.com)
- Remove duplicate init import in network_manager.yml (rteague@redhat.com)
- Document testing repos for dev purposes (bdobreli@redhat.com)
- Remove unused protected_facts_to_overwrite (mgugino@redhat.com)
- Use openshift testing repos for openstack (bdobreli@redhat.com)
- Use openshift_release instead of ose_version (tomas@sedovic.cz)
- Remove the ose_version check (tomas@sedovic.cz)
- Allow number of retries in openshift_management to be configurable
  (ealfassa@redhat.com)
- Bumping to 3.9 (smunilla@redhat.com)
- Cleanup unused openstack provider code (bdobreli@redhat.com)
- Adding 3.9 tito releaser (smunilla@redhat.com)
- Implement container runtime role (mgugino@redhat.com)
- Fix glusterfs checkpoint info (rteague@redhat.com)
- storage_glusterfs: fix typo (lmeyer@redhat.com)
- Playbook Consolidation - Redeploy Certificates (rteague@redhat.com)
- Fix tox (tomas@sedovic.cz)
- Remove shell environment lookup (tomas@sedovic.cz)
- Revert "Fix syntax error caused by an extra paren" (tomas@sedovic.cz)
- Revert "Fix the env lookup fallback in rhel_subscribe" (tomas@sedovic.cz)
- Remove reading shell environment in rhel_subscribe (tomas@sedovic.cz)
- retry package operations (lmeyer@redhat.com)
- Add v3.9 support (sdodson@redhat.com)
- Playbook Consolidation - openshift-logging (rteague@redhat.com)
- Do not escalate privileges in jks generation tasks (iacopo.rozzo@amadeus.com)
- Fix inventory symlinks in origin-ansible container. (dgoodwin@redhat.com)
- Initial upgrade for scale groups. (kwoodson@redhat.com)
- Update the doc text (tomas@sedovic.cz)
- Optionally subscribe OpenStack RHEL nodes (tomas@sedovic.cz)
- Fix the env lookup fallback in rhel_subscribe (tomas@sedovic.cz)
- Fix syntax error caused by an extra paren (tomas@sedovic.cz)
- Fix no_log warnings for custom module (mgugino@redhat.com)
- Add external_svc_subnet for k8s loadbalancer type service
  (jihoon.o@samsung.com)
- Remove openshift_facts project_cfg_facts (mgugino@redhat.com)
- Remove dns_port fact (mgugino@redhat.com)
- Bug 1512793- Fix idempotence issues in ASB deploy (fabian@fabianism.us)
- Remove unused task file from etcd role (rteague@redhat.com)
- fix type in authroize (jchaloup@redhat.com)
- Use IP addresses for OpenStack nodes (tomas@sedovic.cz)
- Update prometheus to 2.0.0 GA (zgalor@redhat.com)
- remove schedulable from openshift_facts (mgugino@redhat.com)
- inventory: Add example for service catalog vars (smilner@redhat.com)
- Correct usage of import_role (rteague@redhat.com)
- Remove openshift.common.cli_image (mgugino@redhat.com)
- Fix openshift_env fact creation within openshift_facts. (abutcher@redhat.com)
- Combine openshift_node and openshift_node_dnsmasq (mgugino@redhat.com)
- GlusterFS: Remove extraneous line from glusterblock template
  (jarrpa@redhat.com)
- Remove openshift_clock from meta depends (mgugino@redhat.com)
- Simplify is_master_system_container logic (mgugino@redhat.com)
- dist.iteritems() no longer exists in Python 3. (jpazdziora@redhat.com)
- Remove spurrious file committed by error (diego.abelenda@camptocamp.com)
- Fix name of the service pointed to by hostname
  (diego.abelenda@camptocamp.com)
- Missed the default value after the variable name change...
  (diego.abelenda@camptocamp.com)
- Change the name of the variable and explicitely document the names
  (diego.abelenda@camptocamp.com)
- Allow to set the hostname for routes to prometheus and alertmanager
  (diego.abelenda@camptocamp.com)
- Allow openshift_install_examples to be false (michael.fraenkel@gmail.com)
- Include Deprecation - openshift-service-catalog (rteague@redhat.com)
- Remove is_openvswitch_system_container from facts (mgugino@redhat.com)
- Workaround the fact that package state=present with dnf fails for already
  installed but excluded packages. (jpazdziora@redhat.com)
- With dnf repoquery and excluded packages, --disableexcludes=all is needed to
  list the package with --installed. (jpazdziora@redhat.com)
- Add support for external glusterfs as registry backend (m.judeikis@gmail.com)
- cri-o: honor additional and insecure registries again (gscrivan@redhat.com)
- docker: copy Docker metadata to the alternative storage path
  (gscrivan@redhat.com)
- Add check for gluterFS DS to stop restarts (m.judeikis@gmail.com)
- Bug 1514417 - Adding correct advertise-client-urls (shawn.hurley21@gmail.com)
- Uninstall tuned-profiles-atomic-openshift-node as defined in origin.spec
  (jmencak@redhat.com)
- Mod startup script to publish all frontend binds (cwilkers@redhat.com)

* Thu Nov 23 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.8.0-0.13.0
-

* Thu Nov 23 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.8.0-0.12.0
-

* Thu Nov 23 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.8.0-0.11.0
-

* Thu Nov 23 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.8.0-0.10.0
- tox.ini: simplify unit test reqs (lmeyer@redhat.com)
- Remove unused task files (rteague@redhat.com)
- Playbook Consolidation - openshift-provisioners (rteague@redhat.com)
- Include Deprecation - openshift-prometheus (rteague@redhat.com)
- Include Deprecation - openshift-node (rteague@redhat.com)
- Include Deprecation - openshift-management (rteague@redhat.com)
- Include Deprecation - openshift-glusterfs (rteague@redhat.com)
- Include Deprecation - openshift-master (rteague@redhat.com)
- Include Deprecation - openshift-hosted (rteague@redhat.com)
- Playbook Consolidation - openshift-service-catalog (rteague@redhat.com)
- Include Deprecation - openshift-nfs (rteague@redhat.com)
- Include Deprecation - openshift-metrics (rteague@redhat.com)
- Include Deprecation - openshift-etcd (rteague@redhat.com)
- Fix system_images_registry variable (mgugino@redhat.com)
- Include Deprecation - openshift-loadbalancer (rteague@redhat.com)
- Include Deprecation - openshift-checks (rteague@redhat.com)
- Playbook Consolidation - openshift-management (rteague@redhat.com)
- Playbook Consolidation - openshift-master (rteague@redhat.com)
- Playbook Consolidation - openshift-hosted (rteague@redhat.com)
- Place-holder for prerequisites.yml (mgugino@redhat.com)
- Cleanup etcd runtime variable. (mgugino@redhat.com)
- Fix uninstall option for prometheus (zgalor@redhat.com)
- Playbook Consolidation - openshift-glusterfs (rteague@redhat.com)
- Playbook Consolidation - openshift-metrics (rteague@redhat.com)
- Playbook Consolidation - openshift-loadbalancer (rteague@redhat.com)
- hosted_registry: clean up tmp mount point and fstab (dusty@dustymabe.com)

* Wed Nov 22 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.8.0-0.9.0
- Fix node system container var (mgugino@redhat.com)
- Add temporary playbook for CI test functionality (rteague@redhat.com)
- Playbook Consolidation - openshift-node (rteague@redhat.com)
- Fix logic for any sys containers (mgugino@redhat.com)
- containerPort must be an int; correctly quote/brace replicas value
  (rmeggins@redhat.com)
- papr: use new PAPR_PULL_TARGET_BRANCH (jlebon@redhat.com)
- Refactor etcd image (mgugino@redhat.com)
- GlusterFS: Files and templates for 3.8 (jarrpa@redhat.com)
- Only remove empty keys from env if env exists (sdodson@redhat.com)
- Upgrade to etcd 3.2 (sdodson@redhat.com)
- Allow modifying and adding prometheus application arguments
  (zgalor@redhat.com)
- Playbook Consolidation - openshift-nfs (rteague@redhat.com)
- Playbook Consolidation - openshift-etcd (rteague@redhat.com)
- Include Deprecation - Init Playbook Paths (rteague@redhat.com)

* Mon Nov 20 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.8.0-0.8.0
-

* Mon Nov 20 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.8.0-0.7.0
-

* Mon Nov 20 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.8.0-0.6.0
-

* Sun Nov 19 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.8.0-0.5.0
-

* Sun Nov 19 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.8.0-0.4.0
- bug 1498398. Enclose content between store tag (rromerom@redhat.com)

* Fri Nov 17 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.8.0-0.3.0
- papr: auto-detect image tag to use and bump to f27 (jlebon@redhat.com)
- Updating mtu value to int (kwoodson@redhat.com)
- fix the logging-es-prometheus selector (jcantril@redhat.com)
- GlusterFS: Add configuration for auto creating block-hosting volumes
  (jarrpa@redhat.com)
- Playbook Consolidation - openshift-checks (rteague@redhat.com)
- Combine openshift_node and openshift_node_upgrade (mgugino@redhat.com)
- registry-console: align image and check (lmeyer@redhat.com)
- registry-console template 3.8 consistency (lmeyer@redhat.com)
- registry-console template 3.7 consistency (lmeyer@redhat.com)
- registry-console template 3.6 consistency (lmeyer@redhat.com)

* Thu Nov 16 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.8.0-0.2.0
- Fix openstack init (rteague@redhat.com)
- Ensure node service is started. (kwoodson@redhat.com)
- Added aos-3.8 releaser for tito (smunilla@redhat.com)
- Playbook Consolidation - Initialization (rteague@redhat.com)
- Minor tweaks to ansible.cfg and example inventory (rteague@redhat.com)
- Removed old version code (mgugino@redhat.com)
- Fixing islnk. (kwoodson@redhat.com)
- Removing setting prefix and version facts in openshift_logging to let the
  component roles set their defaults (ewolinet@redhat.com)
- Create prometheus configmaps before statefulset (zgalor@redhat.com)
- Bug 1510496 - logging: honor ES PVC size (jwozniak@redhat.com)
- Combine master upgrade play with role (mgugino@redhat.com)
- Fix stale data in openshift_facts for logging (mgugino@redhat.com)
- Start requiring Ansible 2.4 (rteague@redhat.com)
- Fixing origin default for es proxy (ewolinet@redhat.com)
- Addressing tox errors (ewolinet@redhat.com)
- Addressing comments (ewolinet@redhat.com)
- Initial Kuryr Ports Pool Support (ltomasbo@redhat.com)
- Remove an unused retry file (tomas@sedovic.cz)
- Namespace the docker volumes (tomas@sedovic.cz)
- Fix tox (tomas@sedovic.cz)
- Namespace the OpenStack vars (tomas@sedovic.cz)
- Use `null` instead of `False` where it makes sense (tomas@sedovic.cz)
- Simplify the template paths for the storage setup (tomas@sedovic.cz)
- Use the default `item` loop variable for checks (tomas@sedovic.cz)
- Move the selinux check up (tomas@sedovic.cz)
- Add the DNS updates and rename the openstack vars (tomas@sedovic.cz)
- Remove the subnet_update_dns_servers task list (tomas@sedovic.cz)
- Move the vars/main.yml to defaults (tomas@sedovic.cz)
- FIXUP ANSIBLE CFG (tomas@sedovic.cz)
- Remove the static_inventory and bastion samples (tomas@sedovic.cz)
- Use the existing ansible.cfg file (tomas@sedovic.cz)
- Remove the subscription-manager role (tomas@sedovic.cz)
- Add a stub of the dns record update code in (tomas@sedovic.cz)
- Use correct host group in provision.yml (tomas@sedovic.cz)
- Remove the post-install and scale-up playbooks (tomas@sedovic.cz)
- Remove the openstack custom-actions for now (tomas@sedovic.cz)
- Remove the extra roles (tomas@sedovic.cz)
- Add openshift_openstack role and move tasks there (tomas@sedovic.cz)
- Use the docker-storage-setup role (tomas@sedovic.cz)
- Update readme (tomas@sedovic.cz)
- Update lookup plugins path (tomas@sedovic.cz)
- .gitignore casl-infra (tomas@sedovic.cz)
- Move the OpenStack playbooks (tomas@sedovic.cz)
- Updating logging components image defaulting pattern to match
  openshift_logging pattern (ewolinet@redhat.com)
- logging with static pvc: allow specifying the storage class name
  (bart.vanbos@kbc.be)
- Add role to configure project request template (hansmi@vshn.ch)
- Remove bash highlight (tomas@sedovic.cz)
- Revert the console hostname change (tomas@sedovic.cz)
- Add Extra CAs (custom post-provision action) (#801) (tlacencin@gmail.com)
- Add Flannel support (#814) (bdobreli@redhat.com)
- Docker storage fix (#812) (cwilkers@redhat.com)
- [WIP] Merge server with nofloating server heat templates (#761)
  (bdobreli@redhat.com)
- Support separate data network for Flannel SDN (#757) (bdobreli@redhat.com)
- Add Extra Docker Registry URLs (custom post-provision action) (#794)
  (tlacencin@gmail.com)
- Make the private key examples consistent (tomas@sedovic.cz)
- Allow the specification of server group policies when provisioning openstack
  (#747) (tzumainn@redhat.com)
- Attach additional RHN Pools (post-provision custom action) (#753)
  (tlacencin@gmail.com)
- Streamline the OpenStack provider README (tomas@sedovic.cz)
- Adding support for cluster-autoscaler role (kwoodson@redhat.com)
- Fix for this issue https://bugzilla.redhat.com/show_bug.cgi?id=1495372 (#793)
  (edu@redhat.com)
- Add CentOS support to the docker-storage-setup role (tomas@sedovic.cz)
- Replace the CASL references (#778) (tomas@sedovic.cz)
- Set public_v4 to private_v4 if it doesn't exist (tomas@sedovic.cz)
- Fix flake8 errors (tomas@sedovic.cz)
- Add dynamic inventory (tomas@sedovic.cz)
- Fixing various contrib changes causing CASL breakage (#771)
  (oybed@users.noreply.github.com)
- Required variables to create dedicated lv (#766) (edu@redhat.com)
- Adding the option to use 'stack_state' to allow for easy de-provisioning
  (#754) (oybed@users.noreply.github.com)
- Fix public master cluster DNS record when using bastion (#752)
  (bdobreli@redhat.com)
- Upscaling OpenShift application nodes (#571) (tlacencin@gmail.com)
- load balancer formatting fix (#745) (tzumainn@redhat.com)
- Docker ansible host (#742) (tomas@sedovic.cz)
- Empty ssh (#729) (tomas@sedovic.cz)
- Remove the `rhsm_register` value from inventory (tomas@sedovic.cz)
- Make the `rhsm_register` value optional (tomas@sedovic.cz)
- Clear the previous inventory during provisioning (tomas@sedovic.cz)
- Fix the cinder_registry_volume conditional (tomas@sedovic.cz)
- Pre-create a Cinder registry volume (tomas@sedovic.cz)
- Add ability to support custom api and console ports (#712)
  (etsauer@gmail.com)
- Support Cinder-backed Openshift registry (#707) (tomas@sedovic.cz)
- openstack: make server ports be trunk ports (#713) (celebdor@gmail.com)
- Point openshift_master_cluster_public_hostname at master or lb if defined
  (#706) (tzumainn@redhat.com)
- Allow using a provider network (#701) (tomas@sedovic.cz)
- Document global DNS security options (#694) (bdobreli@redhat.com)
- Add custom post-provision playbook for adding yum repos (#697)
  (tzumainn@redhat.com)
- Support external/pre-provisioned authoritative cluster DNS (#690)
  (bdobreli@redhat.com)
- Added checks for configured images and flavors (#688) (tlacencin@gmail.com)
- Cast num_* as int for jinja templates (#685) (bdobreli@redhat.com)
- Do not repeat pre_tasks for post-provision playbook (#689)
  (bdobreli@redhat.com)
- Fix node label customisation (#679) (tlacencin@gmail.com)
- Add documentation regarding running custom post-provision tasks (#678)
  (tzumainn@redhat.com)
- Add docs and defaults for multi-master setup (bdobreli@redhat.com)
- Ignore *.cfg and *.crt in the openstack inventory (#672) (tomas@sedovic.cz)
- Update openshift_release in the sample inventory (#647) (tomas@sedovic.cz)
- Configure different Docker volume sizes for different roles (#644)
  (tlacencin@gmail.com)
- Avoid server recreation in case of user_data modification. (#651)
  (robipolli@gmail.com)
- Set custom hostnames for servers (#643) (tlacencin@gmail.com)
- Access UI via a bastion node (#596) (bdobreli@redhat.com)
- group_vars/all.yml, stack_params.yaml, README: specifying flavors enabled and
  documented (#638) (tlacencin@gmail.com)
- Specify different image names for roles (#637) (tlacencin@gmail.com)
- Support multiple private networks for static inventory (#604)
  (bdobreli@redhat.com)
- Allow using ephemeral volumes for docker storage (#615) (tomas@sedovic.cz)
- Remove clouds.yaml from sample-inventory (tomas@sedovic.cz)
- Moving common DNS roles out of the playbook area (#605)
  (oybed@users.noreply.github.com)
- Note about jmespath requirement for control node (#599) (bdobreli@redhat.com)
- removed openstack (djurgens@redhat.com)
- Add wildcard pointer to Private DNS (djurgens@redhat.com)
- Options for bastion, SSH config, static inventory autogeneration
  (bdobreli@redhat.com)
- Add bastion and ssh config for the static inventory role
  (bdobreli@redhat.com)
- Set openshift_hostname explicitly for openstack (#579) (tomas@sedovic.cz)
- README: Added note about infra-ansible installation (#574)
  (tlacencin@gmail.com)
- Static inventory autogeneration (#550) (bdobreli@redhat.com)
- Generate static inventory with shade inventory (#538) (bdobreli@redhat.com)
- Include masters into etcd group, when it is empty (#559)
  (bdobreli@redhat.com)
- During provisioning, make unnecessary packages optional under a switch (#561)
  (tlacencin@gmail.com)
- Set ansible_become for the OSEv3 group (tomas@sedovic.cz)
- README: fix (kpilatov@redhat.com)
- README: typo (kpilatov@redhat.com)
- dependencies: python-heatclient and python-openstackclient added to optional
  dependencies (kpilatov@redhat.com)
- README: added prerequisity for a repository needed for python-openstackclient
  installation (kpilatov@redhat.com)
- Add a role to generate a static inventory (#540) (bdobreli@redhat.com)
- Retry tasks in the subscription manager role (#552) (tlacencin@gmail.com)
- Set up NetworkManager automatically (#542) (tomas@sedovic.cz)
- Replace greaterthan and equalto in openstack-stack (tomas@sedovic.cz)
- Switch the sample inventory to CentOS (#541) (tomas@sedovic.cz)
- Add defaults values for some openstack vars (#539) (tomas@sedovic.cz)
- Install DNS roles from casl-infra with galaxy (#529) (bdobreli@redhat.com)
- Playbook prerequisites.yml checks that prerequisites are met before
  provisioning (#518) (tlacencin@gmail.com)
- Persist DNS configuration for nodes for openstack provider
  (bdobreli@redhat.com)
- Manage packages to install/update for openstack provider
  (bdobreli@redhat.com)
- Fix yaml indentation (tomas@sedovic.cz)
- Use wait_for_connection for the Heat nodes (tomas@sedovic.cz)
- Put back node/flat secgrp for infra nodes on openstack (bdobreli@redhat.com)
- README.md: fixing typo (kpilatov@redhat.com)
- README.md: list jinja2 as a dependency (kpilatov@redhat.com)
- Modify sec groups for provisioned openstack servers (bdobreli@redhat.com)
- rename node_removal_policies, add some comments and defaults
  (tzumainn@redhat.com)
- all.yml: removed whitespaces in front of variables (kpilatov@redhat.com)
- removed whitespace in front of commented variable (kpilatov@redhat.com)
- OSEv3.yml: trailing space... (kpilatov@redhat.com)
- OSEv3.yml: added option to ignore set hardware limits for RAM and DISK
  (kpilatov@redhat.com)
- Fix flat sec group and infra/dns sec rules (bdobreli@redhat.com)
- Add node_removal_policies variable to allow for scaling down
  (tzumainn@redhat.com)
- Use cached facts, do not become for localhost (#484) (bdobreli@redhat.com)
- Add profiling and skippy stdout (#470) (bdobreli@redhat.com)
- Fix flake8 errors with the openstack inventory (tomas@sedovic.cz)
- Fix yamllint errors (tomas@sedovic.cz)
- Update sample inventory with the latest changes (tomas@sedovic.cz)
- Gather facts for provision playbook (bdobreli@redhat.com)
- Drop atomic-openshift-utils, update docs for origin (bdobreli@redhat.com)
- Add ansible.cfg for openstack provider (bdobreli@redhat.com)
- Add a flat sec group for openstack provider (bdobreli@redhat.com)
- Always let the openshift nodes access the DNS (tomas@sedovic.cz)
- Fix privileges in the pre-install playbook (tomas@sedovic.cz)
- Add default values to provision-openstack.yml (tomas@sedovic.cz)
- Move pre_tasks from to the openstack provisioner (tomas@sedovic.cz)
- Add readme (tomas@sedovic.cz)
- Add license for openstack.py in inventory (tomas@sedovic.cz)
- Add a sample inventory for openstack provisioning (tomas@sedovic.cz)
- Symlink roles to provisioning/openstack/roles (tomas@sedovic.cz)
- Add a single provisioning playbook (tomas@sedovic.cz)
- Move the openstack provisioning playbooks (tomas@sedovic.cz)
- Update CASL to use nsupdate for DNS records (#48)
  (oybed@users.noreply.github.com)
- Conditionally set the openshift_master_default_subdomain to avoid overriding
  it unecessary (#47) (oybed@users.noreply.github.com)
- More ansible migration and deploy OCP from local workstation (#376)
  (pschiffe@redhat.com)
- Removed hardcoded values from ansible roles (edu@redhat.com)
- First attempt at a simple multi-master support (#39) (etsauer@gmail.com)
- Stack refactor (#38) (etsauer@gmail.com)
- Ensure DNS configuration has wildcards set for infra nodes (#24)
  (oybed@users.noreply.github.com)
- Fixing two significant bugs in the HEAT deployment (#13) (etsauer@gmail.com)
- update for yamllint errors (jdetiber@redhat.com)
- Making providers common (#126) (rcook@redhat.com)
- Openstack heat (#2) (etsauer@gmail.com)
- Fixing ansible impl to work with OSP9 and ansible 2.2 (bedin@redhat.com)
- Updated env_id to be a sub-domain + make the logic a bit more flexible
  (bedin@redhat.com)
- Fixes Issue #163 if rhsm_password is not defined (vvaldez@redhat.com)
- Cleande up hostname role to make it more generic (bedin@redhat.com)
- Updated to run as root rather than cloud-user, for now... (bedin@redhat.com)
- Channging hard coded host groups to match openshift-ansible expected host
  groups. Importing byo playbook now instead of nested ansible run. Need to
  refactor how we generate hostnames to make it fit this. (esauer@redhat.com)
- Subscription manager role should accomodate orgs with spaces
  (esauer@redhat.com)
- Reverting previous commit and making template adjustments (esauer@redhat.com)
- Changes to allow runs from inside a container. Also allows for running
  upstream openshift-ansible installer (esauer@redhat.com)
- Changes by JayKayy for a full provision of OpenShift on OpenStack
  (esauer@redhat.com)
- Fix typo in task name (vvaldez@redhat.com)
- Add org parameter to Satellite with user/pass (vvaldez@redhat.com)
- Remove vars_prompt, add info to README to re-enable and for ansible-vault
  (vvaldez@redhat.com)
- Cosmetic changes to task names and move yum clean all to prereqs
  (vvaldez@redhat.com)
- Refactor use of rhsm_password to prevent display to CLI (vvaldez@redhat.com)
- Fix bad syntax with extra 'and' in when using rhsm_pool (vvaldez@redhat.com)
- Refactor role to dynamically determine rhsm_method (vvaldez@redhat.com)
- Add subscription-manager support for Hosted or Satellite (vvaldez@redhat.com)
- New OSE3 docker host builder and OpenStack ansible provisioning support
  (andy.block@gmail.com)

* Wed Nov 15 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.8.0-0.1.0
- Allow disabling authorization migration check (sdodson@redhat.com)
- Alternative method to create docker registry auth creds (mgugino@redhat.com)
- Nuke /var/lib/dockershim/sandbox/* while nodes are drained
  (sdodson@redhat.com)
- crio: sync crio.conf (gscrivan@redhat.com)
- Updating provisioning order. (kwoodson@redhat.com)
- Regex anchors changed to match protocol start and ports.
  (kwoodson@redhat.com)
- First pass at v3.8 support (sdodson@redhat.com)
- Run registry auth after docker restart (mgugino@redhat.com)
- Fix extension script for catalog (mgugino@redhat.com)
- Adding instance profile support for node groups. (kwoodson@redhat.com)
- Bumping openshift-ansible to 3.8 (smunilla@redhat.com)
- ansible.cfg: error when inventory does not parse (lmeyer@redhat.com)
- removing kind restrictions from oc_edit (kwoodson@redhat.com)
- Update Docs. Make Clearer where the actual docs are. (tbielawa@redhat.com)
- Remove upgrade playbooks for 3.3 through 3.5 (rteague@redhat.com)
- GlusterFS: Add gluster-s3 functionality (jarrpa@redhat.com)
- GlusterFS: Add glusterblock functionality (jarrpa@redhat.com)
- GlusterFS: Update heketi templates for latest version (jarrpa@redhat.com)
- GlusterFS: Specify resource requests (jarrpa@redhat.com)
- Remove remaining haproxy files with uninstallation
  (nakayamakenjiro@gmail.com)
- Proposal: container_runtime role (mgugino@redhat.com)
- Fix contenerized documentation? (mickael.canevet@camptocamp.com)
- Cleans up additional artifacts in uninstall. Closes 3082
  (gregswift@gmail.com)
- Add execution times to checkpoint status (rteague@redhat.com)
- Make clearer *_nfs_directory and *_volume_name (lpsantil@gmail.com)
- Allow cluster IP for docker-registry service to be set (hansmi@vshn.ch)

* Thu Nov 09 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.5-1
-

* Wed Nov 08 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.4-1
-

* Wed Nov 08 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.3-1
- Adding configuration for keeping transient namespace on error.
  (shawn.hurley21@gmail.com)
- Use openshift.common.client_binary (sdodson@redhat.com)
- Fix examples image streams (mgugino@redhat.com)
- Remove duplicate defaulting for ASB and TSB (sdodson@redhat.com)
- Fix preupgrade authorization objects are in sync minor versions
  (mgugino@redhat.com)
- General template updates for v3.7 (sdodson@redhat.com)
- Update to xPaaS v1.4.6 (sdodson@redhat.com)
- Bug 1511044- Slurp the etcd certs instead of using the lookup
  (fabian@fabianism.us)
- Change prometheus default namespace to 'openshift-metrics'
  (zgalor@redhat.com)
- Bootstrap enhancements. (kwoodson@redhat.com)
- reconcile registry-console and docker_image_availability (lmeyer@redhat.com)

* Wed Nov 08 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.2-1
- Remove debug code that was mistakenly committed (zgalor@redhat.com)
- Correct service restart command (sdodson@redhat.com)
- Give service-catalog controller-manager permissions to update status of
  ClusterServiceClasses and ClusterServicePlans (staebler@redhat.com)

* Wed Nov 08 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.1-1
- Bug 1510636- add name to local registry config (fabian@fabianism.us)

* Wed Nov 08 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.198.0
- container_binary_sync: Remove atomic prefix from image (smilner@redhat.com)
- Bug 1510546- Fix previous fix, task was indented one level too deep
  (fabian@fabianism.us)
- Use oc rather than kubectl (sdodson@redhat.com)
- Re-add challenge auth verification to github and google (mgugino@redhat.com)
- Move fact definition that breaks when check to end of block
  (fabian@fabianism.us)
- [Bug 1509354] Check if routers have certificates and use them
  (kwoodson@redhat.com)
- Fix v3.6 xpaas image streams (sdodson@redhat.com)
- Fix v3.7 xpaas image streams (sdodson@redhat.com)
- Fix prometheus default vars (mgugino@redhat.com)
- openshift_checks: Add OVS versions for OCP 3.7 (miciah.masters@gmail.com)
- Proper quotes (dymurray@redhat.com)
- Update service broker configmap and serviceaccount privileges
  (dymurray@redhat.com)
- Add etcd as part of inventory file. Otherwise, it fails as "Running etcd as
  an embedded service is no longer supported." (sarumuga@redhat.com)
- Add centos based dotnet 2.0 image streams (sdodson@redhat.com)

* Tue Nov 07 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.197.0
- Temporarily set master servingInfo.clientCA as client-ca-bundle.crt during
  rolling CA redeployment. (abutcher@redhat.com)
- container-engine: ensure /var/lib/containers/ is properly labelled
  (gscrivan@redhat.com)
- Moving docker location to share path with system containers.
  (kwoodson@redhat.com)
- Retry restarting master controllers (mgugino@redhat.com)
- Bug 1509680- Fix ansible-service-broker registry validations
  (fabian@fabianism.us)
- Fix preupgrade authorization objects are in sync (mgugino@redhat.com)
- Bug 1507617- Move etcd into its own service/dc with SSL (fabian@fabianism.us)

* Mon Nov 06 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.196.0
- Bug 1509052 - Remove logfile from broker config (david.j.zager@gmail.com)
- Fix github auth validation (mgugino@redhat.com)
- Re-generate lib_openshift (mail@jkroepke.de)
- Remove provisioner restrictions on oc_storageclass (mail@jkroepke.de)

* Mon Nov 06 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.195.0
- Bug 1507787- add full path to default asb etcd image (fabian@fabianism.us)

* Sun Nov 05 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.194.0
- Revert "Bootstrap enhancements." (ccoleman@redhat.com)

* Sun Nov 05 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.193.0
- management: enterprise users must acknowledge use of beta software
  (tbielawa@redhat.com)

* Sat Nov 04 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.192.0
- Bootstrap enhancements. (kwoodson@redhat.com)
- Fix master upgrade version detect and systemd enable (mgugino@redhat.com)
- Correct groupname during upgrade_control_plane play (mgugino@redhat.com)
- openshift_hosted: Add docker-gc (smilner@redhat.com)
- Remove old /etc/yum.repos.d/openshift_additional.repo file.
  (abutcher@redhat.com)
- CFME: Use cluster_hostname if cluster_public_hostname isn't available
  (tbielawa@redhat.com)
- Use client binary and well defined kubeconfig (sdodson@redhat.com)
- Ensure install and remove are mutually exclusive via
  openshift_sanitize_inventory (sdodson@redhat.com)
- Enable SC, ASB, TSB by default (sdodson@redhat.com)
- Using the currently attached pvc for an ES dc if available, otherwise falling
  back to current logic (ewolinet@redhat.com)
- Adding elb changes to provision elbs and add to scale group.
  (kwoodson@redhat.com)
- Give admin and edit roles permission to patch ServiceInstances and
  ServiceBindings (staebler@redhat.com)

* Fri Nov 03 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.191.0
- Adding CONFIG_FILE option back. (kwoodson@redhat.com)
- Configurable node config location. (kwoodson@redhat.com)
- Add enterprise prometheus image defaults (sdodson@redhat.com)
- Adding meta/main.yml to allow for Galaxy use of this repo (bedin@redhat.com)

* Thu Nov 02 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.190.0
- check presence of v2 snapshot before the migration proceeds
  (jchaloup@redhat.com)
- Remove delegate_to from openshift_facts within the openshift_ca role.
  (abutcher@redhat.com)
- Don't use possibly undefined variables in error messages
  (tbielawa@redhat.com)
- MTU for bootstrapping should default to openshift_node_sdn_mtu
  (ccoleman@redhat.com)
- Retry service account bootstrap kubeconfig creation (ccoleman@redhat.com)
- Docker: make use of new etc/containers/registries.conf optional
  (mgugino@redhat.com)
- Add rules to the view ClusterRole for service catalog. (staebler@redhat.com)
- Updating console OPENSHIFT_CONSTANTS flag for TSB (ewolinet@redhat.com)
- GlusterFS: Fix registry storage documentation (jarrpa@redhat.com)
- fix comment and make it visible to end-user (azagayno@redhat.com)
- escape also custom_cors_origins (azagayno@redhat.com)
- add comment on regexp specifics (azagayno@redhat.com)
- escape corsAllowedOrigins regexp strings and anchor them
  (azagayno@redhat.com)

* Wed Nov 01 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.189.0
- Stating that certificate it is required when doing SSL on ELB.
  (kwoodson@redhat.com)
- Ensure GCP image build instance gets cleaned up on teardown
  (ccoleman@redhat.com)
- Switch from bind-interfaces to bind-dynamic (sdodson@redhat.com)
- Remove unused osm_controller_lease_ttl (mgugino@redhat.com)
- Delete images located in a family named {{ prefix }}images
  (ccoleman@redhat.com)
- Use global IP to indicate node should pick DNS (ccoleman@redhat.com)
- Remove project metadata prefixed with the cluster prefix
  (ccoleman@redhat.com)
- Use openshift.node.registry_url instead of oreg_url (ccoleman@redhat.com)
- Allow master node group to wait for stable on GCP (ccoleman@redhat.com)
- GCP cannot use AWS growpart package (ccoleman@redhat.com)
- dnsmasq cache-size dns-forward-max change (pcameron@redhat.com)
- Also require that we match the release (sdodson@redhat.com)
- Add arbitrary firewall port config to master too (sdodson@redhat.com)
- remove master.service during the non-ha to ha upgrade (jchaloup@redhat.com)
- Removing unneeded bootstrap which moved into the product.
  (kwoodson@redhat.com)
- Add retry logic to docker auth credentials (mgugino@redhat.com)
- Retry restarting journald (mgugino@redhat.com)
- Modify StorageClass name to standard (piqin@redhat.com)
- Give PV & PVC empty storage class to avoid being assigned default gp2
  (mawong@redhat.com)
- Use oc_project to ensure openshift_provisioners_project present
  (mawong@redhat.com)
- Fix yaml formatting (mawong@redhat.com)
- Create default storageclass for cloudprovider openstack (piqin@redhat.com)
- preserve the oo-install ansible_inventory_path value (rmeggins@redhat.com)

* Tue Oct 31 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.188.0
- Add dm_thin_pool for gluster use (sdodson@redhat.com)
- Fix broken oc_secret update function (barlik@gmx.com)
- add new clusterNetworks fields to new installs (jtanenba@redhat.com)
- docker: Create openshift_docker_is_node_or_master variable
  (smilner@redhat.com)
- Correctly install cockpit (sdodson@redhat.com)
- Glusterfs storage templates for v1.5 added (chinacoolhacker@gmail.com)
- bug 1501599.  Omit logging project from overcommit restrictions
  (jcantril@redhat.com)
- GlusterFS: Remove image option from heketi command (jarrpa@redhat.com)

* Mon Oct 30 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.187.0
-

* Sun Oct 29 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.186.0
-

* Sat Oct 28 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.185.0
- bug 1506073. Lower cpu request for logging when it exceeds limit
  (jcantril@redhat.com)
- Update the name of the service-catalog binary (staebler@redhat.com)
- disk_availability check: include submount storage (lmeyer@redhat.com)

* Fri Oct 27 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.184.0
- cri-o: Set max log size to 50 mb (mrunalp@gmail.com)
- cri-o: open port 10010 (gscrivan@redhat.com)
- bug 1435144. Remove uneeded upgrade in openshift_logging role
  (jcantril@redhat.com)
- Remove inadvertently committed inventory file (rteague@redhat.com)
- crio: restorcon /var/lib/containers (smilner@redhat.com)
- Correct openshift_release regular expression (rteague@redhat.com)
- crio: Add failed_when to overlay check (smilner@redhat.com)
- docker: set credentials when using system container (gscrivan@redhat.com)
- Change dnsmasq to bind-interfaces + except-interfaces (mgugino@redhat.com)
- Fix CA Bundle passed to service-catalog broker for ansible-service-broker
  (staebler@redhat.com)
- Renaming csr to bootstrap for consistency. (kwoodson@redhat.com)
- Add master config upgrade hook to upgrade-all plays (mgugino@redhat.com)
- Remove 'Not Started' status from playbook checkpoint (rteague@redhat.com)
- Force import_role to static for loading openshift_facts module
  (rteague@redhat.com)
- Make openshift-ansible depend on all subpackages (sdodson@redhat.com)
- Refactor health check playbooks (rteague@redhat.com)

* Fri Oct 27 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.183.0
-

* Thu Oct 26 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.182.0
- Fixing documentation for the cert_key_path variable name.
  (kwoodson@redhat.com)
- Moving removal of unwanted artifacts to image_prep. (kwoodson@redhat.com)
- Ensure journald persistence directories exist (mgugino@redhat.com)
- Fix lint (tbielawa@redhat.com)
- Move add_many_container_providers.yml to playbooks/byo/openshift-management
  with a noop task include to load filter plugins. (abutcher@redhat.com)
- Refactor adding multiple container providers (tbielawa@redhat.com)
- Management Cleanup and Provider Integration (tbielawa@redhat.com)

* Thu Oct 26 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.181.0
- Fix loop_var warnings during logging install (mgugino@redhat.com)
- Fix typo and add detailed comments in kuryr (sngchlko@gmail.com)

* Thu Oct 26 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.179.0
- Remove pause from master service startup (rteague@redhat.com)
- Change default in prometheus storage type to emptydir (zgalor@redhat.com)
- Bug 1491636 - honor node selectors (jwozniak@redhat.com)
- Sync latest imagestreams and templates (sdodson@redhat.com)
- Remove base package install (mgugino@redhat.com)
- etcd: remove hacks for the system container (gscrivan@redhat.com)
- Ensure deployment_subtype is set within openshift_sanitize_inventory.
  (abutcher@redhat.com)
- Add installer checkpoint for prometheus (zgalor@redhat.com)
- Remove unused registry_volume_claim variable (hansmi@vshn.ch)

* Wed Oct 25 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.178.0
- Split prometheus image defaults to prefix and version (zgalor@redhat.com)
- Remove extraneous spaces that yamllint dislikes (staebler@redhat.com)
- Fix edit and admin role patching for service catalog (staebler@redhat.com)
- strip dash when comparing version with Python3 (jchaloup@redhat.com)
- Bug 1452939 - change Logging & Metrics imagePullPolicy (jwozniak@redhat.com)
- Remove role bindings during service catalog un-install (staebler@redhat.com)
- Fix a few small issues in service catalog uninstall (staebler@redhat.com)
- Remove incorrect validation for OpenIDIdentityProvider (mgugino@redhat.com)
- Enable oreg_auth credential replace during upgrades (mgugino@redhat.com)
- Handle bootstrap behavior in GCP template (ccoleman@redhat.com)
- Ensure upgrades apply latest journald settings (mgugino@redhat.com)

* Tue Oct 24 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.177.0
- Check if the master service is non-ha or not (jchaloup@redhat.com)
- Correct host group for controller restart (rteague@redhat.com)
- Set the proper external etcd ip address when migrating embeded etcd
  (jchaloup@redhat.com)
- Switch to stateful set in prometheus (zgalor@redhat.com)
- cli: use the correct name for the master system container
  (gscrivan@redhat.com)
- cli: do not pull again the image when using Docker (gscrivan@redhat.com)
- verstion_gte seems unreliable on containerized installs (sdodson@redhat.com)
- Retry reconcile in case of error and give up eventually (simo@redhat.com)
- Updating ocp es proxy image to use openshift_logging_proxy_image_prefix if
  specified (ewolinet@redhat.com)
- Generate all internal hostnames of no_proxy (ghuang@redhat.com)
- Add nfs variables documentation to README file (zgalor@redhat.com)
- Avoid undefined variable in master sysconfig template (hansmi@vshn.ch)
- Ensure proper variable templating for skopeo auth credentials
  (mgugino@redhat.com)

* Mon Oct 23 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.176.0
- Update defaults (fabian@fabianism.us)
- Use service-ca.crt instead of master ca.crt (fabian@fabianism.us)
- use master cert (fabian@fabianism.us)
- Bug 1496426 - add asb-client secret to openshift-ansible-service-broker
  namespace (fabian@fabianism.us)
- docker: Move enterprise registry from pkg to main (smilner@redhat.com)
- systemcontainers: Verify atomic.conf proxy is always configured
  (smilner@redhat.com)
- Add variable to control whether NetworkManager hook is installed
  (hansmi@vshn.ch)

* Mon Oct 23 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.175.0
-

* Sun Oct 22 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.174.0
-

* Sun Oct 22 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.173.0
-

* Sun Oct 22 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.172.0
-

* Sat Oct 21 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.171.0
- Use "requests" for CPU resources instead of limits
  (peter.portante@redhat.com)
- [bz1501271] Attempt to use ami ssh user and default to ansible_ssh_user.
  (kwoodson@redhat.com)
- Fix undefined variable for master upgrades (mgugino@redhat.com)
- Adding pre check to verify clusterid is set along with cloudprovider when
  performing upgrade. (kwoodson@redhat.com)

* Fri Oct 20 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.170.0
- Check for container runtime prior to restarting when updating system CA
  trust. (abutcher@redhat.com)
- bug 1489498. preserve replica and shard settings (jcantril@redhat.com)
- Set servingInfo.clientCA to ca.crt during upgrade. (abutcher@redhat.com)

* Fri Oct 20 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.169.0
- Initial Kuryr support (mdulko@redhat.com)
- Indentation errors (dymurray@redhat.com)
- Bug 1503233 - Add liveness and readiness probe checks to ASB deploymentconfig
  (dymurray@redhat.com)

* Fri Oct 20 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.168.0
-

* Thu Oct 19 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.167.0
-

* Thu Oct 19 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.166.0
-

* Thu Oct 19 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.165.0
-

* Thu Oct 19 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.164.0
- Change to service-signer.crt for template_service_broker CA_BUNDLE
  (staebler@redhat.com)
- Use service-signer.crt for ca_bundle passed to clusterservicebroker
  (staebler@redhat.com)
- Rename ServiceBroker to ClusterServiceBroker for ansible_service_broker task.
  (staebler@redhat.com)
- Add apiserver.crt to service-catalog controller-manager deployment.
  (staebler@redhat.com)
- Remove redundant faulty role binding ifrom
  kubeservicecatalog_roles_bindings.yml (staebler@redhat.com)
- Update service catalog playbook for service-catalog rc1 (staebler@redhat.com)

* Thu Oct 19 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.163.0
- set use_manageiq as default (efreiber@redhat.com)

* Thu Oct 19 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.162.0
- Wait longer for stable GCP instances (ccoleman@redhat.com)
- Remove unneeded master config updates during upgrades (mgugino@redhat.com)

* Wed Oct 18 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.161.0
-

* Wed Oct 18 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.160.0
- Fix pvc selector default to be empty dict instead of string
  (zgalor@redhat.com)
- Fix typo in setting prom-proxy memory limit (zgalor@redhat.com)
- Do not remove files for bootstrap if resolv or dns. (kwoodson@redhat.com)
- Fix missing docker option signature-verification (mgugino@redhat.com)
- Fix prometheus role nfs (zgalor@redhat.com)

* Wed Oct 18 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.159.0
- Updating openshift-ansible.spec file to include files dir
  (sdodson@redhat.com)
- Bug 1501768: fix eventrouter nodeSelector padding (jwozniak@redhat.com)
- Reverting proxy image version to v1.0.0 to pass CI (ewolinet@redhat.com)
- Making travis happy (ewolinet@redhat.com)
- cri-o: error out when node is a Docker container (gscrivan@redhat.com)
- Rewire openshift_template_service_broker_namespaces configurable
  (jminter@redhat.com)
- Ensure controllerConfig.serviceServingCert is correctly set during upgrade.
  (abutcher@redhat.com)
- Updating pattern for elasticsearch_proxy images (ewolinet@redhat.com)
- Updating ES proxy image prefix and version to match other components
  (ewolinet@redhat.com)
- Add ability to set node and master imageConfig to latest (mgugino@redhat.com)
- Restart all controllers to force reconfiguration during upgrade
  (sdodson@redhat.com)

* Tue Oct 17 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.158.0
- Refactor openshift-management entry point (rteague@redhat.com)
- Add switch to enable/disable container engine's audit log being stored in ES.
  (jkarasek@redhat.com)

* Mon Oct 16 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.157.0
- data migration of embedded etcd not allowed (jchaloup@redhat.com)
- GlusterFS: remove topology reference from deploy-heketi (jarrpa@redhat.com)

* Mon Oct 16 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.156.0
- set initial etcd cluster properly during system container scale up
  (jchaloup@redhat.com)

* Sun Oct 15 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.155.0
-

* Sat Oct 14 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.154.0
-

* Fri Oct 13 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.153.0
- default groups.oo_new_etcd_to_config to an empty list (jchaloup@redhat.com)

* Fri Oct 13 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.152.0
-

* Fri Oct 13 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.151.0
- updated dynamic provision section for openshift metrics to support storage
  class name (elvirkuric@gmail.com)

* Fri Oct 13 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.150.0
- Ensure upgrade playbook exits on health check failures (rteague@redhat.com)
- Ensure docker is installed for containerized load balancers
  (mgugino@redhat.com)
- Fix containerized node service unit placement order (mgugino@redhat.com)
- Provisioning Documentation Updates (mgugino@redhat.com)

* Thu Oct 12 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.149.0
- Fix broken debug_level (mgugino@redhat.com)
- Ensure host was reached for proper conditional validation
  (rteague@redhat.com)
- Ensure docker service status actually changes (mgugino@redhat.com)
- Display warnings at the end of the control plane upgrade (sdodson@redhat.com)
- Force reconciliation of role for 3.6 (simo@redhat.com)
- Remove etcd health check (sdodson@redhat.com)
- migrate embedded etcd to external etcd (jchaloup@redhat.com)

* Wed Oct 11 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.148.0
- Bug 1490647 - logging-fluentd deployed with openshift_logging_use_mux=false
  fails to start due to missing (nhosoi@redhat.com)
- Fix typo in inventory example (rteague@redhat.com)
- Separate tuned daemon setup into a role. (jmencak@redhat.com)
- crio, docker: expect openshift_release to have 'v' (gscrivan@redhat.com)
- rebase on master (maxamillion@fedoraproject.org)
- Add fedora compatibility (maxamillion@fedoraproject.org)
- Allow checkpoint status to work across all groups (rteague@redhat.com)
- Add valid search when search does not exist on resolv.conf
  (nakayamakenjiro@gmail.com)

* Tue Oct 10 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.147.0
- Add PartOf to docker systemd service unit. (mgugino@redhat.com)
- crio: use systemd manager (gscrivan@redhat.com)
- Ensure servingInfo.clientCA is set as ca.crt rather than ca-bundle.crt.
  (abutcher@redhat.com)
- crio, docker: use openshift_release when openshift_image_tag is not used
  (gscrivan@redhat.com)
- crio: fix typo (gscrivan@redhat.com)
- Update registry_config.j2 (jialiu@redhat.com)
- Update registry_config.j2 (jialiu@redhat.com)

* Mon Oct 09 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.146.0
- docker_image_availability: credentials to skopeo (mgugino@redhat.com)
- Rename openshift_cfme role to openshift_management (tbielawa@redhat.com)

* Mon Oct 09 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.145.0
- add missing restart node handler to flannel (jchaloup@redhat.com)
- Switch to configmap leader election on 3.7 upgrade (mkhan@redhat.com)
- crio.conf.j2: sync from upstream (gscrivan@redhat.com)
- cri-o: use overlay instead of overlay2 (gscrivan@redhat.com)
- Ensure docker is restarted when iptables is restarted (mgugino@redhat.com)
- Stop including origin and ose hosts example file (sdodson@redhat.com)
- node: make node service PartOf=openvswitch.service when openshift-sdn is used
  (dcbw@redhat.com)

* Fri Oct 06 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.144.0
- fix typo for default in etcd (mgugino@redhat.com)
- Bumping version of service catalog image for 3.7 (ewolinet@redhat.com)
- remove duplicate [OSEv3:children] group (jfchevrette@gmail.com)
- Fix lint error (tbielawa@redhat.com)
- Update hosts.ose.example (ephillipe@gmail.com)
- Remove the no-longer-used App/DB pv size override variables from inventories
  (tbielawa@redhat.com)
- openshift_checks: lb and nfs do not need docker (lmeyer@redhat.com)
- openshift_checks: use oo group names everywhere (lmeyer@redhat.com)
- Add notes about SA token. Improve NFS validation. (tbielawa@redhat.com)
- Hooks for installing CFME during full openshift installation
  (tbielawa@redhat.com)
- Documentation (tbielawa@redhat.com)
- Import upstream templates. Do the work. Validate parameters.
  (tbielawa@redhat.com)
- CFME 4.6 work begins. CFME 4.5 references added to the release-3.6 branch
  (tbielawa@redhat.com)
- Update hosts.origin.example (ephillipe@gmail.com)
- Add logging es prometheus endpoint (jcantril@redhat.com)
- bug 1497401. Default logging and metrics images to 3.7 (jcantril@redhat.com)
- Ensure docker service started prior to credentials (mgugino@redhat.com)
- Adding support for an inventory directory/hybrid inventory
  (esauer@redhat.com)
- Remove unused tasks file in openshift_named_certificates (rteague@redhat.com)
- Move node cert playbook into node config path (rteague@redhat.com)
- Move master cert playbooks into master config path (rteague@redhat.com)
- Move etcd cert playbooks into etcd config path (rteague@redhat.com)
- Fix hosted selector variable migration (mgugino@redhat.com)
- Bug 1496271 - Perserve SCC for ES local persistent storage
  (jcantril@redhat.com)
- Limit hosts that run openshift_version role (mgugino@redhat.com)
- Update ansible-service-broker config to track latest broker
  (fabian@fabianism.us)
- fix master-facts for provisioning (mgugino@redhat.com)
- Make provisioning steps more reusable (mgugino@redhat.com)
- logging: honor openshift_logging_es_cpu_limit (jwozniak@redhat.com)
- Addressing tox issues (ewolinet@redhat.com)
- bug 1482661. Preserve ES dc nodeSelector and supplementalGroups
  (jcantril@redhat.com)
- Checking if any openshift_*_storage_kind variables are set to dynamic without
  enabling dynamic provisioning (ewolinet@redhat.com)
- Removing setting pvc size and dynamic to remove looped var setting
  (ewolinet@redhat.com)

* Wed Oct 04 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.143.0
- Limit base-package install during master upgrades (mgugino@redhat.com)
- Fix provisiong scale group and elb logic (mgugino@redhat.com)

* Tue Oct 03 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.142.0
- Document that nfs_directory must conform to DNS-1123 (sdodson@redhat.com)
- Move node aws credentials to config.yml (mgugino@redhat.com)
- Use etcd_ip when communicating with the cluster as a peer in etcd scaleup.
  (abutcher@redhat.com)
- Ensure openshift.common.portal_net updated during scaleup.
  (abutcher@redhat.com)
- docker: fix some tox warnings (gscrivan@redhat.com)
- Require openshift_image_tag in the inventory with openshift-enterprise
  (gscrivan@redhat.com)
- crio: use the image_tag on RHEL (gscrivan@redhat.com)
- docker: use the image_tag on RHEL (gscrivan@redhat.com)

* Tue Oct 03 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.141.0
- Restore registires to /etc/sysconfig/docker (mgugino@redhat.com)
- Fix Prometheus byo entry point (rteague@redhat.com)
- Update to the openshift_aws style scheme for variables (ccoleman@redhat.com)

* Tue Oct 03 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.140.0
- openshift_checks: Fix incorrect list cast (smilner@redhat.com)
- lib/base: Allow for empty option value (jarrpa@redhat.com)

* Mon Oct 02 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.139.0
- Fix mispelling in error message yammlint -> yamllint (simo@redhat.com)
- Separate certificate playbooks. (abutcher@redhat.com)
- Reverting using uninstall variables for logging and metrics
  (ewolinet@redhat.com)
- Add --image flag to setup-openshift-heketi-storage (ttindell@isenpai.com)

* Mon Oct 02 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.138.0
- Fix typo in openshift_default_storage_class/README (hansmi@vshn.ch)
- GlusterFS: make ServiceAccounts privileged when either glusterfs or heketi is
  native (jarrpa@redhat.com)
- Fix some provisioning variables (mgugino@redhat.com)

* Mon Oct 02 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.137.0
- openshift_node: Add MASTER_SERVICE on system container install
  (smilner@redhat.com)
- openshift_node: Set DOCKER_SERVICE for system container (smilner@redhat.com)

* Sun Oct 01 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.136.0
- Include openshift_hosted when redeploying router certificates to handle auto-
  generated wildcard certificate or custom openshift_hosted_router_certificate.
  (abutcher@redhat.com)
- Check for router service annotations when redeploying router certificates.
  (abutcher@redhat.com)
- Remove oo_option symlink from specfile. (abutcher@redhat.com)
- Add a README.md to lookup_plugins/ (abutcher@redhat.com)
- Remove oo_option facts. (abutcher@redhat.com)
- block 3.6->3.7 upgrade if storage backend is not set to etcd3
  (jchaloup@redhat.com)
- Changes necessary to support AMI building (mgugino@redhat.com)

* Sat Sep 30 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.135.0
- fix whitespace for centos repos (jdetiber@redhat.com)
- Fix registry auth variable (mgugino@redhat.com)
- move health-checks and control-plane-verification before excluders
  (jchaloup@redhat.com)
- Fix typo in files (Docker registries) (william17.burton@gmail.com)
- Registering the broker for TSB (ewolinet@redhat.com)
- Quick formatting updates to the logging README. (steveqtran@gmail.com)
- openshift_facts: coerce docker_use_system_container to bool
  (smilner@redhat.com)
- Migrate enterprise registry logic to docker role (mgugino@redhat.com)
- minor update to README and removed dead file (steveqtran@gmail.com)
- Added new variables for logging role for remote-syslog plugin
  (steveqtran@gmail.com)
- Remove some reminants of Atomic Enterprise (sdodson@redhat.com)
- Allow examples management to be disabled (sdodson@redhat.com)
- rename vars to avoid double negatives and ensuing confusion
  (jsanda@redhat.com)
- set prometheus endpoint properties to false by default (jsanda@redhat.com)
- add options to disable prometheus endpoints (jsanda@redhat.com)
- Enable JMX reporting of internal metrics (jsanda@redhat.com)

* Thu Sep 28 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.134.0
- OpenShift-Ansible Installer Checkpointing (rteague@redhat.com)
- evaluate etcd_backup_tag variable (jchaloup@redhat.com)

* Thu Sep 28 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.133.0
- papr: use F26 container for extended tests (jlebon@redhat.com)
- Fix typo in drop_etcdctl.yml (hansmi@vshn.ch)
- Rename filter_plugins to unique names (rteague@redhat.com)
- Fix missing quotes on openshift_aws_build_ami_ssh_user default
  (mgugino@redhat.com)
- papr: Workaround for RHBZ#1483553 (smilner@redhat.com)
- Adding default for volume size if not set (ewolinet@redhat.com)
- Fix origin repo deployment (mgugino@redhat.com)
- More variables in AWS provisioning plays (mgugino@redhat.com)
- Support installation of NetworkManager for provisioned nodes
  (mgugino@redhat.com)
- Set the etcd backend quota to 4GB by default (jchaloup@redhat.com)
- logging: introducing event router (jwozniak@redhat.com)
- logging: fix kibana and kibana-ops defaults (jwozniak@redhat.com)
- papr: Use Fedora 26 (smilner@redhat.com)

* Wed Sep 27 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.132.0
- make difference filter output a list for Python3 (jchaloup@redhat.com)
- Updating to check for netnamespace kube-service-catalog to be ready
  (ewolinet@redhat.com)
- consolidate etcd_common role (jchaloup@redhat.com)
- Fluentd: one output tag, one output plugin (nhosoi@redhat.com)

* Tue Sep 26 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.131.0
- Generate aggregator api client config in temporary directory.
  (abutcher@redhat.com)

* Tue Sep 26 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.130.0
- Passing in image parameter for tsb template (ewolinet@redhat.com)

* Tue Sep 26 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.129.0
- Refactor openshift_hosted plays and role (mgugino@redhat.com)
- Remove logging ES_COPY feature (jcantril@redhat.com)

* Tue Sep 26 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.128.0
- check if the storage backend is set to etcd3 before upgrading to 3.7
  (jchaloup@redhat.com)
- crio: detect the correct version of the images (gscrivan@redhat.com)
- crio: set the correct image name with OSE (gscrivan@redhat.com)
- resolve #5428: python-dbus not found (ltheisen@mitre.org)
- Updating default behavior for installing metrics and logging. Separating out
  uninstall to own variable (ewolinet@redhat.com)
- Add booleans to prevent unwanted install of nuage roles. (mgugino@redhat.com)
- Set master facts prior to adding new etcd client urls to master config.
  (abutcher@redhat.com)
- Remove debugging statements and pause module (sdodson@redhat.com)
- Fix registry_auth logic for upgrades (mgugino@redhat.com)
- crio: skip installation on lbs and nfs nodes (gscrivan@redhat.com)
- Remove override default.py callback plugin (rteague@redhat.com)
- consolidate etcd_migrate role (jchaloup@redhat.com)
- Add python3-PyYAML for Fedora installs (mgugino@redhat.com)
- Do a full stop/start when etcd certificates had expired.
  (abutcher@redhat.com)
- Move additional/block/insecure registires to /etc/containers/registries.conf
  (mgugino@redhat.com)
- Improve CA playbook restart logic and skip restarts when related services had
  previously expired certificates. (abutcher@redhat.com)
- health checks: add diagnostics check (lmeyer@redhat.com)
- Remove unused openshift_hosted_logging role (mgugino@redhat.com)
- consolidate etcd_upgrade role (jchaloup@redhat.com)
- disable excluders after all pre-checks (jchaloup@redhat.com)
- Fixed AnsibleUnsafeText by converting to int (edu@redhat.com)
- Ensure that hostname is lowercase (sdodson@redhat.com)
- Fix deprecated subscription-manager command
  (bliemli@users.noreply.github.com)
- Returning actual results of yedit query.  Empty list was returning empty
  dict. (kwoodson@redhat.com)
- Default openshift_pkg_version to full version-release during upgrades
  (sdodson@redhat.com)
- Creating structure to warn for use of deprecated variables and set them in a
  single location before they are no longer honored (ewolinet@redhat.com)
- Remove default value for oreg_url (mgugino@redhat.com)
- Creating initial tsb role to consume and apply templates provided for tsb
  (ewolinet@redhat.com)
- Set network facts using first master's config during scaleup.
  (abutcher@redhat.com)
- Use 3.7 RPM repo (ahaile@redhat.com)
- Changes for Nuage atomic ansible install
  (rohan.s.parulekar@nuagenetworks.net)
- Add 3.7 scheduler predicates (jsafrane@redhat.com)
- Consolidate etcd certs roles (jchaloup@redhat.com)
- GlusterFS can now be run more than once. Ability to add devices to nodes
  (ttindell@isenpai.com)
- Ensure valid search on resolv.conf (mateus.caruccio@getupcloud.com)
- move (and rename) get_dns_ip filter into openshift_node_facts
  (jdiaz@redhat.com)
- cri-o: Allow full image override (smilner@redhat.com)

* Thu Sep 21 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.127.0
- Updating to always configure api aggregation with installation
  (ewolinet@redhat.com)
- Do not reconcile in >= 3.7 (simo@redhat.com)
- Cleanup old deployment types (mgugino@redhat.com)
- crio: ensure no default CNI configuration files are left
  (gscrivan@redhat.com)
- node: specify the DNS domain (gscrivan@redhat.com)
- more retries on repoquery_cmd (lmeyer@redhat.com)
- fix etcd back message error (jchaloup@redhat.com)
- openshift_checks: enable providing file outputs (lmeyer@redhat.com)
- Fix registry auth task ordering (mgugino@redhat.com)
- Prometheus role fixes (zgalor@redhat.com)
- papr: Update inventory to include required vars (smilner@redhat.com)
- testing: Skip net vars on integration tests (smilner@redhat.com)
- inventory: Update network variable doc (smilner@redhat.com)
- installer image: use tmp file for vaultpass (lmeyer@redhat.com)
- system container: use ansible root as cwd (lmeyer@redhat.com)
- openshift_sanitize_inventory: Check for required vars (smilner@redhat.com)
- No conversion to boolean and no quoting for include_granted_scopes.
  (jpazdziora@redhat.com)
- Correct firewall install for openshift-nfs (rteague@redhat.com)
- inventory: Update versions to 3.7 (smilner@redhat.com)
- Port origin-gce roles for cluster setup to copy AWS provisioning
  (ccoleman@redhat.com)
- Bug 1491636 - honor openshift_logging_es_ops_nodeselector
  (jwozniak@redhat.com)
- Setup tuned after the node has been restarted. (jmencak@redhat.com)
- Only attempt to start iptables on hosts in the current batch
  (sdodson@redhat.com)
- Removing setting of pod presets (ewolinet@redhat.com)
- cri-o: Fix Fedora image name (smilner@redhat.com)
- add retry on repoquery_cmd (lmeyer@redhat.com)
- add retries to repoquery module (lmeyer@redhat.com)
- Rework openshift-cluster into deploy_cluster.yml (rteague@redhat.com)
- inventory generate: fix config doc (lmeyer@redhat.com)
- inventory generate: remove refs to openshift_cluster_user (lmeyer@redhat.com)
- inventory generate: always use kubeconfig, no login (lmeyer@redhat.com)
- Scaffold out the entire build defaults hash (tbielawa@redhat.com)
- Use openshift.common.ip rather than ansible_default_ipv4 in etcd migration
  playbook. (abutcher@redhat.com)
- Add IMAGE_VERSION to the image stream tag source (sdodson@redhat.com)
- Add loadbalancer config entry point (rteague@redhat.com)
- pull openshift_master deps out into a play (jchaloup@redhat.com)
- Don't assume storage_migration control variables are already boolean
  (mchappel@redhat.com)
- upgrade: Updates warning on missing required variables (smilner@redhat.com)
- Update master config with new client urls during etcd scaleup.
  (abutcher@redhat.com)
- Increase rate limiting in journald.conf (maszulik@redhat.com)
- Correct logic for openshift_hosted_*_wait (rteague@redhat.com)
- Adding mangagement-admin SC to admin role for management-infra project
  (ewolinet@redhat.com)
- Only install base openshift package on masters and nodes (mgugino@redhat.com)
- Workaround Ansible Jinja2 delimiter warning (rteague@redhat.com)
- openshift-checks: add role symlink (lmeyer@redhat.com)
- double the required disk space for etcd backup (jchaloup@redhat.com)
- openshift_health_check: allow disabling all checks (lmeyer@redhat.com)
- docker_image_availability: fix local image search (lmeyer@redhat.com)
- docker_image_availability: probe registry connectivity (lmeyer@redhat.com)
- openshift_checks: add retries in python (lmeyer@redhat.com)
- add inventory-generator under new sub pkg (jvallejo@redhat.com)
- Re-enabling new tuned profile hierarchy (PR5089) (jmencak@redhat.com)
- Add `openshift_node_open_ports` to allow arbitrary firewall exposure
  (ccoleman@redhat.com)
- Fix: authenticated registry support for containerized hosts
  (mgugino@redhat.com)
- [Proposal] OpenShift-Ansible Proposal Process (rteague@redhat.com)
- Improve searching when conditions for Jinja2 delimiters (rteague@redhat.com)
- Clarify requirement of having etcd group (sdodson@redhat.com)
- add health checks 3_6,3_7 upgrade path (jvallejo@redhat.com)
- container-engine: Allow full image override (smilner@redhat.com)
- Add openshift_public_hostname length check (mgugino@redhat.com)
- Skip failure dedup instead of crashing (rhcarvalho@gmail.com)
- Properly quote "true" and "false" strings for include_granted_scopes.
  (jpazdziora@redhat.com)
- Move sysctl.conf customizations to a separate file (jdesousa@redhat.com)
- Fix new_master or new_node fail check (denverjanke@gmail.com)
- [Proposal] OpenShift-Ansible Playbook Consolidation (rteague@redhat.com)
- GlusterFS: Allow option to use or ignore default node selectors
  (jarrpa@redhat.com)
- GlusterFS: Clarify heketi URL documentation (jarrpa@redhat.com)
- GlusterFS: Add files/templates for v3.7 (jarrpa@redhat.com)
- Support setting annotations on Hawkular route (hansmi@vshn.ch)
- add additional preflight checks to upgrade path (jvallejo@redhat.com)
- hot fix for env variable resolve (m.judeikis@gmail.com)
- GlusterFS: Correct firewall port names (jarrpa@redhat.com)
- Make RH subscription more resilient to temporary failures
  (lhuard@amadeus.com)

* Mon Sep 11 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.126.0
- Fix rpm version logic for hosts (mgugino@redhat.com)
- Revert back to hostnamectl and previous default of not setting hostname
  (sdodson@redhat.com)
- Correct include path to not follow symlink (rteague@redhat.com)
- Fix include path for docker upgrade tasks (rteague@redhat.com)
- Fix issue with etcd_common when using pre_upgrade tag (rteague@redhat.com)
- inventory: Denote new required upgrade variables (smilner@redhat.com)
- upgrade: Verify required network items are set (smilner@redhat.com)
- ami build process calls openshift-node/config.yml (kwoodson@redhat.com)

* Fri Sep 08 2017 Scott Dodson <sdodson@redhat.com> 3.7.0-0.125.1
- Consolidating AWS roles and variables underneath openshift_aws role.
  (kwoodson@redhat.com)
- Fix README.md typo (mgugino@redhat.com)
- Fixing variables and allowing custom ami. (kwoodson@redhat.com)
- Remove openshift-common (mgugino@redhat.com)
- Fix openshift_master_config_dir (sdodson@redhat.com)
- remove experimental-cri flag from node config (sjenning@redhat.com)
- cri-o: Split RHEL and CentOS images (smilner@redhat.com)
- openshift_checks aos_version: also check installed under yum
  (lmeyer@redhat.com)
- Create ansible role for deploying prometheus on openshift (zgalor@redhat.com)
- Fix: set openshift_master_config_dir to the correct value.
  (mgugino@redhat.com)
- Bump ansible requirement to 2.3 (sdodson@redhat.com)
- Move master additional config out of base (rteague@redhat.com)
- Import dnf only if importing yum fails (jhadvig@redhat.com)
- output skopeo image check command (nakayamakenjiro@gmail.com)
- skip openshift_cfme_nfs_server if not using nfs (sdw35@cornell.edu)
- bug 1487573. Bump the allowed ES versions (jcantril@redhat.com)
- update env in etcd.conf.j2 to reflect the latest naming (jchaloup@redhat.com)
- logging set memory request to limit (jcantril@redhat.com)
- Use the proper pod subnet instead the services one (edu@redhat.com)
- elasticsearch: reintroduce readiness probe (jwozniak@redhat.com)
- cri-o: add support for additional registries (gscrivan@redhat.com)
- reverse order between router cert generation (mewt.fr@gmail.com)
- ensured to always use a certificate for the router (mewt.fr@gmail.com)
- Adding proxy env vars for dc/docker-registry (kwoodson@redhat.com)
- oc_atomic_container: support Skopeo output (gscrivan@redhat.com)

* Tue Sep 05 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.125.0
-

* Tue Sep 05 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.124.0
- Fix ansible_syntax check (rteague@redhat.com)
- Standardize etcd entry point playbooks (rteague@redhat.com)
- Adding deprecation checks to ansible_syntax (rteague@redhat.com)
- Break out master config into stand-alone playbook (rteague@redhat.com)
- Move all-in-one fail check to evaluate_groups.yml (rteague@redhat.com)
- Break out node config into stand-alone playbook (rteague@redhat.com)
- Adding another default to protect against missing name/desc
  (kwoodson@redhat.com)
- Removed dns role (mgugino@redhat.com)
- Fix typo in variable names for glusterfs firewall configuration
  (bacek@bacek.com)
- disk_availability: fix bug where msg is overwritten (lmeyer@redhat.com)
- Added firwall defaults to etcd role. (kwoodson@redhat.com)
- Remove meta depends from clock (mgugino@redhat.com)
- Only run migrate auth for < 3.7 (rteague@redhat.com)
- Fix openshift_master upgrade (mgugino@redhat.com)
- Merging openshift_node with openshift bootstrap. (kwoodson@redhat.com)
- Test: Fail on entry point playbooks in common (rteague@redhat.com)
- Bug 1467265 - logging: add 'purge' option with uninstall
  (jwozniak@redhat.com)
- openshift_checks: ignore hidden files in checks dir
  (miciah.masters@gmail.com)

* Wed Aug 30 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.123.0
-

* Wed Aug 30 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.122.0
- Update openshift_hosted_routers example to be in ini format.
  (abutcher@redhat.com)
- Update calico to v2.5 (djosborne10@gmail.com)

* Wed Aug 30 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.121.0
- Revert "logging set memory request to limit" (sdodson@redhat.com)
- Move firewall install and fix scaleup playbooks (rteague@redhat.com)
- Fix group conditional requirements (rteague@redhat.com)
- Updating openshift_service_catalog to use oc_service over oc_obj to resolve
  idempotency issues being seen from rerunning role (ewolinet@redhat.com)
- annotate the infra projects for logging to fix bz1480988
  (jcantril@redhat.com)
- docker_image_availability: timeout skopeo inspect (lmeyer@redhat.com)
- Fix scaleup on containerized installations (sdodson@redhat.com)
- bug 1480878. Default pvc for logging (jcantril@redhat.com)
- logging set memory request to limit (jcantril@redhat.com)
- openshift_cfme: add nfs directory support (fsimonce@redhat.com)

* Tue Aug 29 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.120.0
- Nuage changes to add custom mounts for atomic-openshift-node service
  (rohan.s.parulekar@nuagenetworks.net)
- Add independent registry auth support (mgugino@redhat.com)
- roles: use openshift_use_crio (gscrivan@redhat.com)
- cri-o: change to system runc (gscrivan@redhat.com)
- cri-o: rename openshift_docker_use_crio to openshift_use_crio
  (gscrivan@redhat.com)
- Remove unsupported playbooks and utilities (rteague@redhat.com)
- Updating default tag for enterprise installation for ASB
  (ewolinet@redhat.com)
- Only validate certificates that are passed to oc_route (zgalor@redhat.com)

* Mon Aug 28 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.118.0
- Fix origin metrics and logging container version
  (gevorg15@users.noreply.github.com)
- Removing deprecation warnings for when conditions. (kwoodson@redhat.com)
- Default to global setting for firewall. (kwoodson@redhat.com)
- system-containers: Fallback for system_images_registry (smilner@redhat.com)
- inventory: Add system_images_registry example (smilner@redhat.com)
- Remove near-meta role openshift_cli_facts (mgugino@redhat.com)
- Update error message: s/non-unique/duplicate (rhcarvalho@gmail.com)
- Make pylint disables more specific (rhcarvalho@gmail.com)
- Handle exceptions in failure summary cb plugin (rhcarvalho@gmail.com)
- Rewrite failure summary callback plugin (rhcarvalho@gmail.com)
- Handle more exceptions when running checks (rhcarvalho@gmail.com)
- List known checks/tags when check name is invalid (rhcarvalho@gmail.com)
- List existing health checks when none is requested (rhcarvalho@gmail.com)
- Add playbook for running arbitrary health checks (rhcarvalho@gmail.com)
- Update health check README (rhcarvalho@gmail.com)
- Standardize openshift_provisioners entry point (rteague@redhat.com)
- Remove unused upgrade playbook (rteague@redhat.com)
- Bug 1471322: logging roles based image versions (jwozniak@redhat.com)

* Fri Aug 25 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.117.0
- Standardize openshift-checks code paths (rteague@redhat.com)

* Fri Aug 25 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.116.0
- Add missing hostnames to registry cert (sdodson@redhat.com)

* Fri Aug 25 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.115.0
-

* Fri Aug 25 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.114.0
-

* Fri Aug 25 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.113.0
- openshift_version: enterprise accepts new style pre-release
  (smilner@redhat.com)
- Nuage changes for Atomic hosts OSE Integration
  (rohan.s.parulekar@nuagenetworks.net)

* Fri Aug 25 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.112.0
- fix #5206.  Default ES cpu limit (jcantril@redhat.com)

* Fri Aug 25 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.111.0
- Upgrade check for OpenShift authorization objects (rteague@redhat.com)

* Fri Aug 25 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.110.0
- Setup tuned profiles in /etc/tuned (jmencak@redhat.com)

* Thu Aug 24 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.109.0
-

* Thu Aug 24 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.108.0
-

* Thu Aug 24 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.107.0
-

* Thu Aug 24 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.106.0
- Add dotnet 2.0 to v3.6 (sdodson@redhat.com)
- Add dotnet 2.0 to v3.7 (sdodson@redhat.com)
- Update v3.6 content (sdodson@redhat.com)
- Update all image streams and templates (sdodson@redhat.com)
- Passing memory and cpu limit for ops ES install (ewolinet@redhat.com)
- If IP4_NAMESERVERS are unset then pull the value from /etc/resolv.conf
  (sdodson@redhat.com)
- New tuned profile hierarchy. (jmencak@redhat.com)
- GlusterFS: add minor README note for #5071 (jarrpa@redhat.com)
- Update cfme templates to auto-generate postgresql password
  https://bugzilla.redhat.com/show_bug.cgi?id=1461973 (simaishi@redhat.com)

* Wed Aug 23 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.105.0
- Fix generated content (sdodson@redhat.com)
- Switch to migrating one host and forming a new cluster (sdodson@redhat.com)
- First attempt at provisioning. (kwoodson@redhat.com)
- First attempt at creating the cert signer. (kwoodson@redhat.com)
- remove out of scope variable from exception message
  (maxamillion@fedoraproject.org)
- raise AosVersionException if no expected packages found by dnf query
  (maxamillion@fedoraproject.org)
- Fix missing space in calico ansible roles (djosborne10@gmail.com)
- Allow GCS object storage to be configured (ccoleman@redhat.com)
- add dnf support to roles/openshift_health_checker/library/aos_version.py
  (maxamillion@fedoraproject.org)
- Add hostname/nodename length check (mgugino@redhat.com)
- Refactor openshift_hosted's docker-registry route setup (dms@redhat.com)
- bug 1468987: kibana_proxy OOM (jwozniak@redhat.com)

* Sun Aug 20 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.104.0
- Ensure that openshift_node_facts has been called for dns_ip
  (sdodson@redhat.com)

* Sat Aug 19 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.103.0
-

* Fri Aug 18 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.102.0
-

* Fri Aug 18 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.101.0
-

* Fri Aug 18 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.7.0-0.100.0
- Change memory requests and limits units (mak@redhat.com)
- Display "origin 3.6" as in previous installer 3.5 (brunovern.a@gmail.com)
- Use sdn_cluster_network_cidr as default calico pool (djosborne10@gmail.com)
- fix missing console appending in logging (jcantril@redhat.com)
- Enable version 3.6 for OSE (bacek@bacek.com)
- Adding std_include to the metrics playbook. (kwoodson@redhat.com)
- Don't include noop (rteague@redhat.com)
- Remove openshift_repos dependencies (rteague@redhat.com)
- polish openshift-master role (jchaloup@redhat.com)
- etc_traffic check: factor away short_version (lmeyer@redhat.com)
- openshift-checks: have playbooks invoke std_include (lmeyer@redhat.com)
- bug: container_binary_sync no longer moves upon symlinks (smilner@redhat.com)
- Remove orphan files (rteague@redhat.com)
- Additional os_firewall role refactoring (rteague@redhat.com)
- Standardize usage of std_include in byo (rteague@redhat.com)
- Cleanup validate_hostnames (rteague@redhat.com)
- Use openshift.node.dns_ip as listening address (sdodson@redhat.com)
- Remove obsolete yum check (rteague@redhat.com)
- Clean up Calico readme (djosborne10@gmail.com)
- Change vsd user nodes parameter name (rohan.s.parulekar@nuagenetworks.net)
- Removing dependencies for openshift_repos and setting them up early in the
  cluster build. (kwoodson@redhat.com)
- Default values for CFME container images are invalid (jkaur@redhat.com)
- Fix duplicate evaluate_groups.yml call during install (rteague@redhat.com)
- Minor update to correct firewall play name (rteague@redhat.com)
- Moving firewall rules under the role to work with refactor.
  (kwoodson@redhat.com)
- Fix Restore Master AWS Options (michael.fraenkel@gmail.com)
- Update etcd scaleup entrypoint includes and use etcd_{hostname,ip} facts for
  new member registration. (abutcher@redhat.com)
- openshift_checks: allow OVS 2.7 on OCP 3.5 and 3.6 (miciah.masters@gmail.com)
- Refactor group initialization (rteague@redhat.com)
- Updated README to reflect refactor.  Moved firewall initialize into separate
  file. (kwoodson@redhat.com)
- system_container.yml: fix braces (lmeyer@redhat.com)
- Error check project creation. (kwoodson@redhat.com)
- Update README.md (sdodson@redhat.com)
- Fix syntax for when statement (rhcarvalho@gmail.com)
- configure kibana index mode (jcantril@redhat.com)
- Change default CFME namespace to use reserved openshift- prefix
  (tbielawa@redhat.com)
- Start iptables on each master in serial (denverjanke@gmail.com)
- Remove additional 'restart master' handler references. (abutcher@redhat.com)
- Adding a default condition and removing unneeded defaults.
  (kwoodson@redhat.com)
- adding check to a yaml dump to work properly with new ruamel lib
  (ihorvath@redhat.com)
- Bump calico to v2.4.1 (djosborne10@gmail.com)
- openshift_checks: refactor find_ansible_mount (lmeyer@redhat.com)
- More complete discovery of entry point playbooks (rteague@redhat.com)
- Add missing byo v3_7 playbooks (sdodson@redhat.com)
- Add v3_7 upgrades (sdodson@redhat.com)
- Remove remaining references to openshift-master.service (ccoleman@redhat.com)
- Disable old openshift-master.service on upgrade (ccoleman@redhat.com)
- Use the new election mode (client based) instead of direct etcd access
  (ccoleman@redhat.com)
- Remove the origin-master.service and associated files (ccoleman@redhat.com)
- Make native clustering the default everywhere (ccoleman@redhat.com)
- Warn when user has no etcd group member nodes (ccoleman@redhat.com)
- First attempt at refactor of os_firewall (kwoodson@redhat.com)
- Refactor of openshift_version. (kwoodson@redhat.com)
- Fix lint errors (sdodson@redhat.com)
- integration tests: keep openshift_version happy (lmeyer@redhat.com)
- New pattern involves startup and initializing through the std_include.yml
  (kwoodson@redhat.com)
- adding readme for openshift_manageiq (efreiber@redhat.com)
- papr: Update to use v3.6.0 images (smilner@redhat.com)
- Removing tasks from module openshift_facts. (kwoodson@redhat.com)
- Updating PVC generation to only be done if the pvc does not already exist to
  avoid idempotent issues (ewolinet@redhat.com)
- Origin image build: add oc client (lmeyer@redhat.com)
- Add v3.7 hosted templates (sdodson@redhat.com)
- GlusterFS: Don't use /dev/null for empty file. (jarrpa@redhat.com)
- Quick Installer should specify which config file to edit. (jkaur@redhat.com)
- cri-o: configure the CNI network (gscrivan@redhat.com)
- nfs only run if cloud_provider not defined (sdw35@cornell.edu)
- Default gte_3_7 to false (sdodson@redhat.com)
- Add v3.7 content (sdodson@redhat.com)
- Update version checks to tolerate 3.7 (skuznets@redhat.com)
- cri-o: Restart cri-o after openshift sdn installation (smilner@redhat.com)
- cri-o: Continue node without SELinux check (smilner@redhat.com)
- examples: use the correct variable name (gscrivan@redhat.com)
- cri-o: allow to override CRI-O image indipendently from Docker
  (gscrivan@redhat.com)
- docker: introduce use_crio_only (gscrivan@redhat.com)
- docker: skip Docker setup when using CRI-O (gscrivan@redhat.com)
- openvswitch: system container depends on the cri-o service
  (gscrivan@redhat.com)
- cli_image: do not require Docker when using CRI-O (gscrivan@redhat.com)
- cri-o: skip Set precise containerized version check (gscrivan@redhat.com)
- cri-o: skip Docker version test (gscrivan@redhat.com)
- cri-o: use only images from Docker Hub (gscrivan@redhat.com)
- cri-o: Enable systemd-modules-load if required (smilner@redhat.com)
- openshift_node: fix typo for experimental-cri (smilner@redhat.com)
- cri-o: Fix node template to use full variable (smilner@redhat.com)
- cri-o: Ensure overlay is available (smilner@redhat.com)
- cri-o: Default insecure registries to "" (smilner@redhat.com)
- crio: use a template for the configuration (gscrivan@redhat.com)
- openshift_docker_facts: Add use_crio (smilner@redhat.com)
- cri-o: Minor fixes for tasks (smilner@redhat.com)
- cri-o: Hardcode image name to cri-o (smilner@redhat.com)
- cri-o: Add cri-o as a Wants in node units (smilner@redhat.com)
- cri-o: configure storage and insecure registries (gscrivan@redhat.com)
- node.yaml: configure node to use cri-o when openshift.common.use_crio
  (gscrivan@redhat.com)
- inventory: Add use_crio example (smilner@redhat.com)
- cri-o: Allow cri-o usage. (smilner@redhat.com)
- adding pods/logs to manageiq role (efreiber@redhat.com)
- openshift_checks: refactor logging checks (lmeyer@redhat.com)
- GlusterFS: Copy SSH private key to master node. (jarrpa@redhat.com)
- openshift_checks: add property to track 'changed' (lmeyer@redhat.com)
- Fixing SA and clusterrole namespaces (ewolinet@redhat.com)
- package_version check: tolerate release version 3.7 (lmeyer@redhat.com)
- Missing space (kp@tigera.io)
- add pre-flight checks to ugrade path (jvallejo@redhat.com)
- add fluentd logging driver config check (jvallejo@redhat.com)
- Paren wrap integration print(). (abutcher@redhat.com)
- Update openshift_cert_expiry for py3 support. (abutcher@redhat.com)
- Use enterprise images for CFME enterprise deployments (sdodson@redhat.com)
- use mux_client_mode instead of use_mux_client (rmeggins@redhat.com)
- openshift_checks: enable variable conversion (lmeyer@redhat.com)
- GlusterFS: Check for namespace if deploying a StorageClass
  (jarrpa@redhat.com)
- Switch logging and metrics OCP image tag from 3.6.0 to v3.6
  (sdodson@redhat.com)
- Fixing storageclass doc variable. (kwoodson@redhat.com)
- GlusterFS: Fix variable names in defaults. (jarrpa@redhat.com)
- Fix aws_secret_key check (carlpett@users.noreply.github.com)
- Impl fluentd file buffer (nhosoi@redhat.com)
- Use existing OPENSHIFT_DEFAULT_REGISTRY setting during masters scaleup
  (tbielawa@redhat.com)
- GlusterFS: Default glusterfs_name in loop items. (jarrpa@redhat.com)
- Remove cluster in favor of rolebindings. (kwoodson@redhat.com)
- Updating metrics role to create serviceaccounts and roles immediately
  (ewolinet@redhat.com)
- GlusterFS: Use default namespace when not native. (jarrpa@redhat.com)
- Set the openshift_version from the openshift.common.version in case it is
  empty (jchaloup@redhat.com)
- Revert "Add health checks to upgrade playbook" (rhcarvalho@gmail.com)
- move common tasks to a single file included by both systemd_units.yml
  (jchaloup@redhat.com)
- Fixes for auth_proxy, vxlan mode (srampal@cisco.com)
- Tolerate non existence of /etc/sysconfig/atomic-openshift-master
  (sdodson@redhat.com)
- Block etcdv3 migration for supported configurations (sdodson@redhat.com)
- Shut down masters before taking an etcd backup (sdodson@redhat.com)
- Move node facts to new openshift_node_facts role. (abutcher@redhat.com)
- Add glusterfs_registry hosts to oo_all_hosts. (jarrpa@redhat.com)
- Updating template parameter replica to be more unique to avoid var scope
  creeping (ewolinet@redhat.com)
- Add 3.7 releaser (sdodson@redhat.com)
- add selector and storage class name to oc_pvc module (jcantril@redhat.com)
- backport 'Add systemctl daemon-reload handler to openshift_node' #4403 to
  openshift_node_upgrade (jchaloup@redhat.com)
- Normalize list of checks passed to action plugin (rhcarvalho@gmail.com)
- Clean up unnecessary quotes (rhcarvalho@gmail.com)
- Make LoggingCheck.run return the correct type (rhcarvalho@gmail.com)
- Clean up openshift-checks playbooks (rhcarvalho@gmail.com)
- fixes after rebasing with #4485 (jvallejo@redhat.com)
- add pre-flight checks to ugrade path (jvallejo@redhat.com)
- Refactor openshift_facts BIOS vendor discovery (rteague@redhat.com)
- Normalize logging entry. (kwoodson@redhat.com)
- Nuage changes to support IPTables kube-proxy in OpenShift
  (siva_teja.areti@nokia.com)
- Remove default provisioner. (kwoodson@redhat.com)
- Fix for : https://bugzilla.redhat.com/show_bug.cgi?id=1467423
  (jkaur@redhat.com)
- allow to specify docker registry for system containers (jchaloup@redhat.com)
- Fail within scaleup playbooks when new_{nodes,masters} host groups are empty.
  (abutcher@redhat.com)
- Add rate limit configurability (sdodson@redhat.com)
- Resolve deprecation warnings in Contiv roles (rteague@redhat.com)
- add etcd scaleup playbook (jawed.khelil@amadeus.com)
- Spacing and moving deleget_to to bottom. (kwoodson@redhat.com)
- Updated to use modules instead of command for user permissions.
  (kwoodson@redhat.com)
- fix BZ1422541 on master branch (weshi@redhat.com)

* Thu Jul 27 2017 Scott Dodson <sdodson@redhat.com> 3.7.1-1
- Fix incorrect delegate_to in control plane upgrade (sdodson@redhat.com)
- Follow the new naming conventions. (zhang.wanmin@zte.com.cn)
- Simplify generation of /etc/origin/node/resolv.conf (sdodson@redhat.com)
- Add glusterfs hosts to oo_all_hosts so that hosts set initial facts.
  (abutcher@redhat.com)
- Sync all openshift.common.use_openshift_sdn uses in yaml files
  (jchaloup@redhat.com)
- Fixing podpresets perms for service-catalog-controller (ewolinet@redhat.com)
- Fixing route spec caCertificate to be correctly capitalized
  (ewolinet@redhat.com)
- Set TimeoutStartSec=300 (sdodson@redhat.com)
- Revert "set KillMode to process in node service file" (sdodson@redhat.com)
- openshift_checks: refactor to internalize task_vars (lmeyer@redhat.com)
- openshift_checks: get rid of deprecated module_executor (lmeyer@redhat.com)
- openshift_checks: improve comments/names (lmeyer@redhat.com)
- add default value for router path in the cert (efreiber@redhat.com)
- Router wildcard certificate created by default (efreiber@redhat.com)
- Remove unsupported parameters from example inventory files.
  (jarrpa@redhat.com)
- Fix lint errors (sdodson@redhat.com)
- Metrics: grant hawkular namespace listener role (mwringe@redhat.com)
- Removing nolog from htpasswd invocation so not to supress errors
  (ewolinet@redhat.com)
- Removed kubernetes.io string from default. (kwoodson@redhat.com)
- Allow storage migrations to be optional and/or non fatal (sdodson@redhat.com)
- libvirt: fall back to mkisofs if genisoimage isn't available
  (dcbw@redhat.com)
- libvirt: add documentation about SSH keypair requirements (dcbw@redhat.com)
- Updating how storage type is determined, adding bool filter in
  openshift_logging_elasticsearch (ewolinet@redhat.com)
- Pass the provisioner to the module. (kwoodson@redhat.com)
- Use absolute path when unexcluding (Sergi Jimenez)
- Fixes https://bugzilla.redhat.com/show_bug.cgi?id=1474246 (Sergi Jimenez)
- Support enabling the centos-openshift-origin-testing repository
  (dms@redhat.com)
- 1472467- add ose- prefix to ansible service broker name (fabian@fabianism.us)
- Updating openshift_logging_kibana default for kibana hostname
  (ewolinet@redhat.com)
- GlusterFS: Create registry storage svc and ep in registry namespace
  (jarrpa@redhat.com)
- Default an empty list for etcd_to_config if not there (tbielawa@redhat.com)
- If proxy in effect, add etcd host IP addresses to NO_PROXY list on masters
  (tbielawa@redhat.com)
- GlusterFS: Pass all booleans through bool filter. (jarrpa@redhat.com)
- GlusterFS: Fix bug in detecting whether to open firewall ports.
  (jarrpa@redhat.com)
- Pass first master's openshift_image_tag to openshift_loadbalancer for
  containerized haproxy installation. (abutcher@redhat.com)
- verify sane log times in logging stack (jvallejo@redhat.com)
- Fix log dumping on service failure (sdodson@redhat.com)
- Updating verbs for serviceclasses objects (ewolinet@redhat.com)
- Fix broken link to Docker image instructions (rhcarvalho@gmail.com)
- Added parameters inside of gce defaults.  Pass all params to the module.
  (kwoodson@redhat.com)
- add etcd increased-traffic check (jvallejo@redhat.com)
- Add etcd exports to openshift_storage_nfs (abutcher@redhat.com)
- Hopefully finally fix the no_proxy settings (tbielawa@redhat.com)
- openshift_checks/docker_storage: overlay/2 support (lmeyer@redhat.com)
- Removing parameter kind and allowing default to be passed.
  (kwoodson@redhat.com)
- Remove openshift_use_dnsmasq from aws and libvirt playbooks
  (sdodson@redhat.com)
- 1471973- default to bootstrapping the broker on startup (fabian@fabianism.us)
- image builds: remove dependency on playbook2image (jvallejo@redhat.com)
- Setting node selector to be empty string (ewolinet@redhat.com)
- Add drain retries after 60 second delay (sdodson@redhat.com)
- Dump some logs (sdodson@redhat.com)
- daemon_reload on node and ovs start (sdodson@redhat.com)
- Ensure proper fact evaluation (sdodson@redhat.com)
- Wrap additional service changes in retries (sdodson@redhat.com)
- Wrap docker stop in retries (sdodson@redhat.com)
- Add retries to node restart handlers (sdodson@redhat.com)
- Test docker restart with retries 3 delay 30 (smilner@redhat.com)
- Adding podpreset config into master-config (ewolinet@redhat.com)
- Update image-gc-high-threshold value (decarr@redhat.com)
- Adding a check for variable definition. (kwoodson@redhat.com)
- docker: fix docker_selinux_enabled (lmeyer@redhat.com)
- Changing cluster role to admin (rhallise@redhat.com)
- drain still pending in below files without fix : (jkaur@redhat.com)
- Fixed spacing and lint errors. (kwoodson@redhat.com)
- Switch CI to ansible-2.3.1.0 (sdodson@redhat.com)
- Allow OVS 2.7 in latest OpenShift releases (rhcarvalho@gmail.com)
- Make aos_version module handle multiple versions (rhcarvalho@gmail.com)
- Split positive and negative unit tests (rhcarvalho@gmail.com)
- GlusterFS: Create in custom namespace by default (jarrpa@redhat.com)
- hosted registry: Use proper node name in GlusterFS storage setup
  (jarrpa@redhat.com)
- GlusterFS: Make heketi-cli command configurable (jarrpa@redhat.com)
- GlusterFS: Reintroduce heketi-cli check for non-native heketi
  (jarrpa@redhat.com)
- GlusterFS: Bug fixes for external GlusterFS nodes (jarrpa@redhat.com)
- GlusterFS: Improve and extend example inventory files (jarrpa@redhat.com)
- Fixed tests and added sleep for update. (kwoodson@redhat.com)
- Fixing needs_update comparison.  Added a small pause for race conditions.
  Fixed doc.  Fix kind to storageclass (kwoodson@redhat.com)
- Adding storageclass support to lib_openshift. (kwoodson@redhat.com)
- Add an SA policy to the ansible-service-broker (rhallise@redhat.com)
- Import templates will fail if user is not system:admin (jkaur@redhat.com)
- Additional optimization parameters for ansible.cfg (sejug@redhat.com)
- Fix etcd conditional check failure (admin@webresource.nl)
- Remove invalid when: from vars: (rteague@redhat.com)

* Tue Jul 18 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.153-1
- Updating to compare sets instead of sorted lists (ewolinet@redhat.com)
- Adding ability to create podpreset for service-catalog-controller for
  bz1471881 (ewolinet@redhat.com)
- Updating to use oc replace and conditionally update edit and admin roles
  (ewolinet@redhat.com)
- Other playbooks maybe expecting this to be at least an empty string. I think
  they default it to an empty list if its not found. (tbielawa@redhat.com)
- Fix NO_PROXY environment variable setting (tbielawa@redhat.com)
- Changing the passing of data for sc creation. (kwoodson@redhat.com)
- Fixed variable name. (kwoodson@redhat.com)
- Adding disk encryption to storageclasses and to openshift registry
  (kwoodson@redhat.com)

* Mon Jul 17 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.152-1
-

* Sun Jul 16 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.151-1
-

* Sun Jul 16 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.150-1
-

* Sat Jul 15 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.149-1
- Config was missed before replace. (jkaur@redhat.com)
- Redeploy-certificates will fail for registry and router if user is not
  system:admin (jkaur@redhat.com)

* Fri Jul 14 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.148-1
- Adding in permissions to edit and admin cluster roles (ewolinet@redhat.com)
- making kube-service-catalog project network global when using redhat
  /openshift-ovs-multitenant plugin (ewolinet@redhat.com)
- set KillMode to process in node service file (jchaloup@redhat.com)
- Upgrade fails when "Drain Node for Kubelet upgrade" (jkaur@redhat.com)
- openvswitch, syscontainer: specify the Docker service name
  (gscrivan@redhat.com)

* Thu Jul 13 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.144-1
- Created js file for enabling tech preview for console, updated master-config
  for pod presets and console tech preview (ewolinet@redhat.com)
- GlusterFS: Add updated example hosts files (jarrpa@redhat.com)
- GlusterFS: Fix SSH-based heketi configuration (jarrpa@redhat.com)

* Wed Jul 12 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.143-1
-

* Wed Jul 12 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.142-1
- add scheduled pods check (jvallejo@redhat.com)
- Only store failures that were not ignored. (rhcarvalho@gmail.com)
- Add overlay to supported Docker storage drivers (rhcarvalho@gmail.com)
- ansible.cfg: improve ssh ControlPath (lmeyer@redhat.com)
- openshift_checks: fix execute_module params (lmeyer@redhat.com)
- OCP build: override python-directed envvars (lmeyer@redhat.com)
- OCP build: fix bug 1465724 (lmeyer@redhat.com)
- OCP build: sync packages needed (lmeyer@redhat.com)
- Adding create permissions for serviceclasses.servicecatalog.k8s.io to
  service-catalog-controller role (ewolinet@redhat.com)
- Fix calico when certs are auto-generated (djosborne10@gmail.com)
- Removing trailing newline. (kwoodson@redhat.com)
- Error upgrading control_plane when user is not system:admin
  (jkaur@redhat.com)
- [Bz 1468113] Configure the rest of the masters with the correct URL.
  (kwoodson@redhat.com)

* Tue Jul 11 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.141-1
- Add evaluate_groups.yml to network_manager playbook (rteague@redhat.com)
- updating fetch tasks to be flat paths (ewolinet@redhat.com)

* Mon Jul 10 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.140-1
-

* Sat Jul 08 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.139-1
- increase implicit 300s default timeout to explicit 600s (jchaloup@redhat.com)

* Sat Jul 08 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.138-1
- Wait for etcd to become healthy before migrating TTL (tbielawa@redhat.com)
- Use openshift.node.nodename as glusterfs_hostname. (abutcher@redhat.com)
- container-engine: Update Fedora registry url (smilner@redhat.com)
- updating configmap map definition to fix asb not starting up correctly
  (ewolinet@redhat.com)
- xPaas v1.4.1 for 3.4 (sdodson@redhat.com)
- xPaas v1.4.1 for 3.5 (sdodson@redhat.com)
- xPaaS 1.4.1 for 3.6 (sdodson@redhat.com)
- Only add entries to NO_PROXY settings if a NO_PROXY value is set
  (tbielawa@redhat.com)
- fixing configuation values. (shurley@redhat.com)

* Fri Jul 07 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.137-1
- Install container-selinux with container-engine (smilner@redhat.com)
- Bug 1466152 - Json-file log driver: Neither
  "openshift_logging_fluentd_use_journal=false" nor omitted collects the log
  entries (rmeggins@redhat.com)
- Adding serial: 1 to play to ensure we run one at a time (ewolinet@redhat.com)
- Fix yamllint (sdodson@redhat.com)
- Workaround seboolean module with setsebool command. (abutcher@redhat.com)
- Removed quotes and added env variable to be specific. (kwoodson@redhat.com)
- [BZ 1467786] Fix for OPENSHIFT_DEFAULT_REGISTRY setting.
  (kwoodson@redhat.com)
- set the proper label of /var/lib/etcd directory (jchaloup@redhat.com)

* Thu Jul 06 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.136-1
- Synching certs and aggregator configs from first master to all other masters
  (ewolinet@redhat.com)
- Addressing servicecatalog doesnt have enough permissions and multimaster
  config for service-catalog (ewolinet@redhat.com)
- add back mux_client config that was removed (rmeggins@redhat.com)
- use master etcd certificates when delegating oadm migrate etcd-ttl
  (jchaloup@redhat.com)

* Wed Jul 05 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.135-1
- Update the tag for enterprise service catalog (sdodson@redhat.com)
- Fix missing service domain .svc in NO_PROXY settings (tbielawa@redhat.com)
- drop etcdctl before the etcd_container service (jchaloup@redhat.com)
- Fix prefix for OCP service-catalog prefix (sdodson@redhat.com)
- Fully qualify ocp ansible_service_broker_image_prefix (sdodson@redhat.com)

* Wed Jul 05 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.134-1
-

* Tue Jul 04 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.133-1
- etcd, syscontainer: fix copy of existing datastore (gscrivan@redhat.com)
- pre-pull images before stopping docker (jchaloup@redhat.com)
- Always convert no_proxy from string into a list (sdodson@redhat.com)
- fix 1466680. Fix logging deploying to the specified namespace
  (jcantril@redhat.com)
- logging_es: temporarily disable readiness probe (jwozniak@redhat.com)
- Fixes to storage migration (sdodson@redhat.com)

* Mon Jul 03 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.132-1
-

* Sun Jul 02 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.131-1
- Fix upgrade (sdodson@redhat.com)
- Prevent the script to use default route ip as upstream nameserver.
  (steveteuber@users.noreply.github.com)
- Use default ports for dnsmasq and node dns (sdodson@redhat.com)
- Run dns on the node and use that for dnsmasq (sdodson@redhat.com)
- Using ca-bundle.crt to connect to local etcd if master.etcd-ca.crt DNE
  (ewolinet@redhat.com)
- Set OPENSHIFT_DEFAULT_REGISTRY in registry dc. (abutcher@redhat.com)
- Updating to use openshift.master.etcd_hosts for etcd servers for apiserver
  (ewolinet@redhat.com)
- Update v1.4 image streams and templates (sdodson@redhat.com)
- xPaaS v1.4.0 for v3.4 (sdodson@redhat.com)
- Sync latest image streams and templates for v1.5 (sdodson@redhat.com)
- xPaaS v1.4.0 for v3.5 (sdodson@redhat.com)
- Update latest image streams for v3.6 (sdodson@redhat.com)
- Bump xPaas v1.4.0 for v3.6 (sdodson@redhat.com)
- docker_image_availability: fix containerized etcd (lmeyer@redhat.com)
- evalute etcd backup directory name only once (jchaloup@redhat.com)
- run etcd_container with type:spc_t label (jchaloup@redhat.com)
- Fixing ops storage options being passed to openshift_logging_elasticsearch
  role fixing default ops pv selector (ewolinet@redhat.com)
- Adding labels for elasticsearch and kibana services (ewolinet@redhat.com)
- Add a retry to the docker restart handler (sdodson@redhat.com)
- docker_storage check: make vgs return sane output (lmeyer@redhat.com)
- Capture exceptions when resolving available checks (rhcarvalho@gmail.com)
- PAPR: customize disk space requirements (rhcarvalho@gmail.com)
- Enable disk check on containerized installs (rhcarvalho@gmail.com)
- Add module docstring (rhcarvalho@gmail.com)
- Add suggestion to check disk space in any path (rhcarvalho@gmail.com)
- Require at least 1GB in /usr/bin/local and tempdir (rhcarvalho@gmail.com)
- Refactor DiskAvailability for arbitrary paths (rhcarvalho@gmail.com)
- Adding some more sections to additional considerations, being less rigid on
  large roles for composing -- can also be a playbook (ewolinet@redhat.com)
- Updating snippet contents, formatting and providing urls
  (ewolinet@redhat.com)
- Update snippets and add bullet point on role dependency (ewolinet@redhat.com)
- Creating initial proposal doc for review (ewolinet@redhat.com)

* Fri Jun 30 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.129-1
- Fix generate role binding destination for the HOSA service account
  (steveteuber@users.noreply.github.com)
- Correct version comparisons to ensure proper evaluation (rteague@redhat.com)
- Adding become: false to local_action tasks (ewolinet@redhat.com)
- upgrade: fix name for the etcd system container (gscrivan@redhat.com)
- fix backup and working directory for etcd run as a system container
  (jchaloup@redhat.com)
- etcd_migrate: Add /var/usrlocal/bin to path for oadm (smilner@redhat.com)
- etcd_migrate: Add /usr/local/bin to path for oadm (smilner@redhat.com)
- Sync environment variables FLUENTD/MUX_CPU_LIMIT FLUENTD/MUX_MEMORY_LIMIT
  with the resource limit values. (nhosoi@redhat.com)
- Update master configuration for named certificates during master cert
  redeploy. (abutcher@redhat.com)
- Get rid of openshift_facts dep in rhel_subscribe (sdodson@redhat.com)
- logging: write ES heap dump to persistent storage (jwozniak@redhat.com)

* Thu Jun 29 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.128-1
- parameterize etcd binary path (fabian@fabianism.us)
- attach leases via the first master only and only once (jchaloup@redhat.com)
- evalute groups when running etcd upgrade from byo/openshift-
  cluster/upgrades/upgrade_etcd.yml (jchaloup@redhat.com)
- Bug 1465168 - mux doesn't recognize ansible boolean parameters correctly
  (rmeggins@redhat.com)

* Tue Jun 27 2017 Scott Dodson <sdodson@redhat.com> 3.6.123.1003-1
- Generate loopback kubeconfig separately to preserve OpenShift CA certificate.
  (abutcher@redhat.com)
- registry: look for the oc executable in /usr/local/bin and ~/bin
  (gscrivan@redhat.com)
- router: look for the oc executable in /usr/local/bin and ~/bin
  (gscrivan@redhat.com)
- Retry docker startup once (sdodson@redhat.com)

* Tue Jun 27 2017 Scott Dodson <sdodson@redhat.com> 3.6.123.1002-1
- Fix typo in fluentd_secureforward_contents variable
  (Andreas.Dembach@dg-i.net)
- Reverting quotation change in ansible_service_broker install for etcd
  (ewolinet@redhat.com)

* Mon Jun 26 2017 Scott Dodson <sdodson@redhat.com> 3.6.123.1001-1
- oc_atomic_container: use rpm to check the version. (gscrivan@redhat.com)
- Fix .spec for stagecut (jupierce@redhat.com)
- Picking change from sdodson (ewolinet@redhat.com)
- openshift_version: skip nfs and lb hosts (smilner@redhat.com)
- openshift_checks: eval groups before including role (lmeyer@redhat.com)
- Adding volume fact for etcd for openshift ansible service broker
  (ewolinet@redhat.com)
- Updating to label node and wait for apiservice to be healthy and started
  (ewolinet@redhat.com)
- Also configure default registry on HA masters (sdodson@redhat.com)
- Fix parsing certs with very large serial numbers (tbielawa@redhat.com)
- fix yamllint issues (fabian@fabianism.us)
- openshift_logging: use empty default for storage labels (fsimonce@redhat.com)
- Set clean install and etcd storage on first master to fix scaleup
  (sdodson@redhat.com)
- images, syscontainer: change default value for ANSIBLE_CONFIG
  (gscrivan@redhat.com)
- Cleanup/updates for env variables and etcd image (fabian@fabianism.us)
- Sync 3.5 cfme templates over to 3.6 (sdodson@redhat.com)
- Moving checks down after required initialization happens.
  (kwoodson@redhat.com)
- add play and role to install ansible-service-broker (fabian@fabianism.us)
- Creation of service_catalog and placeholder broker roles
  (ewolinet@redhat.com)
- GlusterFS: Use proper namespace for heketi command and service account
  (jarrpa@redhat.com)
- Fixing quote issue. (kwoodson@redhat.com)
- GlusterFS: Fix heketi secret name (jarrpa@redhat.com)
- Fix for dynamic pvs when using storageclasses. (kwoodson@redhat.com)
- Ensure that host pki tree is mounted in containerized components
  (sdodson@redhat.com)

* Fri Jun 23 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.123-1
- releases: enable build/push with multiple tags (lmeyer@redhat.com)
- Update template examples for 3.6 (rteague@redhat.com)
- Reverting v prefix introduced by stagecut (smunilla@redhat.com)
- Fixed readme doc. (kwoodson@redhat.com)
- Adding version field for stagecut (smunilla@redhat.com)
- Remove package_update from install playbook (rhcarvalho@gmail.com)
- Restart NetworkManager only if dnsmasq was used
  (bliemli@users.noreply.github.com)
- remove extra close brace in example inventory (gpei@redhat.com)
- Adding option for serviceAccountConfig.limitSecretReferences
  (kwoodson@redhat.com)
- doc: Add system_container examples to inventory (smilner@redhat.com)
- system_containers: Add openshift_ to other system_container vars
  (smilner@redhat.com)
- system_containers: Add openshift_ to use_system_containers var
  (smilner@redhat.com)
- detect etcd service name based on etcd runtime when restarting
  (jchaloup@redhat.com)
- set proper etcd_data_dir for system container (jchaloup@redhat.com)
- etcd, system_container: do not mask etcd_container (gscrivan@redhat.com)
- etcd, system_container: do not enable system etcd (gscrivan@redhat.com)
- oc_atomic_container: Require 1.17.2 (smilner@redhat.com)
- Verify matched openshift_upgrade_nodes_label (rteague@redhat.com)
- bug 1457642. Use same SG index to avoid seeding timeout (jcantril@redhat.com)

* Wed Jun 21 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.122-1
-

* Tue Jun 20 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.121-1
- Updating default from null to "" (ewolinet@redhat.com)

* Tue Jun 20 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.120-1
- Update atomic-openshift-master.j2 (sdodson@redhat.com)
- Enable push to registry via dns only on clean 3.6 installs
  (sdodson@redhat.com)
- Disable actually pushing to the registry via dns for now (sdodson@redhat.com)
- Add openshift_node_dnsmasq role to upgrade (sdodson@redhat.com)
- Push to the registry via dns (sdodson@redhat.com)

* Tue Jun 20 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.119-1
- Temporarilly only migrate jobs as we were before (sdodson@redhat.com)
- Disable TLS verification in skopeo inspect (rhcarvalho@gmail.com)
- Preserve etcd3 storage if it's already in use (sdodson@redhat.com)
- GlusterFS: Generate better secret keys (jarrpa@redhat.com)
- GlusterFS: Fix error when groups.glusterfs_registry is undefined.
  (jarrpa@redhat.com)
- GlusterFS: Use proper identity in heketi secret (jarrpa@redhat.com)
- GlusterFS: Allow configuration of heketi port (jarrpa@redhat.com)
- GlusterFS: Fix variable typo (jarrpa@redhat.com)
- GlusterFS: Minor template fixes (jarrpa@redhat.com)
- registry: mount GlusterFS storage volume from correct host
  (jarrpa@redhat.com)

* Mon Jun 19 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.117-1
- Run storage upgrade pre and post master upgrade (rteague@redhat.com)
- Introduce etcd migrate role (jchaloup@redhat.com)
- Add support for rhel, aci, vxlan (srampal@cisco.com)

* Sun Jun 18 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.116-1
- PAPR: define openshift_image_tag via command line (rhcarvalho@gmail.com)
- Ensure only one ES pod per PV (peter.portante@redhat.com)
- etcd v3 for clean installs (sdodson@redhat.com)
- Rename cockpit-shell -> cockpit-system (rhcarvalho@gmail.com)
- Update image repo name, images have been moved from 'cloudforms' to
  'cloudforms42' for CF 4.2. (simaishi@redhat.com)
- Update image repo name, images have been moved from 'cloudforms' to
  'cloudforms45' for CF 4.5. (simaishi@redhat.com)
- CloudForms 4.5 templates (simaishi@redhat.com)

* Fri Jun 16 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.114-1
-

* Fri Jun 16 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.113-1
- Make rollout status check best-effort, add poll (skuznets@redhat.com)
- Verify the rollout status of the hosted router and registry
  (skuznets@redhat.com)
- fix es routes for new logging roles (rmeggins@redhat.com)

* Thu Jun 15 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.112-1
- Add the the other featured audit-config paramters as example (al-
  git001@none.at)

* Thu Jun 15 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.111-1
- doc: Info for system container installer options (smilner@redhat.com)
- Add ANSIBLE_CONFIG to system container installer (smilner@redhat.com)
- Add missing file. Remove debugging prompt. (tbielawa@redhat.com)
- Update readme one last time (tbielawa@redhat.com)
- Reconfigure masters in serial to avoid HA meltdowns (tbielawa@redhat.com)
- First POC of a CFME turnkey solution in openshift-anisble
  (tbielawa@redhat.com)
- Reverted most of this pr 4356 except:   adding
  openshift_logging_fluentd_buffer_queue_limit: 1024
  openshift_logging_fluentd_buffer_size_limit: 1m
  openshift_logging_mux_buffer_queue_limit: 1024
  openshift_logging_mux_buffer_size_limit: 1m   and setting the matched
  environment variables. (nhosoi@redhat.com)
- Adding the defaults for openshift_logging_fluentd_{cpu,memory}_limit to
  roles/openshift_logging_fluentd/defaults/main.yml. (nhosoi@redhat.com)
- Adding environment variables FLUENTD_CPU_LIMIT, FLUENTD_MEMORY_LIMIT,
  MUX_CPU_LIMIT, MUX_MEMORY_LIMIT. (nhosoi@redhat.com)
- Introducing fluentd/mux buffer_queue_limit, buffer_size_limit, cpu_limit, and
  memory_limit. (nhosoi@redhat.com)

* Thu Jun 15 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.110-1
- papr: add documentation to YAML and simplify context (jlebon@redhat.com)
- docs: better documentation for PAPR (jlebon@redhat.com)
- papr: install libffi-devel (jlebon@redhat.com)
- pre-install checks: add more during byo install (lmeyer@redhat.com)
- move etcd backup to etcd_common role (jchaloup@redhat.com)
- Support installing HOSA via ansible (mwringe@redhat.com)
- GlusterFS: Remove requirement for heketi-cli (jarrpa@redhat.com)
- GlusterFS: Fix bugs in wipe (jarrpa@redhat.com)
- GlusterFS: Skip heketi-cli install on Atomic (jarrpa@redhat.com)
- GlusterFS: Create a StorageClass if specified (jarrpa@redhat.com)
- GlusterFS: Use proper secrets (jarrpa@redhat.com)
- GlusterFS: Allow cleaner separation of multiple clusters (jarrpa@redhat.com)
- GlusterFS: Minor corrections and cleanups (jarrpa@redhat.com)
- GlusterFS: Improve documentation (jarrpa@redhat.com)
- GlusterFS: Allow configuration of kube namespace for heketi
  (jarrpa@redhat.com)
- GlusterFS: Adjust when clauses for registry config (jarrpa@redhat.com)
- GlusterFS: Allow failure reporting when deleting deploy-heketi
  (jarrpa@redhat.com)
- GlusterFS: Tweak pod probe parameters (jarrpa@redhat.com)
- GlusterFS: Allow for configuration of node selector (jarrpa@redhat.com)
- GlusterFS: Label on Openshift node name (jarrpa@redhat.com)
- GlusterFS: Make sure timeout is an int (jarrpa@redhat.com)
- GlusterFS: Use groups variables (jarrpa@redhat.com)
- papr: rename redhat-ci related files to papr (jlebon@redhat.com)
- singletonize some role tasks that repeat a lot (lmeyer@redhat.com)

* Wed Jun 14 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.109-1
-

* Wed Jun 14 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.108-1
- Upgraded Calico to 2.2.1 Release (vincent.schwarzer@yahoo.de)

* Wed Jun 14 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.107-1
- Disable negative caching, set cache TTL to 1s (skuznets@redhat.com)
- Update mounts in system container installer (smilner@redhat.com)
- Set ansible retry file location (smilner@redhat.com)
- installer: add bind mount for /etc/resolv.conf (gscrivan@redhat.com)
- Making pylint happy (ewolinet@redhat.com)
- Fix possible access to undefined variable (rhcarvalho@gmail.com)
- certificates: copy the certificates for the etcd system container
  (gscrivan@redhat.com)
- Separate etcd and OpenShift CA redeploy playbooks. (abutcher@redhat.com)
- lib/base: allow for results parsing on non-zero return code
  (jarrpa@redhat.com)
- etcd: system container defines ETCD_(PEER_)?TRUSTED_CA_FILE
  (gscrivan@redhat.com)
- etcd: unmask system container service before installing it
  (gscrivan@redhat.com)
- etcd: copy previous database when migrating to system container
  (gscrivan@redhat.com)
- etcd: define data dir location for the system container (gscrivan@redhat.com)
- oc_obj: set _delete() rc to 0 if err is 'not found' (jarrpa@redhat.com)
- oc_obj: only check 'items' if exists in delete (jarrpa@redhat.com)
- Removed hardocded Calico Policy Controller URL (vincent.schwarzer@yahoo.de)
- Allowing openshift_metrics to specify PV selectors and allow way to define
  selectors when creating pv (ewolinet@redhat.com)

* Tue Jun 13 2017 Jenkins CD Merge Bot <smunilla@redhat.com> 3.6.100-1
- Change default key for gce (hekumar@redhat.com)
- set etcd working directory for embedded etcd (jchaloup@redhat.com)
- Add daemon-reload handler to openshift_node and notify when /etc/systemd
  files have been updated. (abutcher@redhat.com)
- Use volume.beta.kubernetes.io annotation for storage-classes
  (per.carlson@vegvesen.no)
- Correct master-config update during upgrade (rteague@redhat.com)

* Mon Jun 12 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.99-1
- Replace repoquery with module (jchaloup@redhat.com)
- Consider previous value of 'changed' when updating (rhcarvalho@gmail.com)
- Improve code readability (rhcarvalho@gmail.com)
- Disable excluder only on nodes that are not masters (jchaloup@redhat.com)
- Added includes to specify openshift version for libvirt cluster create.
  Otherwise bin/cluster create fails on unknown version for libvirt deployment.
  (schulthess@puzzle.ch)
- docker checks: finish and refactor (lmeyer@redhat.com)
- oc_secret: allow use of force for secret type (jarrpa@redhat.com)
- add docker storage, docker driver checks (jvallejo@redhat.com)
- Add dependency and use same storageclass name as upstream
  (hekumar@redhat.com)
- Add documentation (hekumar@redhat.com)
- Install default storageclass in AWS & GCE envs (hekumar@redhat.com)

* Fri Jun 09 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.98-1
-

* Fri Jun 09 2017 Scott Dodson <sdodson@redhat.com> 3.6.97-1
- Updated to using oo_random_word for secret gen (ewolinet@redhat.com)
- Updating kibana to store session and oauth secrets for reuse, fix oauthclient
  generation for ops (ewolinet@redhat.com)

* Thu Jun 08 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.89.5-1
- Rename container image to origin-ansible / ose-ansible (pep@redhat.com)

* Thu Jun 08 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.89.4-1
- Guard check for container install based on openshift dictionary key
  (ayoung@redhat.com)
- Separate client config removal in uninstall s.t. ansible_ssh_user is removed
  from with_items. (abutcher@redhat.com)
- Remove supported/implemented barrier for registry object storage providers.
  (abutcher@redhat.com)
- Add node unit file on upgrade (smilner@redhat.com)
- fix up openshift-ansible for use with 'oc cluster up' (jcantril@redhat.com)
- specify all logging index mappings for kibana (jcantril@redhat.com)
- openshift-master: set r_etcd_common_etcd_runtime (gscrivan@redhat.com)
- rename daemon.json to container-daemon.json (smilner@redhat.com)
- Updating probe timeout and exposing variable to adjust timeout in image
  (ewolinet@redhat.com)
- Do not attempt to override openstack nodename (jdetiber@redhat.com)
- Update image stream to openshift/origin:2c55ade (skuznets@redhat.com)

* Wed Jun 07 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.89.3-1
- Use local openshift.master.loopback_url when generating initial master
  loopback kubeconfigs. (abutcher@redhat.com)

* Tue Jun 06 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.89.2-1
-

* Tue Jun 06 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.89.1-1
- Updating image for registry_console (ewolinet@redhat.com)
- add elasticseatch, fluentd, kibana check (jvallejo@redhat.com)
- show correct default value in inventory (mmckinst@redhat.com)
- Skip service restarts within ca redeployment playbook when expired
  certificates are detected. (abutcher@redhat.com)
- Add mtu setting to /etc/sysconfig/docker-network (sdodson@redhat.com)
- Add daemon_reload parameter to service tasks (tbielawa@redhat.com)
- mux uses fluentd cert/key to talk to ES (rmeggins@redhat.com)
- fix curator host, port params; remove curator es volumes
  (rmeggins@redhat.com)
- add mux docs; allow to specify mux namespaces (rmeggins@redhat.com)
- oc_secret: allow for specifying secret type (jarrpa@redhat.com)
- Revert "Merge pull request #4271 from DG-i/master" (skuznets@redhat.com)
- verify upgrade targets separately for each group (masters, nodes, etcd)
  (jchaloup@redhat.com)
- Updating Kibana-proxy secret key name, fixing deleting secrets, fixed extra
  ES dc creation (ewolinet@redhat.com)
- upgrade: Reload systemd before restart (smilner@redhat.com)
- Skip router/registry cert redeploy when
  openshift_hosted_manage_{router,registry}=false (abutcher@redhat.com)
- disable docker excluder before it is updated to remove older excluded
  packages (jchaloup@redhat.com)
- Support byo etcd for calico (djosborne10@gmail.com)
- preflight int tests: fix for package_version changes (lmeyer@redhat.com)
- Remove unnecessary comment. (rhcarvalho@gmail.com)
- update aos_version module to support generic pkgs and versions
  (jvallejo@redhat.com)
- Add separate variables for control plane nodes (sdodson@redhat.com)
- Copy Nuage VSD generated user certificates to Openshift master nodes
  (sneha.deshpande@nokia.com)
- add existing_ovs_version check (jvallejo@redhat.com)
- Tolerate failures in the node upgrade playbook (sdodson@redhat.com)

* Wed May 31 2017 Scott Dodson <sdodson@redhat.com> 3.6.89.0-1
- AMP 2.0 (sdodson@redhat.com)
- add support for oc_service for labels, externalIPs (rmeggins@redhat.com)
- [JMAN4-161] Add templates and pv example for cloudforms jboss middleware
  manager (pgier@redhat.com)

* Wed May 31 2017 Scott Dodson <sdodson@redhat.com> 3.6.89-1
- Adding default value for openshift_hosted_logging_storage_kind
  (ewolinet@redhat.com)
- memory check: use GiB/MiB and adjust memtotal (lmeyer@redhat.com)
- bool (sdodson@redhat.com)
- Metrics: update the imagePullPolicy to be always (mwringe@redhat.com)
- Remove typos that got reintroduced (smilner@redhat.com)
- oc_atomic_container: Workaround for invalid json from atomic command
  (smilner@redhat.com)
- Remove system-package=no from container-engine install (smilner@redhat.com)
- oc_atomic_container: Hard code system-package=no (smilner@redhat.com)
- Updating to generate PVC when storage type is passed in as nfs
  (ewolinet@redhat.com)
- disable become for local actions (Mathias.Merscher@dg-i.net)
- check for rpm version and docker image version equality only if
  openshift_pkg_version and openshift_image_tag are not defined
  (jchaloup@redhat.com)

* Tue May 30 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.86-1
- Reduce memory requirement to 2gb for fedora ci jobs (sdodson@redhat.com)
- openshift_logging: increasing *_elasticsearch_* default CPU and memory
  (jwozniak@redhat.com)
- Updating python-passlib assert (ewolinet@redhat.com)
- allow to configure oreg_url specifically for node or master. refs #4233
  (tobias@tobru.ch)
- Updating registry-console version to be v3.6 instead of 3.6
  (ewolinet@redhat.com)

* Thu May 25 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.85-1
- Prepending v to registry-console version (ewolinet@redhat.com)
- memory health check: adjust threshold for etcd (lmeyer@redhat.com)
- health checks: specify check skip reason (lmeyer@redhat.com)
- health checks: configure failure output in playbooks (lmeyer@redhat.com)
- disk/memory checks: make threshold configurable (lmeyer@redhat.com)
- Show help on how to disable checks after failure (rhcarvalho@gmail.com)
- Allow disabling checks via Ansible variable (rhcarvalho@gmail.com)
- Verify memory and disk requirements before install (rhcarvalho@gmail.com)
- filter_plugins: Allow for multiple pairs in map_from_pairs()
  (jarrpa@redhat.com)

* Wed May 24 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.84-1
- oc_process: Better error output on failed template() call (jarrpa@redhat.com)

* Wed May 24 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.83-1
- Allow a hostname to resolve to 127.0.0.1 during validation (dms@redhat.com)

* Wed May 24 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.82-1
- Fixing tux warnings and some final clean up (ewolinet@redhat.com)
- Appease travis (sdodson@redhat.com)
- preflight int tests: fix test flake (lmeyer@redhat.com)
- Add a readiness probe to the Kibana container (skuznets@redhat.com)
- Create logging deployments with non-zero replica counts (skuznets@redhat.com)
- Pulling changes from master branch (ewolinet@redhat.com)
- Adding some missing changes (ewolinet@redhat.com)
- fixing available variables for 2.3.0 (ewolinet@redhat.com)
- Updating pvc generation names (ewolinet@redhat.com)
- updating delete_logging to use modules (ewolinet@redhat.com)
- Pulling in changes from master (ewolinet@redhat.com)
- Decomposing openshift_logging role into subcomponent roles
  (ewolinet@redhat.com)
- Fix renaming error with calico template files (djosborne10@gmail.com)

* Tue May 23 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.80-1
- RPM workaround for the move of cert playbooks (pep@redhat.com)
- health check playbooks: relocate and expand (lmeyer@redhat.com)

* Tue May 23 2017 Scott Dodson <sdodson@redhat.com> 3.6.69-1
- preflight int tests: fix for openshift_version dep (lmeyer@redhat.com)
- Removing requirement to pass aws credentials (esauer@redhat.com)
- Workaround sysctl module issue with py3 by converting task to lineinfile.
  (abutcher@redhat.com)
- inventory: rename certificates->certificate in router example
  (smilner@redhat.com)
- remove skopeo dependency on docker-py (jvallejo@redhat.com)
- improve error handling for missing vars (jvallejo@redhat.com)
- lib/base: Allow for more complex template params (jarrpa@redhat.com)
- Fix yamllint problems (sdodson@redhat.com)
- add ability to expose Elasticsearch as an external route
  (rmeggins@redhat.com)
- Parameterized Calico/Node Arguments (vincent.schwarzer@yahoo.de)
- Fix auditConfig for non-HA environments (rteague@redhat.com)
- Added Docker Registry Port 5000 to Firewalld (vincent.schwarzer@yahoo.de)
- Added Calicoctl to deployment of Master Nodes (vincent.schwarzer@yahoo.de)
- move etcd upgrade related code into etcd_upgrade role (jchaloup@redhat.com)
- Localhost TMP Dir Fix (vincent.schwarzer@yahoo.de)
- Adjusted Naming Schema of Calico Roles (vincent.schwarzer@yahoo.de)
- Update hosts.*.example to include openshift_hosted_metrics_deployer_version
  (pat2man@gmail.com)
- Fix gpg key path in our repo (sdodson@redhat.com)
- Uninstall: restart docker when container-engine restart hasn't changed.
  (abutcher@redhat.com)
- add etcd cluster size check (jvallejo@redhat.com)
- fix etcd_container_version detection (jchaloup@redhat.com)
- systemcontainercustom.conf.j2: use Environment instead of ENVIRONMENT
  (gscrivan@redhat.com)
- node, systemd: change Requires to Wants for openvswitch (gscrivan@redhat.com)
- Add teams attribute to github identity provider (dms@redhat.com)
- Don't escalate privileges in local tmpdir creation (skuznets@redhat.com)
- Remove use of local_action with delegate_to and switch 'delegate_to:
  localhost' temporary directory cleanup actions to local_actions.
  (abutcher@redhat.com)
- Rework openshift_excluders role (rteague@redhat.com)
- Add regexp for container-engine lineinfile (smilner@redhat.com)
- Default image policy on new clusters to on (ccoleman@redhat.com)
- revert role-specific var name (jvallejo@redhat.com)
- Filter non-strings from the oc_adm_ca_server_cert hostnames parameter.
  (abutcher@redhat.com)
- Don't set-up origin repositories if they've already been configured
  (dms@redhat.com)
- byo inventory versions 1.5 -> 3.6 (smilner@redhat.com)
- byo inventory versions 3.5 -> 3.6 (smilner@redhat.com)
- use dest instead of path for lineinfile (smilner@redhat.com)
- openshift_version: skip rpm version==image version on Atomic
  (gscrivan@redhat.com)
- Add NO_PROXY workaround for container-engine atomic command
  (smilner@redhat.com)
- Add no_proxy to atomic.conf (smilner@redhat.com)
- Include object validation in 3.6 upgrades (sdodson@redhat.com)
- uninstall: handle container-engine (gscrivan@redhat.com)
- Added Calico BGP Port 179 to Firewalld (vincent.schwarzer@yahoo.de)
- Fixed for python3 with Fedora 25 Atomic (donny@fortnebula.com)
- Add docker package for container-engine install (smilner@redhat.com)
- Fix python3 error in repoquery (jpeeler@redhat.com)
- check if hostname is in list of etcd hosts (jvallejo@redhat.com)
- Fix templating of static service files (rteague@redhat.com)
- Fix container image build references (pep@redhat.com)
- Reset selinux context on /var/lib/origin/openshift.common.volumes
  (sdodson@redhat.com)
- Adding assert to check for python-passlib on control host
  (ewolinet@redhat.com)
- Update variable name to standard (rhcarvalho@gmail.com)
- Make class attribute name shorter (rhcarvalho@gmail.com)
- Add module docstring (rhcarvalho@gmail.com)
- Update check (rhcarvalho@gmail.com)
- Change based on feedback (vincent.schwarzer@yahoo.de)
- Removed Hardcoded Calico URLs (vincent.schwarzer@yahoo.de)
- int -> float (rhcarvalho@gmail.com)
- Remove vim line (rhcarvalho@gmail.com)
- add etcd volume check (jvallejo@redhat.com)
- Added additional Calico Network Plugin Checks (vincent.schwarzer@yahoo.de)
- Ensure good return code for specific until loops (smilner@redhat.com)
- add template service broker configurable (jminter@redhat.com)
- Prevent line wrap in yaml dump of IDP, fixes #3912 (rikkuness@gmail.com)

* Sat May 13 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.68-1
- Updating registry-console image version during a post_control_plane upgrade
  (ewolinet@redhat.com)
- Remove userland-proxy-path from daemon.json (smilner@redhat.com)
- Fix whistespace issues in custom template (smilner@redhat.com)
- Always add proxy items to atomic.conf (smilner@redhat.com)
- Move container-engine systemd environment to updated location
  (smilner@redhat.com)
- doc: Add link to daemon.json upstream doc (smilner@redhat.com)
- Remove unused daemon.json keys (smilner@redhat.com)
- bug 1448860. Change recovery_after_nodes to match node_quorum
  (jcantril@redhat.com)
- bug 1441369. Kibana memory limits bug 1439451. Kibana crash
  (jcantril@redhat.com)
- Extend repoquery command (of lib_utils role) to ignore excluders
  (jchaloup@redhat.com)
- lower case in /etc/daemon.json and correct block-registry (ghuang@redhat.com)
- Fix for yedit custom separators (mwoodson@redhat.com)
- Updating 3.6 enterprise registry-console template image version
  (ewolinet@redhat.com)
- Default to iptables on master (sdodson@redhat.com)
- Rename blocked-registries to block-registries (smilner@redhat.com)
- Ensure true is lowercase in daemon.json (smilner@redhat.com)
- use docker_log_driver and /etc/docker/daemon.json to determine log driver
  (rmeggins@redhat.com)
- Temporarily revert to OSEv3 host group usage (rteague@redhat.com)
- Add service file templates for master and node (smilner@redhat.com)
- Update systemd units to use proper container service name
  (smilner@redhat.com)
- polish etcd_common role (jchaloup@redhat.com)
- Note existence of Fedora tests and how to rerun (rhcarvalho@gmail.com)
- Fix for OpenShift SDN Check (vincent.schwarzer@yahoo.de)
- Updating oc_obj to use get instead of getattr (ewolinet@redhat.com)
- Updating size suffix for metrics in role (ewolinet@redhat.com)
- GlusterFS: Allow swapping an existing registry's backend storage
  (jarrpa@redhat.com)
- GlusterFS: Allow for a separate registry-specific playbook
  (jarrpa@redhat.com)
- GlusterFS: Improve role documentation (jarrpa@redhat.com)
- hosted_registry: Get correct pod selector for GlusterFS storage
  (jarrpa@redhat.com)
- hosted registry: Fix typo (jarrpa@redhat.com)
- run excluders over selected set of hosts during control_plane/node upgrade
  (jchaloup@redhat.com)
- Reserve kubernetes and 'kubernetes-' prefixed namespaces
  (jliggitt@redhat.com)
- oc_volume: Add missing parameter documentation (jarrpa@redhat.com)

* Wed May 10 2017 Scott Dodson <sdodson@redhat.com> 3.6.67-1
- byo: correct option name (gscrivan@redhat.com)
- Fail if rpm version != docker image version (jchaloup@redhat.com)
- Perform package upgrades in one transaction (sdodson@redhat.com)
- Properly fail if OpenShift RPM version is undefined (rteague@redhat.com)

* Wed May 10 2017 Scott Dodson <sdodson@redhat.com> 3.6.66-1
- Fix issue with Travis-CI using old pip version (rteague@redhat.com)
- Remove vim configuration from Python files (rhcarvalho@gmail.com)
- Use local variables for daemon.json template (smilner@redhat.com)
- Fix additional master cert & client config creation. (abutcher@redhat.com)

* Tue May 09 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.62-1
-

* Tue May 09 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.61-1
-

* Mon May 08 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.60-1
-

* Mon May 08 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.59-1
- Updating logging and metrics to restart api, ha and controllers when updating
  master config (ewolinet@redhat.com)
- Adding defaults for es_indices (ewolinet@redhat.com)
- Updating logic for generating pvcs and their counts to prevent reuse when
  looping (ewolinet@redhat.com)

* Mon May 08 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.58-1
- Moving Dockerfile content to images dir (jupierce@redhat.com)

* Mon May 08 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.57-1
-

* Sun May 07 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.56-1
-

* Sat May 06 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.55-1
- Fix 1448368, and some other minors issues (ghuang@redhat.com)
- mux startup is broken without this fix (rmeggins@redhat.com)
- Dockerfile: create symlink for /opt/app-root/src (gscrivan@redhat.com)
- docs: Add basic system container dev docs (smilner@redhat.com)
- installer: Add system container variable for log saving (smilner@redhat.com)
- installer: support running as a system container (gscrivan@redhat.com)

* Fri May 05 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.54-1
- Allow oc_ modules to pass unicode results (rteague@redhat.com)
- Ensure repo cache is clean on the first run (rteague@redhat.com)
- move etcdctl.yml from etcd to etcd_common role (jchaloup@redhat.com)
- Modified pick from release-1.5 for updating hawkular htpasswd generation
  (ewolinet@redhat.com)

* Thu May 04 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.53-1
- Correctly setting the primary and replica shard count settings
  (ewolinet@redhat.com)
- System container docker (smilner@redhat.com)
- Stop logging AWS credentials in master role. (dgoodwin@redhat.com)
- Remove set operations from openshift_master_certificates iteration.
  (abutcher@redhat.com)
- Refactor system fact gathering to avoid dictionary size change during
  iteration. (abutcher@redhat.com)
- Refactor secret generation for python3. (abutcher@redhat.com)
- redhat-ci: use requirements.txt (jlebon@redhat.com)

* Wed May 03 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.52-1
- Making mux with_items list evaluate as empty if didnt get objects before
  (ewolinet@redhat.com)
- etcd Upgrade Refactor (rteague@redhat.com)
- v3.3 Upgrade Refactor (rteague@redhat.com)
- v3.4 Upgrade Refactor (rteague@redhat.com)
- v3.5 Upgrade Refactor (rteague@redhat.com)
- v3.6 Upgrade Refactor (rteague@redhat.com)
- Fix variants for v3.6 (rteague@redhat.com)
- Normalizing groups. (kwoodson@redhat.com)
- Use openshift_ca_host's hostnames to sign the CA (sdodson@redhat.com)

* Tue May 02 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.51-1
- Remove std_include from playbooks/byo/rhel_subscribe.yml
  (abutcher@redhat.com)
- Adding way to add labels and nodeselectors to logging project
  (ewolinet@redhat.com)

* Tue May 02 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.50-1
- Don't double quote when conditions (sdodson@redhat.com)
- Remove jinja template delimeters from when conditions (sdodson@redhat.com)
- move excluder upgrade validation tasks under openshift_excluder role
  (jchaloup@redhat.com)
- Fix test compatibility with OpenSSL 1.1.0 (pierre-
  louis.bonicoli@libregerbil.fr)

* Mon May 01 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.49-1
- Warn users about conflicts with docker0 CIDR range (lpsantil@gmail.com)
- Bump ansible rpm dependency to 2.2.2.0 (sdodson@redhat.com)

* Mon May 01 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.48-1
-

* Mon May 01 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.47-1
-

* Mon May 01 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.46-1
- Contrib: Hook to verify modules match assembled fragments
  (tbielawa@redhat.com)

* Mon May 01 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.45-1
-

* Sun Apr 30 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.44-1
- Refactor etcd roles (jchaloup@redhat.com)

* Sat Apr 29 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.43-1
- Document the Pull Request process (rhcarvalho@gmail.com)
- Add Table of Contents (rhcarvalho@gmail.com)
- Improve Contribution Guide (rhcarvalho@gmail.com)
- Replace absolute with relative URLs (rhcarvalho@gmail.com)
- Move repo structure to a separate document (rhcarvalho@gmail.com)
- Remove outdated information about PRs (rhcarvalho@gmail.com)
- Move link to BUILD.md to README.md (rhcarvalho@gmail.com)
- Adding checks for starting mux for 2.2.0 (ewolinet@redhat.com)
- Fix OpenShift registry deployment on OSE 3.2 (lhuard@amadeus.com)

* Fri Apr 28 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.42-1
- Fix certificate check Job examples (pep@redhat.com)
- Add python-boto requirement (pep@redhat.com)

* Thu Apr 27 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.41-1
- Add bool for proper conditional handling (rteague@redhat.com)

* Thu Apr 27 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.40-1
- Fix cluster creation with `bin/cluster` when there’s no glusterfs node
  (lhuard@amadeus.com)

* Thu Apr 27 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.39-1
- Move container build instructions to BUILD.md (pep@redhat.com)
- Elaborate container image usage instructions (pep@redhat.com)

* Wed Apr 26 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.38-1
- .redhat-ci.yml: also publish journal logs (jlebon@redhat.com)
- Standardize all Origin versioning on 3.6 (rteague@redhat.com)
- integration tests: add CI scripts (lmeyer@redhat.com)
- preflight int tests: define image builds to support tests (lmeyer@redhat.com)
- preflight int tests: generalize; add tests (lmeyer@redhat.com)
- Add stub of preflight integration tests (rhcarvalho@gmail.com)
- Move Python unit tests to subdirectory (rhcarvalho@gmail.com)
- Revert "Add /etc/sysconfig/etcd to etcd_container" (sdodson@redhat.com)
- Replace original router cert variable names. (abutcher@redhat.com)
- oc_obj: Allow for multiple kinds in delete (jarrpa@redhat.com)
- Update v1.5 content (sdodson@redhat.com)
- Update v1.6 content (sdodson@redhat.com)
- Make the rhel_subscribe role subscribe to OSE 3.5 channel by default
  (lhuard@amadeus.com)
- Addressing yamllint (ewolinet@redhat.com)
- Updating kibana-proxy secret key for server-tls entry (ewolinet@redhat.com)
- Pick from issue3896 (ewolinet@redhat.com)
- Cleanup comments and remove extraneous tasks (sdodson@redhat.com)
- Store backups in /var/lib/etcd/openshift-backup (sdodson@redhat.com)
- Create member/snap directory encase it doesn't exist (sdodson@redhat.com)
- Copy v3 data dir when performing backup (sdodson@redhat.com)

* Tue Apr 25 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.37-1
- Differentiate between service serving router certificate and custom
  openshift_hosted_router_certificate when replacing the router certificate.
  (abutcher@redhat.com)

* Tue Apr 25 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.36-1
- Update swap disable tasks (rteague@redhat.com)
- Removing resource version to remove object conflicts caused by race
  conditions. (kwoodson@redhat.com)
- cast openshift_logging_use_mux_client to bool (rmeggins@redhat.com)
- mux does not require privileged, only hostmount-anyuid (rmeggins@redhat.com)
- Switched Heapster to use certificates generated by OpenShift
  (juraci@kroehling.de)
- Use metrics and logging deployer tag v3.4 for enterprise (sdodson@redhat.com)
- Remove v1.5 and v1.6 metrics/logging templates (sdodson@redhat.com)

* Sun Apr 23 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.35-1
-

* Fri Apr 21 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.34-1
- GlusterFS: provide default for groups.oo_glusterfs_to_config in with_items
  (jarrpa@redhat.com)

* Fri Apr 21 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.33-1
- Adding module calls instead of command for idempotency. (kwoodson@redhat.com)
- Use return_value when value is constant (pierre-
  louis.bonicoli@libregerbil.fr)
- Add missing mock for locate_oc_binary method (pierre-
  louis.bonicoli@libregerbil.fr)

* Fri Apr 21 2017 Scott Dodson <sdodson@redhat.com> 3.6.32-1
- Don't check excluder versions when they're not enabled (sdodson@redhat.com)

* Fri Apr 21 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.31-1
- Stop all services prior to upgrading, start all services after
  (sdodson@redhat.com)

* Thu Apr 20 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.30-1
- Add Ansible syntax checks to tox (rteague@redhat.com)
- Add /etc/sysconfig/etcd to etcd_container (me@fale.io)
- openshift_version: improve messaging (lmeyer@redhat.com)
- Simplify memory availability check, review tests (rhcarvalho@gmail.com)
- Simplify mixin class (rhcarvalho@gmail.com)
- Simplify disk availability check, review tests (rhcarvalho@gmail.com)
- add disk and memory availability check tests (jvallejo@redhat.com)
- add ram and storage preflight check (jvallejo@redhat.com)
- Fix paths for file includes (rteague@redhat.com)
- Fix instantiation of action plugin in test fixture (rhcarvalho@gmail.com)
- Introduce Elasticsearch readiness probe (lukas.vlcek@gmail.com)
- added a empty file to the contiv empty dir. This allows contiv to be vendored
  in git (mwoodson@redhat.com)

* Wed Apr 19 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.29-1
- Create openshift-metrics entrypoint playbook (rteague@redhat.com)

* Tue Apr 18 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.28-1
- Minor v3.6 upgrade docs fixes (rteague@redhat.com)

* Tue Apr 18 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.27-1
- repo: start testing PRs on Fedora Atomic Host (jlebon@redhat.com)

* Tue Apr 18 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.26-1
- Correct role dependencies (rteague@redhat.com)
- Allow for GlusterFS to provide registry storage (jarrpa@redhat.com)
- Integrate GlusterFS into OpenShift installation (jarrpa@redhat.com)
- GlusterFS playbook and role (jarrpa@redhat.com)

* Mon Apr 17 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.25-1
- Fix default image tag for enterprise (sdodson@redhat.com)
- Cast etcd_debug to a boolean (skuznets@redhat.com)

* Fri Apr 14 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.24-1
- tox tests: pin test requirement versions (lmeyer@redhat.com)
- This is no longer a widely encountered issue (sdodson@redhat.com)
- Standardize use of byo and common for network_manager.yml
  (rteague@redhat.com)
- Disable swap space on nodes at install and upgrade (rteague@redhat.com)
- Do not check package version on non-master/node (rhcarvalho@gmail.com)

* Thu Apr 13 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.23-1
- Refactor initialize groups tasks (rteague@redhat.com)
- tox tests: pin test requirement versions (lmeyer@redhat.com)
- skip PackageAvailability check if not yum (jvallejo@redhat.com)
- Document service_type for openshift-enterprise (rhcarvalho@gmail.com)
- Remove references to outdated deployment_type (rhcarvalho@gmail.com)
- Update deployment_type documentation (rhcarvalho@gmail.com)
- Document merge time trends page (rhcarvalho@gmail.com)
- Remove outdated documentation (rhcarvalho@gmail.com)
- Remove outdated build instructions (rhcarvalho@gmail.com)
- openshift_sanitize_inventory: disallow conflicting deployment types
  (lmeyer@redhat.com)
- Refactor docker upgrade playbooks (rteague@redhat.com)
- Changed Hawkular Metrics secrets to use a format similar to the one
  automatically generated by OpenShift (juraci@kroehling.de)

* Wed Apr 12 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.22-1
- Fixed spelling mistake. (kwoodson@redhat.com)
- Remove unnecessary folder refs (rteague@redhat.com)
- Switching commands for modules during upgrade of router and registry.
  (kwoodson@redhat.com)
- Fixing a compatibility issue with python 2.7 to 3.5 when reading from
  subprocess. (kwoodson@redhat.com)
- Refactor use of initialize_oo_option_facts.yml (rteague@redhat.com)
- preflight checks: refactor and fix aos_version (lmeyer@redhat.com)
- Add external provisioners playbook starting with aws efs (mawong@redhat.com)

* Tue Apr 11 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.21-1
- Adding a query for the existing docker-registry route. (kwoodson@redhat.com)
- Removing docker-registry route from cockpit-ui. (kwoodson@redhat.com)

* Fri Apr 07 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.20-1
- Fixed a bug when oc command fails. (kwoodson@redhat.com)
- openshift_sanitize_inventory: validate release (lmeyer@redhat.com)

* Fri Apr 07 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.19-1
- Add example scheduled certificate check (pep@redhat.com)
- Switch from ignoring to passing on checks (rteague@redhat.com)
- Add tests for action plugin (rhcarvalho@gmail.com)
- Remove unnecessary code (rhcarvalho@gmail.com)
- Make resolve_checks more strict (rhcarvalho@gmail.com)

* Fri Apr 07 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.18-1
- master-api: add mount for /var/log (gscrivan@redhat.com)
- master: add mount for /var/log (gscrivan@redhat.com)
- unexclude excluder if it is to be upgraded and already installed
  (jchaloup@redhat.com)
- Bump calico policy controller (djosborne10@gmail.com)
- Fixed a string format and a lint space issue (kwoodson@redhat.com)
- Fixed name and selector to be mutually exclusive (kwoodson@redhat.com)
- Adding ability to delete by selector. (kwoodson@redhat.com)
- Adding delete with selector support. (kwoodson@redhat.com)

* Thu Apr 06 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.17-1
- Adding signed router cert and fixing server_cert bug. (kwoodson@redhat.com)

* Wed Apr 05 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.16-1
- Removing test coverage for shared code. (kwoodson@redhat.com)
- Port 10255 unnecessary.  Removing all instances (ccallega@redhat.com)
- oo_filters: Disable pylint too-many-lines test (jarrpa@redhat.com)
- oo_collect: Allow list elements to be lists of dict (jarrpa@redhat.com)
- oc_label: handle case where _get() returns no results (jarrpa@redhat.com)
- Addressing py27-yamllint (esauer@redhat.com)
- Add 'docker-registry.default.svc' to cert-redeploy too (sdodson@redhat.com)
- Support unicode output when dumping yaml (rteague@redhat.com)
- Add docker-registry.default.svc short name to registry service signing
  (sdodson@redhat.com)
- oc_configmap: Add missing check for name (jarrpa@redhat.com)
- oo_collect: Update comments to show source of failure (jarrpa@redhat.com)
- openshift_facts: Allow examples_content_version to be set to v1.6
  (jarrpa@redhat.com)
- Restart polkitd to workaround a bug in polkitd (sdodson@redhat.com)
- Add names to openshift_image_tag asserts (smilner@redhat.com)
- doc: Remove atomic-openshift deployment type (smilner@redhat.com)
- openshift_version now requires prepended version formats (smilner@redhat.com)
- Warn if openshift_image_tag is defined by hand for package installs
  (smilner@redhat.com)
- Verify openshift_image_tag is valid during openshift_version main
  (smilner@redhat.com)
- Add openshift_version fact fallback debug messages (smilner@redhat.com)
- cleanup: when in openshift_version tasks are multiline (smilner@redhat.com)
- Compatibility updates to openshift_logging role for ansible 2.2.2.0+
  (esauer@redhat.com)

* Tue Apr 04 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.15-1
- Document etcd_ca_default_days in example inventories. (abutcher@redhat.com)
- Fixed a bug. Ansible requires a msg param when module.fail_json.
  (kwoodson@redhat.com)

* Sat Apr 01 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.14-1
- Update v1.5 content (sdodson@redhat.com)
- Add v1.6 content (sdodson@redhat.com)
- Fix generated code (sdodson@redhat.com)
- bug 1432607.  Allow configuration of ES log destination (jcantril@redhat.com)
- openshift_facts: install python3-dbus package on Fedora nodes.
  (vsemushi@redhat.com)
- Remove kube-nfs-volumes role (mawong@redhat.com)

* Fri Mar 31 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.13-1
- fixed decode switch so it works on OSX (stobias@harborfreight.com)
- Wait for firewalld polkit policy to be defined (sdodson@redhat.com)
- Correct copy task to use remote source (rteague@redhat.com)
- validate and normalize inventory variables (lmeyer@redhat.com)
- Fixed spacing. (kwoodson@redhat.com)
- Fixed docs.  Fixed add_resource. (kwoodson@redhat.com)
- Fixing linting for spaces. (kwoodson@redhat.com)
- Removing initial setting of metrics image prefix and version
  (ewolinet@redhat.com)
- Adding clusterrole to the toolbox. (kwoodson@redhat.com)
- Fixed a bug in oc_volume. (kwoodson@redhat.com)
- Adding a few more test cases.  Fixed a bug when key was empty. Safeguard
  against yedit module being passed an empty key (kwoodson@redhat.com)
- Added the ability to do multiple edits (kwoodson@redhat.com)
- fix es config merge so template does not need quoting. gen then merge
  (jcantril@redhat.com)

* Thu Mar 30 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.12-1
- Update example inventory files to mention certificate validity parameters.
  (vsemushi@redhat.com)
- openshift_hosted: add openshift_hosted_registry_cert_expire_days parameter.
  (vsemushi@redhat.com)
- oc_adm_ca_server_cert.py: re-generate. (vsemushi@redhat.com)
- oc_adm_ca_server_cert: add expire_days parameter. (vsemushi@redhat.com)
- openshift_ca: add openshift_ca_cert_expire_days and
  openshift_master_cert_expire_days parameters. (vsemushi@redhat.com)
- redeploy-certificates/registry.yml: add
  openshift_hosted_registry_cert_expire_days parameter. (vsemushi@redhat.com)
- openshift_master_certificates: add openshift_master_cert_expire_days
  parameter. (vsemushi@redhat.com)
- openshift_node_certificates: add openshift_node_cert_expire_days parameter.
  (vsemushi@redhat.com)
- Update Dockerfile.rhel7 to reflect changes to Dockerfile (pep@redhat.com)

* Wed Mar 29 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.11-1
- Add etcd_debug and etcd_log_package_levels variables (sdodson@redhat.com)
- Make the OCP available version detection excluder free (jchaloup@redhat.com)
- Add test scaffold for docker_image_availability.py (rhcarvalho@gmail.com)
- Add unit tests for package_version.py (rhcarvalho@gmail.com)
- Add unit tests for package_update.py (rhcarvalho@gmail.com)
- Add unit tests for package_availability.py (rhcarvalho@gmail.com)
- Add unit tests for mixins.py (rhcarvalho@gmail.com)
- Test recursively finding subclasses (rhcarvalho@gmail.com)
- Test OpenShift health check loader (rhcarvalho@gmail.com)
- Rename module_executor -> execute_module (rhcarvalho@gmail.com)
- Use oo_version_gte_3_6+ for future versions and treat 1.x origin as legacy.
  Add tests. (abutcher@redhat.com)
- Added 3.5 -> 3.6 upgrade playbooks (skuznets@redhat.com)
- Add oo_version_gte_X_X_or_Y_Y version comparison filters.
  (abutcher@redhat.com)

* Tue Mar 28 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.10-1
- Use meta/main.yml for role dependencies (rteague@redhat.com)
- Upgrade specific rpms instead of just master/node. (dgoodwin@redhat.com)
- Adding namespace to doc. (kwoodson@redhat.com)
- Add calico. (djosborne10@gmail.com)
- Fixing up test cases, linting, and added a return. (kwoodson@redhat.com)
- first step in ocimage (ihorvath@redhat.com)
- ocimage (ihorvath@redhat.com)
- Setting defaults on openshift_hosted. (kwoodson@redhat.com)
- rebase and regenerate (jdiaz@redhat.com)
- fix up things flagged by flake8 (jdiaz@redhat.com)
- clean up and clarify docs/comments (jdiaz@redhat.com)
- add oc_user ansible module (jdiaz@redhat.com)
- Fix etcd cert generation (djosborne10@gmail.com)

* Sat Mar 25 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.9-1
- Found this while searching the metrics role for logging, is this wrong?
  (sdodson@redhat.com)
- Fix overriding openshift_{logging,metrics}_image_prefix (sdodson@redhat.com)
- Make linter happy (sdodson@redhat.com)
- Specify enterprise defaults for logging and metrics images
  (sdodson@redhat.com)
- Update s2i-dotnetcore content (sdodson@redhat.com)
- Stop all services before upgrading openvswitch (sdodson@redhat.com)
- Bug 1434300 - Log entries are generated in ES after deployed logging stacks
  via ansible, but can not be found in kibana. (rmeggins@redhat.com)
- Adding error checking to the delete. (kwoodson@redhat.com)
- Updated comment. (kwoodson@redhat.com)
- Fixed doc.  Updated test to change existing key.  Updated module spec for
  required name param. (kwoodson@redhat.com)
- Adding oc_configmap to lib_openshift. (kwoodson@redhat.com)

* Fri Mar 24 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.8-1
- vendor patched upstream docker_container module. (jvallejo@redhat.com)
- add docker_image_availability check (jvallejo@redhat.com)
- Do not use auto_expand_replicas (lukas.vlcek@gmail.com)
- Adding tests to increase TC. (kwoodson@redhat.com)
- Adding a pvc create test case. (kwoodson@redhat.com)
- Cherry picking from #3711 (ewolinet@redhat.com)

* Thu Mar 23 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.7-1
- openshift_logging calculate min_masters to fail early on split brain
  (jcantril@redhat.com)
- Fixed linting and configmap_name param (kwoodson@redhat.com)
- Adding configmap support. (kwoodson@redhat.com)
- Make /rootfs mount rslave (sdodson@redhat.com)
- Update imageConfig.format on upgrades to match oreg_url (sdodson@redhat.com)
- Adding configmap support and adding tests. (kwoodson@redhat.com)
- Adding oc_volume to lib_openshift. (kwoodson@redhat.com)
- upgrade: restart ovs-vswitchd and ovsdb-server (gscrivan@redhat.com)
- Make atomic-openshift-utils require playbooks of the same version
  (sdodson@redhat.com)

* Wed Mar 22 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.6-1
- Fix copy-pasta docstrings (rhcarvalho@gmail.com)
- Rename _ns -> node_selector (rhcarvalho@gmail.com)
- Reindent code (rhcarvalho@gmail.com)
- Update the failure methods and add required variables/functions
  (tbielawa@redhat.com)
- Import the default ansible output callback on_failed methods
  (tbielawa@redhat.com)
- Switched Cassandra to use certificates generated by OpenShift
  (juraci@kroehling.de)
- Allow user to specify additions to ES config (jcantril@redhat.com)

* Tue Mar 21 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.5-1
- Attempt to match version of excluders to target version (sdodson@redhat.com)
- Get rid of adjust.yml (sdodson@redhat.com)
- Protect against missing commands (sdodson@redhat.com)
- Simplify excluder enablement logic a bit more (sdodson@redhat.com)
- Add tito releaser for 3.6 (smunilla@redhat.com)
- Adding oc_group to lib_openshift (kwoodson@redhat.com)
- preflight checks: improve user output from checks (lmeyer@redhat.com)
- preflight checks: bypass RPM excludes (lmeyer@redhat.com)
- acceptschema2 default: true (aweiteka@redhat.com)
- Do not require python-six via openshift_facts (rhcarvalho@gmail.com)

* Sat Mar 18 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.4-1
- Cherry picking from #3689 (ewolinet@redhat.com)
- Moving projects task within openshift_hosted (rteague@redhat.com)
- Refactor openshift_projects role (rteague@redhat.com)
- Add unit tests for existing health checks (rhcarvalho@gmail.com)
- Do not update when properties when not passed. (kwoodson@redhat.com)
- change shell to bash in generate_jks.sh (l@lmello.eu.org)

* Fri Mar 17 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.3-1
- enable docker excluder since the time it is installed (jchaloup@redhat.com)

* Thu Mar 16 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.2-1
- enable excluders during node/master scaling up (jchaloup@redhat.com)
- Fixing variable naming for 35 scoping. (kwoodson@redhat.com)
- Fix get_router_replicas infrastructure node count. (abutcher@redhat.com)
- Fix containerized openvswitch race (sdodson@redhat.com)

* Thu Mar 16 2017 Jenkins CD Merge Bot <tdawson@redhat.com> 3.6.1-1
- Bump version to 3.6.0 (smunilla@redhat.com)
- Improve CONTRIBUTING guide with testing tricks (rhcarvalho@gmail.com)
- Update versions in example inventories (sdodson@redhat.com)
- Only call excluder playbooks on masters and nodes (sdodson@redhat.com)
- Since we've decided that we're no longer paying attention to current status
  remove this as it was toggling things (sdodson@redhat.com)
- Remove travis notifications (jdetiber@redhat.com)
- Removing dependency on master facts for master_public_url default
  (ewolinet@redhat.com)
- don't assume openshift_upgrade_target is in a form d.d (jchaloup@redhat.com)
- Cherry picked from #3657 (ewolinet@redhat.com)
- Revert "Enable docker during installation and upgrade by default"
  (skuznets@redhat.com)
- Nuage service account handling by single master
  (vishal.patil@nuagenetworks.net)
- Add router svcacct cluster-reader role (rteague@redhat.com)
- Cherry picking from #3644 (ewolinet@redhat.com)
- Revert module_utils six for openshift_health_checker (jdetiber@redhat.com)
- Refactor and remove openshift_serviceaccount (rteague@redhat.com)
- Fix typo (sdodson@redhat.com)
- Force to use TLSv1.2 (related to https://github.com/openshift/openshift-
  ansible/pull/2707) (olivier@openkumo.fr)
- Raise on dry-run failures. (kwoodson@redhat.com)
- validate excluders on non-atomic hosts only (jchaloup@redhat.com)
- enable docker excluder since the time it is installed (jchaloup@redhat.com)
- cherry picking from #3621 #3614 #3627 (ewolinet@redhat.com)
- Renaming oadm_manage_node to oc_adm_manage_node (rteague@redhat.com)
- add 'hawkular/metrics' when updating config (jcantril@redhat.com)
- update all the masters (jcantril@redhat.com)
- bug 1430661. Update masterConfig metricsPublicURL on install
  (jcantril@redhat.com)
- nuage: Move role back to config (smilner@redhat.com)
- Fix incorrect comparison when detecting petsets (tbielawa@redhat.com)
- Removed unused, unwanted, incorrectly committed code. (kwoodson@redhat.com)
- Minor updates to README_CONTAINER_IMAGE.md (pep@redhat.com)
- Fix references to openshift_set_node_ip in inventory examples
  (gskgoskk@gmail.com)
- Bug 1428711 - [IntService_public_324] ES pod is unable to read
  searchguard.truststore after upgarde logging from 3.3.1 to 3.5.0
  (rmeggins@redhat.com)
- bug 1428249. Use ES hostmount storage if it exists (jcantril@redhat.com)
- Use ansible.compat.six where possible (jdetiber@redhat.com)
- Remove debug task (tbielawa@redhat.com)
- Use six from ansible.module_utils for remote hosts (jdetiber@redhat.com)
- re-enable excluders if they are enabled after openshift version detection
  (jchaloup@redhat.com)
- Allow overriding minTLSVersion and cipherSuites (meggen@redhat.com)
- extend the excluders to containerized deployment (jchaloup@redhat.com)
- Fixing the way policies are found.  The old method was unreliable.  This
  method searches all and matches on properties. (kwoodson@redhat.com)
- openshift_excluders depends on openshift_repos (sdodson@redhat.com)
- add ability to specify an etcd version (mmckinst@umich.edu)
- Lowering test coverage percentage. (kwoodson@redhat.com)
- Removing ordereddict.  Replaced with sorted keys. (kwoodson@redhat.com)
- New role (tbielawa@redhat.com)
- Fixed for linting. (kwoodson@redhat.com)
- enable excluders by default (jchaloup@redhat.com)
- ignore the docker excluder status if it is not enabled by a user
  (jchaloup@redhat.com)
- Fix pylint/pyflakes errors on master (sdodson@redhat.com)
- Identify PetSets in 3.4 clusters and fail if any are detected
  (tbielawa@redhat.com)
- More logging fixes (ewolinet@redhat.com)
- Fix for issue 3541 (srampal@cisco.com)
- Fix to OpenshiftCLIConfig to support an ordereddict.  This was breaking test
  cases. (kwoodson@redhat.com)
- - update excluders to latest, in non-upgrade scenarios do not update - check
  both available excluder versions are at most of upgrade target version - get
  excluder status through status command - make excluders enablement
  configurable (jchaloup@redhat.com)
- Adding scripts for building and pushing images (bleanhar@redhat.com)
- Adding test_oc_adm_router. (kwoodson@redhat.com)
- Loosely couple docker to iptables service (rteague@redhat.com)
- Generic message directing people to contact support (sdodson@redhat.com)
- Fixing plugin, nodeselectors, and secret pull check (ewolinet@redhat.com)
- Adding into the origin inventory doc. (kwoodson@redhat.com)
- Add oc_objectvalidator to upgrade check (sdodson@redhat.com)
- Augmenting documentation for router sharding. (kwoodson@redhat.com)
- Adding router test. (kwoodson@redhat.com)
- openshift_facts: ensure system containers deps are installed
  (gscrivan@redhat.com)
- Preserve order of Docker registries (eric.mountain@amadeus.com)
- Updating metrics defaults (ewolinet@redhat.com)
- Enable coveralls.io (jdetiber@redhat.com)
- Fix indentation of run_once (sdodson@redhat.com)
- Update docs for test consolidation and remove the Makefile
  (jdetiber@redhat.com)
- Consolidate root/utils tests (jdetiber@redhat.com)
- Remove dummy setup/teardown methods (rhcarvalho@gmail.com)
- Clean up test files (rhcarvalho@gmail.com)
- Remove commented-out test code (rhcarvalho@gmail.com)
- Make generic OCObjectValidator from OCSDNValidator (mkhan@redhat.com)
- logging needs openshift_master_facts before openshift_facts
  (rmeggins@redhat.com)
- separate out test tool configs from setup.cfg (jdetiber@redhat.com)
- Dockerfile and docs to run containerized playbooks (pep@redhat.com)
- Lower test coverage percentage. (kwoodson@redhat.com)
- Mock runs differntly on travis.  Fix the mock test params to be ANY.
  (kwoodson@redhat.com)
- Fixed the none namespace.  Fixed tests with latest loc_oc_binary call.
  (kwoodson@redhat.com)
- Updating the namespace param to None. (kwoodson@redhat.com)
- Regenerated code with latest yedit changes. (kwoodson@redhat.com)
- Fixed tests to align with new naming. (kwoodson@redhat.com)
- Fixed docs.  Added check for delete failures.  Updated namespace to None.
  (kwoodson@redhat.com)
- Fixing linters (kwoodson@redhat.com)
- Adding integration test.  Fixed issue with node_selector.
  (kwoodson@redhat.com)
- Adding oc_project to lib_openshift. (kwoodson@redhat.com)
- Remove old commented-out tests (rhcarvalho@gmail.com)
- Remove redundant assertion (rhcarvalho@gmail.com)
- Fix test (rhcarvalho@gmail.com)
- Lint utils/test (rhcarvalho@gmail.com)
- Rewrap long lines (rhcarvalho@gmail.com)
- Remove unused argument (rhcarvalho@gmail.com)
- Remove unused Makefile variables (rhcarvalho@gmail.com)
- Adding some more logging defaults (ewolinet@redhat.com)
- node/sdn: make /var/lib/cni persistent to ensure IPAM allocations stick
  around across node restart (dcbw@redhat.com)
- BZ1422348 - Don't install python-ruamel-yaml (sdodson@redhat.com)
- Re-generate modules (sdodson@redhat.com)
- Only set ownership to etcd for thirdparty datadir (sdodson@redhat.com)
- Added ports. (kwoodson@redhat.com)
- Fixed router name to produce 2nd router. (kwoodson@redhat.com)
- Updated to work with an array of routers. (kwoodson@redhat.com)
- Adding support for router sharding. (kwoodson@redhat.com)
- Removing the openshift_master_facts dependency (ewolinet@redhat.com)
- bug 1420256. Initialize openshift_logging pvc_facts to empty
  (jcantril@redhat.com)
- Add oc_adm_policy_user task cluster-role policy (rteague@redhat.com)
- Correct config for hosted registry (rteague@redhat.com)
- Fixing checkout for bindings with -binding suffix (jupierce@redhat.com)
- Leave an empty contiv role directory (sdodson@redhat.com)
- Updating stdout check for changed_when (ewolinet@redhat.com)
- test fixes for openshift_certificates_expiry (jdetiber@redhat.com)
- oadm_policy_group/adm_policy_user module (jupierce@redhat.com)
- Fail on Atomic if docker is too old (smilner@redhat.com)
- Remove contiv role and playbook from rpm packages (sdodson@redhat.com)
- Resolving yammlint errors (ewolinet@redhat.com)
- Fixed error handling when oc adm ca create-server-cert fails.  Fixed a logic
  error in secure. (kwoodson@redhat.com)
- removing extra when condition (kwoodson@redhat.com)
- Removing run_once. (kwoodson@redhat.com)
- Adding the activeDeadlineSeconds.  Removed debug. (kwoodson@redhat.com)
- Separating routes so logic is simpler. (kwoodson@redhat.com)
- Defaulting variables properly to avoid undefined route in dict error.
  (kwoodson@redhat.com)
- Add v1.3 FIS templates (sdodson@redhat.com)
- v1.4 Add FIS templates (sdodson@redhat.com)
- Add FIS templates (sdodson@redhat.com)
- Removed duplicate host param. (kwoodson@redhat.com)
- Fixed failures on create when objects exist. (kwoodson@redhat.com)
- Add ca-bundle.crt to list of certs to synchronize. (abutcher@redhat.com)
- Do not force custom ca cert deployment. (abutcher@redhat.com)
- regenerate lib_openshift with yedit exception changes (jdiaz@redhat.com)
- Adding changed_whens for role, rolebinding, and scc reconciliation based on
  output from oadm policy command (ewolinet@redhat.com)
- raise exceptions when walking through object path (jdiaz@redhat.com)
- logging fluentd filter was renamed to viaq (rmeggins@redhat.com)
- Add 'persistentVolumeClaim' to volume_info type (rteague@redhat.com)
- Updating delete/recreate with replace --force. (kwoodson@redhat.com)
- Fixed logic error.  Ensure both svc and dc exist. (kwoodson@redhat.com)
- Modified base debug statements.  Fixed oc_secret debug/verbose flag.  Added
  reencrypt for route. (kwoodson@redhat.com)
- Adding support for a route with certs and reencrypt. (kwoodson@redhat.com)
- node: use the new oc_atomic_container module (gscrivan@redhat.com)
- master: use the new oc_atomic_container module (gscrivan@redhat.com)
- etcd: use the new oc_atomic_container module (gscrivan@redhat.com)
- lib_openshift: new module atomic_container (gscrivan@redhat.com)
- Combined (squashed) commit for all changes related to adding Contiv support
  into Openshift Ansible. This is the first (beta) release of Contiv with
  Openshift and is only supported for Openshift Origin + Bare metal deployments
  at the time of this commit. Please refer to the Openshift and Contiv official
  documentation for details of the level of support for different features and
  modes of operation. (srampal@cisco.com)
- Re-generate lib_openshift (sdodson@redhat.com)
- Make s3_volume_mount available to set_fact call (smilner@redhat.com)
- Correct fact creation for pvc (rteague@redhat.com)
- [oc_obj] Move namespace argument to end of command. (abutcher@redhat.com)
- Create hosted registry service (rteague@redhat.com)
- Correct typo in haproxy router collection. (abutcher@redhat.com)
- Fix issue #3505, add notes about origin upgrade versions support in BYO
  upgrade README file (contact@stephane-klein.info)
- Moving replica logic to filter_plugin to fix skipped task variable behavior.
  (kwoodson@redhat.com)
- install the latest excluders (jchaloup@redhat.com)
- openshift_hosted: Update tasks to use oc_ modules (rteague@redhat.com)
- Rebased. (kwoodson@redhat.com)
- Fixed indentation (kwoodson@redhat.com)
- Adding get_env_var to deploymentconfig. (kwoodson@redhat.com)
- Fixed default variables.  Added a fix to generated secret in env var.
  (kwoodson@redhat.com)
- Revert "Add centos paas sig common" (sdodson@redhat.com)
- Fix Quick Installer failed due to a Python method failure
  (tbielawa@redhat.com)
- Removed JGroups cert and password generation. (juraci@kroehling.de)
- Fix symlink to lookup_plugins/oo_option.py (jchaloup@redhat.com)
- Use 2 and 3 friendly urlparse in oo_filters (smilner@redhat.com)
- Update v1.5 content (sdodson@redhat.com)
- Update v1.4 content (sdodson@redhat.com)
- xPaaS ose-v1.3.6 (sdodson@redhat.com)
- Prepare for origin moving to OCP version scheme (ccoleman@redhat.com)
- initialize_openshift_version: handle excluder packages (gscrivan@redhat.com)
- Add insecure edge termination policy for kibana. (whearn@redhat.com)
- openshift_logging default to 2 replicas of primary shards
  (jcantril@redhat.com)
- Fixing doc for oc_adm_ca_server_cert. (kwoodson@redhat.com)
- Convert selectattr tests to use 'match' (rteague@redhat.com)
- Re-generate lib_openshift and lib_utils libraries (sdodson@redhat.com)
- curator config must be in /etc/curator not /usr/curator (rmeggins@redhat.com)
- Updated for pylint. Fixed create doc. (kwoodson@redhat.com)
- Attempt to handle router preparation errors. (kwoodson@redhat.com)
- Fixing the generate tox tests. (kwoodson@redhat.com)
- BZ1414276 - Quote ansible_ssh_user when determining group id
  (sdodson@redhat.com)
- Moving import to local class. (kwoodson@redhat.com)
- Added required_together.  Added two minor bug fixes for when data is not
  passed. (kwoodson@redhat.com)
- fix up ruamel.yaml/pyyaml no-member lint errors (jdetiber@redhat.com)
- Renamed NotContainerized to NotContainerizedMixin and dropped no-member
  (smilner@redhat.com)
- Removed unrequired no-members from yedit and generated code
  (smilner@redhat.com)
- Removing reference to oadm.  Moved parameter under general params.
  (kwoodson@redhat.com)
- adding tag to update_master_config (ewolinet@redhat.com)
- CloudFront oc_secret contents should be a list (smilner@redhat.com)
- lib_openshift oc file lookup improvements (jdetiber@redhat.com)
- roles/lib_openshift: Handle /usr/local/bin/oc with sudo (walters@verbum.org)
- if no key, cert, cacert, or default_cert is passed then do not pass to oc
  (kwoodson@redhat.com)
- Added backup feature.  Fixed a bug with reading the certificate and verifying
  names.  Added force option. (kwoodson@redhat.com)
- Add SDNValidator Module (mkhan@redhat.com)
- bug 1425321. Default the master api port based on the facts
  (jcantril@redhat.com)
- Bug 1420219 - No log entry can be found in Kibana UI after deploying logging
  stacks with ansible (rmeggins@redhat.com)
- Address cert expiry parsing review comments (tbielawa@redhat.com)
- Fix typo (rhcarvalho@gmail.com)
- Update link to project homepage (rhcarvalho@gmail.com)
- Implement fake openssl cert classes (tbielawa@redhat.com)
- Removed oadm_ references in doc. (kwoodson@redhat.com)
- Remove unused plays (jhadvig@redhat.com)
- Remove pytest-related dependencies from setup.py (rhcarvalho@gmail.com)
- Added copy support when modifying cert and key on existence
  (kwoodson@redhat.com)
- Small spacing fix. (kwoodson@redhat.com)
- Updated doc and defined defaults for signer_* (kwoodson@redhat.com)
- Removed unused code.  Made tests executable. (kwoodson@redhat.com)
- Removing cmd, fixed docs and comments. (kwoodson@redhat.com)
- Rename of oadm_ca to oc_adm_ca.  Decided to whittle down to the direct call,
  server_cert. (kwoodson@redhat.com)
- Fixing doc. (kwoodson@redhat.com)
- Adding oadm_ca to lib_openshift. (kwoodson@redhat.com)
- Fixing docs. Fixed default_cert suggestion. (kwoodson@redhat.com)
- Renamed modules, fixed docs, renamed variables, and cleaned up logic.
  (kwoodson@redhat.com)
- Renaming registry and router roles to oc_adm_ (kwoodson@redhat.com)
- Fixing registry doc and suggestions. (kwoodson@redhat.com)
- Adding router and registry to lib_openshift. (kwoodson@redhat.com)
- bug 142026. Ensure Ops PVC prefix are initialized to empty when ops e…
  nabled (jcantril@redhat.com)
- Reverting logic for verify api handler to be uniform with other ways we
  verify, will be uniformly updated in future (ewolinet@redhat.com)
- bug 1417261. Quote name and secrets in logging templates
  (jcantril@redhat.com)
- openshift_facts: handle 'latest' version (gscrivan@redhat.com)
- Surrounding node selector values with quotes (ewolinet@redhat.com)
- Raise the bar on coverage requirements (rhcarvalho@gmail.com)
- Accept extra positional arguments in tox (rhcarvalho@gmail.com)
- Replace nose with pytest (utils) (rhcarvalho@gmail.com)
- Clean up utils/README.md (rhcarvalho@gmail.com)
- Replace nose with pytest (rhcarvalho@gmail.com)
- Extract assertion common to all tests as function (rhcarvalho@gmail.com)
- Replace nose yield-style tests w/ pytest fixtures (rhcarvalho@gmail.com)
- Configure pytest to run tests and coverage (rhcarvalho@gmail.com)
- Fix validation of generated code (rhcarvalho@gmail.com)
- Make tests run with either nosetests or pytest (rhcarvalho@gmail.com)
- Replace assert_equal with plain assert (rhcarvalho@gmail.com)
- Make usage of short_version/release consistent (rhcarvalho@gmail.com)
- Reorganize tests and helper functions logically (rhcarvalho@gmail.com)
- Remove test duplication (rhcarvalho@gmail.com)
- Move similar test cases together (rhcarvalho@gmail.com)
- Insert paths in the second position of sys.path (rhcarvalho@gmail.com)
- Rename test for consistency (rhcarvalho@gmail.com)
- Replace has_key in new modules (smilner@redhat.com)
- Fix symlink to filter_plugins/oo_filters.py (jchaloup@redhat.com)
- Correct logic test for running pods (rteague@redhat.com)
- Temporarily lower the bar for minimum coverage (rhcarvalho@gmail.com)
- Unset exec bit in tests, add missing requirements (jdetiber@redhat.com)
- Include missing unit tests to test runner config (rhcarvalho@gmail.com)
- Fix tests on Python 3 (rhcarvalho@gmail.com)
- Remove dead code in installer (rhcarvalho@gmail.com)
- Remove dead code (rhcarvalho@gmail.com)
- Document how to find dead Python code (rhcarvalho@gmail.com)
- updating until statments on uri module for api verification
  (ewolinet@redhat.com)
- add dependency on openshift_repos (sdodson@redhat.com)
- Fixing a bug by removing default debug (kwoodson@redhat.com)
- Updating to use uri module instead (ewolinet@redhat.com)
- Updating node playbooks to use oc_obj (rteague@redhat.com)
- Add centos paas sig common (sdodson@redhat.com)
- Disentangle openshift_repos from openshift_facts (sdodson@redhat.com)
- Adding missing handler to resolve error that it was not found
  (ewolinet@redhat.com)
- String compatibility for python2,3 (kwoodson@redhat.com)
- Fix indenting/ordering in router cert redeploy (sdodson@redhat.com)
- post_control_plane.yml: don't fail on grep (gscrivan@redhat.com)
- facts/main: Require Python 3 for Fedora, Python 2 everywhere else
  (walters@verbum.org)
- Fix typo, add symlinks for roles (sdodson@redhat.com)
- Resolve deprecation warning (rteague@redhat.com)
- Revert temporary hack to skip router/registry upgrade. (dgoodwin@redhat.com)
- Don't attempt to install python-ruamel-yaml on atomic (sdodson@redhat.com)
- Pleasing the linting gods. (kwoodson@redhat.com)
- Fixed tests for pyyaml vs ruamel.  Added import logic.  Fixed safe load.
  (kwoodson@redhat.com)
- update example templates+imagestreams (bparees@redhat.com)
- Adding fallback support for pyyaml. (kwoodson@redhat.com)
- bug 1420217. Default ES memory to be compariable to 3.4 deployer
  (jcantril@redhat.com)
- Register cloudfront privkey when required (smilner@redhat.com)
- initialize oo_nodes_to_upgrade group when running control plane upgrade only
  (jchaloup@redhat.com)
- adding some quotes for safety (ewolinet@redhat.com)
- Revert "Add block+when skip to `openshift_facts` tasks" (abutcher@redhat.com)
- Add missing full hostname for the Hawkular Metrics certificate (BZ1421060)
  Fix issue where the signer certificate's name is static, preventing
  redeployments from being acceptable. (mwringe@redhat.com)
- fixing use of oc_scale module (ewolinet@redhat.com)
- fixing default for logging (ewolinet@redhat.com)
- Fix some lint (jdetiber@redhat.com)
- Fixed issue where upgrade fails when using daemon sets (e.g. aggregated
  logging) (adbaldi+ghub@gmail.com)
- upgrades: fix path to disable_excluder.yml (jchaloup@redhat.com)
- Add upgrade job step after the entire upgrade performs (maszulik@redhat.com)
- Ansible Lint cleanup and making filter/lookup plugins used by
  openshift_master_facts available within the role (jdetiber@redhat.com)
- Update variant_version (smilner@redhat.com)
- Add block+when skip to `openshift_facts` tasks (tbielawa@redhat.com)
- Trying to fix up/audit note some changes (tbielawa@redhat.com)
- updating defaults for logging and metrics roles (ewolinet@redhat.com)
- Fix logic for checking docker-registry (rteague@redhat.com)
- node, vars/main.yml: define l_is_ha and l_is_same_version
  (gscrivan@redhat.com)
- Modify playbooks to use oc_obj module (rteague@redhat.com)
- master, vars/main.yml: define l_is_ha and l_is_same_version
  (gscrivan@redhat.com)
- oc route commands now using the oc_route module (smilner@redhat.com)
- Modify playbooks to use oc_label module (rteague@redhat.com)
- Fix cases where child classes override OpenShiftCLI values
  (jdetiber@redhat.com)
- BZ1421860: increase Heapster's metric resolution to 30s (mwringe@redhat.com)
- BZ1421834: increase the Heapster metric resolution to 30s
  (mwringe@redhat.com)
- Fix Bug 1419654 Remove legacy config_base fallback to /etc/openshift
  (sdodson@redhat.com)
- Modify playbooks to use oadm_manage_node module (rteague@redhat.com)
- Removing trailing spaces (esauer@redhat.com)
- Removed adhoc s3_registry (smilner@redhat.com)
- replace 'oc service' command with its lib_openshift equivalent
  (jchaloup@redhat.com)
- Making router pods scale with infra nodes (esauer@redhat.com)
- Provisioning of nfs share and PV for logging ops (efreiber@redhat.com)
- Add libselinux-python dependency for localhost (sdodson@redhat.com)
- oc secrets now done via oc_secret module (smilner@redhat.com)
- More fixes for reboot/wait for hosts. (dgoodwin@redhat.com)
- fix openshift_logging where defaults filter needs quoting
  (jcantril@redhat.com)
- Do not hard code package names (rhcarvalho@gmail.com)
- Refactor code to access values from task_vars (rhcarvalho@gmail.com)
- oc serviceaccount now done via oc_serviceaccount module (smilner@redhat.com)
- bug 1420229. Bounce metrics components to recognize changes on updates or
  upgrades (jcantril@redhat.com)
- node: simplify when conditionals (gscrivan@redhat.com)
- openvswitch: simplify when conditionals (gscrivan@redhat.com)
- uninstall: delete master-api and master-controllers (gscrivan@redhat.com)
- master: support HA deployments with system containers (gscrivan@redhat.com)
- Ensure etcd client certs are regenerated with embedded etcd.
  (abutcher@redhat.com)
- bug 1420425. Allow setting of public facing certs for kibana in
  openshift_logging role (jcantril@redhat.com)
- bug 1399523. Ops pvc should have different prefix from non-ops for
  openshift_logging (jcantril@redhat.com)
- Include rpm/git paths in expiry README. (tbielawa@redhat.com)
- Fixing docs, linting, and comments. (kwoodson@redhat.com)
- fix bug 1420204. Default openshift_logging_use_journal to empty so fluentd
  detects and is consistent with deployer (jcantril@redhat.com)
- Let pylint use as many CPUs as available (rhcarvalho@gmail.com)
- Add note about extraneous virtualenvs (rhcarvalho@gmail.com)
- Document how to create new checks (rhcarvalho@gmail.com)
- Introduce tag notation for checks (rhcarvalho@gmail.com)
- Replace multi-role checks with action plugin (rhcarvalho@gmail.com)
- Removing the /usr/bin/ansible-playbook dependency in in the spec file
  (mwoodson@redhat.com)
- use the correct name for the ruamel-yaml python module (jchaloup@redhat.com)
- Reword module documentation (rhcarvalho@gmail.com)
- Separate import groups with a blank line (rhcarvalho@gmail.com)
- Remove commented-out debugging code (rhcarvalho@gmail.com)
- Replace service account secrets handling with oc_serviceaccount_secret module
  (jchaloup@redhat.com)
- node: refactor Docker container tasks in a block (gscrivan@redhat.com)
- etcd: use as system container (gscrivan@redhat.com)
- Implement uninstall for system containers (gscrivan@redhat.com)
- system-containers: implement idempotent update (gscrivan@redhat.com)
- atomic-openshift: install as a system container (gscrivan@redhat.com)
- make sure cluster_size is an int for arith. ops (rmeggins@redhat.com)
- Bug 1420234 - illegal_argument_exception in Kibana UI. (rmeggins@redhat.com)
- bug 1420538. Allow users to set supplementalGroup for Cassandra
  (jcantril@redhat.com)
- Document openshift_cockpit_deployer_prefix and add
  openshift_cockpit_deployer_version (sdodson@redhat.com)
- Make the cert expiry playbooks runnable (tbielawa@redhat.com)
- Ensure embedded etcd config uses CA bundle. (abutcher@redhat.com)
- bug 1420684. On logging upgrade use the correct value for namespace
  (jcantril@redhat.com)
- Fixing docs. (kwoodson@redhat.com)
- bug 1419962. fix openshift_metrics pwd issue after reinstall where cassandra
  has incorrect pwd exception (jcantril@redhat.com)
- Fixing for linters. (kwoodson@redhat.com)
- Adding test cases. (kwoodson@redhat.com)
- Fixing docs. (kwoodson@redhat.com)
- oc process (ihorvath@redhat.com)
- node: ensure conntrack-tools is installed (gscrivan@redhat.com)
- Updating defaults to pull from previously defined variable names used in
  playbooks (ewolinet@redhat.com)
- Pleasing the linting bot. (kwoodson@redhat.com)
- fixup! master: latest use same predicates as last version
  (gscrivan@redhat.com)
- fixup! master: latest use same priorities as last version
  (gscrivan@redhat.com)
- Adding integration tests. (kwoodson@redhat.com)
- Set image change triggers to auto=true for OCP 3.4 - for v1.5
  (simaishi@redhat.com)
- Reference class instead of self.__class__ within super constructor to avoid
  calling self forever. (abutcher@redhat.com)
- Adding oc_env to lib_openshift. (kwoodson@redhat.com)
- Fixing for flake8 spacing. (kwoodson@redhat.com)
- Fixing tests for linters. (kwoodson@redhat.com)
- Adding port support for route. (kwoodson@redhat.com)
- use pvc_size instead of pv_size for openshift_metrics since the role creates
  claims (jcantril@redhat.com)
- Added temporary kubeconfig file. Fixed tests to coincide with tmpfile.
  (kwoodson@redhat.com)
- Set image change triggers to auto=true for OCP 3.4
  (https://github.com/ManageIQ/manageiq-pods/pull/88) (simaishi@redhat.com)
- fixes 1419839.  Install only heapster for openshift_metrics when heapster
  standalone flag is set (jcantril@redhat.com)
- Adding code to copy kubeconfig before running oc commands.
  (kwoodson@redhat.com)
- master: latest use same predicates as last version (gscrivan@redhat.com)
- master: latest use same priorities as last version (gscrivan@redhat.com)
- Changed lib_openshift to use real temporary files. (twiest@redhat.com)
- Fixed ansible module unit and integration tests and added runners.
  (twiest@redhat.com)
- Moving to ansible variable. (kwoodson@redhat.com)
- Specifying port for wait_for call. (kwoodson@redhat.com)
- Reverting commit 3257 and renaming master_url to openshift_logging_master_url
  (ewolinet@redhat.com)
- [openshift_ca] Reference client binary from openshift_ca_host.
  (abutcher@redhat.com)
- Fix playbooks/byo/openshift_facts.yml include path (sdodson@redhat.com)
- Add missing symlink to roles (rhcarvalho@gmail.com)
- Bump registry-console to 3.5 (sdodson@redhat.com)
- Added oc_serviceaccount_secret to lib_openshift. (twiest@redhat.com)
- fix 1406057. Allow openshift_metrics nodeselectors for components
  (jcantril@redhat.com)
- Use service annotations to redeploy router service serving cert signer cert.
  (abutcher@redhat.com)
- Move excluder disablement into control plane and node upgrade playbooks
  (sdodson@redhat.com)
- Add excluder management to upgrade and config playbooks (sdodson@redhat.com)
- Add openshift_excluder role (sdodson@redhat.com)
- Fix RHEL Subscribe std_include path (tbielawa@redhat.com)
- Copies CloudFront pem file to registry hosts (smilner@redhat.com)
- Remove legacy router/registry certs and client configs from synchronized
  master certs. (abutcher@redhat.com)
- Bump registry to 3.4 (sdodson@redhat.com)
- Sync latest image stream content (sdodson@redhat.com)
- Support latest for containerized version (gscrivan@redhat.com)
- Ensure python2-ruamel-yaml is installed (sdodson@redhat.com)
- openshift_logging link pull secret to serviceaccounts fix unlabel when
  undeploying (jcantril@redhat.com)
- fixes 1414625. Fix check of keytool in openshift_metrics role
  (jcantril@redhat.com)
- Doc enhancements. (kwoodson@redhat.com)
- fixes 1417261. Points playbooks to the correct 3.5 roles for logging and
  metrics (jcantril@redhat.com)
- Change default docker log driver from json-file to journald.
  (abutcher@redhat.com)
- Add logic to verify patched version of Ansible (rteague@redhat.com)
- Restructure certificate redeploy playbooks (abutcher@redhat.com)
- Temporary hack to skip router/registry upgrade. (dgoodwin@redhat.com)
- Fixing linters. (kwoodson@redhat.com)
- run node upgrade if master is node as part of the control plan upgrade only
  (jchaloup@redhat.com)
- Appease yamllint (sdodson@redhat.com)
- Adding import_role to block to resolve when eval (ewolinet@redhat.com)
- Updating oc_apply to use command instead of shell (ewolinet@redhat.com)
- Wrap openshift_hosted_logging import_role within a block.
  (abutcher@redhat.com)
- Adding unit test.  Fixed redudant calls to get. (kwoodson@redhat.com)
- Fixing doc and generating new label with updated base. (kwoodson@redhat.com)
- oc_label ansible module (jdiaz@redhat.com)
- Fixing copy pasta comments.  Fixed required in docs. (kwoodson@redhat.com)
- Fix openshift_hosted_logging bool typo. (abutcher@redhat.com)
- Updating oc_apply changed_when conditions, fixing filter usage for
  openshift_hosted_logging playbook (ewolinet@redhat.com)
- Add default ansible.cfg file (rteague@redhat.com)
- Move current node upgrade tasks under openshift_node_upgrade role
  (jchaloup@redhat.com)
- Fix host when waiting for a master system restart. (dgoodwin@redhat.com)
- Adding bool filter to when openshift_logging_use_ops evals and updating
  oc_apply to handle trying to update immutable fields (ewolinet@redhat.com)
- Fixing for tox tests. (flake8|pylint) (kwoodson@redhat.com)
- Adding unit test for oc_service.  Added environment fix for non-standard oc
  installs. (kwoodson@redhat.com)
- Adding integration tests. (kwoodson@redhat.com)
- Adding oc_service to lib_openshift. (kwoodson@redhat.com)
- Sync etcd ca certs from etcd_ca_host to other etcd hosts
  (jawed.khelil@amadeus.com)

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
