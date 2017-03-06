FROM rhel7

MAINTAINER Troy Dawson <tdawson@redhat.com>

LABEL Name="openshift3/installer"
LABEL Vendor="Red Hat" License=GPLv2+
LABEL Version="v3.1.1.901"
LABEL Release="6"
LABEL BZComponent="aos3-installation-docker"
LABEL Architecture="x86_64"
LABEL io.k8s.description="Ansible code and playbooks for installing Openshift Container Platform." \
      io.k8s.display-name="Openshift Installer" \
      io.openshift.tags="openshift,installer"

RUN INSTALL_PKGS="atomic-openshift-utils" && \
    yum install -y --enablerepo=rhel-7-server-ose-3.2-rpms $INSTALL_PKGS && \
    rpm -V $INSTALL_PKGS && \
    yum clean all

# Expect user to mount a workdir for container output (installer.cfg, hosts inventory, ansible log)
VOLUME /var/lib/openshift-installer/
WORKDIR /var/lib/openshift-installer/

RUN mkdir -p /var/lib/openshift-installer/

ENTRYPOINT ["/usr/bin/atomic-openshift-installer", "-c", "/var/lib/openshift-installer/installer.cfg", "--ansible-log-path", "/var/lib/openshift-installer/ansible.log"]
