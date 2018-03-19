FROM centos:7

MAINTAINER OpenShift Team <dev@lists.openshift.redhat.com>

USER root

# Add origin repo for including the oc client
COPY images/installer/origin-extra-root /

ARG EXTRA_REPOS
ARG EXTRA_REPO_PKGS

# install ansible and deps
# Doing pyOpenSSL separately due to the fact that some centos SIGs package it
# under the different name python2-pyOpenSSL
RUN INSTALL_PKGS="python-lxml python-dns python2-cryptography openssl java-1.8.0-openjdk-headless python2-passlib httpd-tools openssh-clients origin-clients" \
 && yum install -y --setopt=tsflags=nodocs $INSTALL_PKGS pyOpenSSL \
 && EPEL_PKGS="python2-boto python2-boto3 python2-crypto google-cloud-sdk-183.0.0 which python2-pip.noarch" \
 && EXTRA_REPOS="epel-release ${EXTRA_REPOS}" \
 && EXTRA_REPO_PKGS="${EPEL_PKGS} ${EXTRA_REPO_PKGS}" \
 && EPEL_TESTING_PKGS="ansible" \
 && yum install -y $EXTRA_REPOS \
 && yum install -y --setopt=tsflags=nodocs $EXTRA_REPO_PKGS \
 && yum install -y --setopt=tsflags=nodocs --enablerepo=epel-testing $EPEL_TESTING_PKGS \
 && rpm -V pyOpenSSL || rpm -V python2-pyOpenSSL \
 && rpm -V $INSTALL_PKGS $EXTRA_REPO_PKGS $EPEL_TESTING_PKGS \
 && pip install apache-libcloud~=2.2.1 \
 && yum clean all

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
