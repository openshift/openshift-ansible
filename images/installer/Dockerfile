FROM centos:7

MAINTAINER OpenShift Team <dev@lists.openshift.redhat.com>

USER root

# Add origin repo for including the oc client
COPY images/installer/origin-extra-root /

# install ansible and deps
RUN INSTALL_PKGS="ansible-2.9.13 azure-cli-2.0.46 java-1.8.0-openjdk-headless python-lxml python-dns openssl python2-passlib httpd-tools openssh-clients origin-clients iproute patch which" \
 && yum install -y --setopt=tsflags=nodocs $INSTALL_PKGS \
 && EPEL_PKGS=" python2-pip.noarch python2-crypto python2-scandir python2-packaging" \
 && yum install -y epel-release \
 && yum install -y --setopt=tsflags=nodocs $EPEL_PKGS \
 && if [ "$(uname -m)" == "x86_64" ]; then yum install -y https://sdodson.fedorapeople.org/google-cloud-sdk-183.0.0-3.el7.x86_64.rpm ; fi \
 && rpm -V $INSTALL_PKGS $EPEL_PKGS \
 && yum clean all

RUN pip install --upgrade 'pip<21' 'setuptools<45' 'wheel' \
 && pip install 'boto' 'pyOpenSSL' 'apache-libcloud' 'SecretStorage<3' 'ansible[azure]' 'boto3'

LABEL name="openshift/origin-ansible" \
      summary="OpenShift's installation and configuration tool" \
      description="A containerized openshift-ansible image to let you run playbooks to install, upgrade, maintain and check an OpenShift cluster" \
      url="https://github.com/openshift/openshift-ansible" \
      io.k8s.display-name="openshift-ansible" \
      io.k8s.description="A containerized openshift-ansible image to let you run playbooks to install, upgrade, maintain and check an OpenShift cluster" \
      io.openshift.expose-services="" \
      io.openshift.tags="openshift,install,upgrade,ansible" \
      atomic.run="once"

ENV USER_UID=1001 \
    HOME=/opt/app-root/src \
    WORK_DIR=/usr/share/ansible/openshift-ansible \
    OPTS="-v"

# Add image scripts and files for running as a system container
COPY images/installer/root /
# Include playbooks, roles, plugins, etc. from this repo
COPY . ${WORK_DIR}

RUN /usr/local/bin/user_setup \
 && rm /usr/local/bin/usage.ocp

USER ${USER_UID}

WORKDIR ${WORK_DIR}
ENTRYPOINT [ "/usr/local/bin/entrypoint" ]
CMD [ "/usr/local/bin/run" ]
