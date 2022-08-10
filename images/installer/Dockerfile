FROM quay.io/centos/centos:stream8

MAINTAINER OpenShift Team <dev@lists.openshift.redhat.com>

USER root

LABEL name="openshift/origin-ansible" \
      summary="OpenShift's installation and configuration tool" \
      description="A containerized openshift-ansible image to use in CI - includes necessary packages to test clusters on AWS/GCP/Azure" \
      url="https://github.com/openshift/openshift-ansible" \
      io.k8s.display-name="openshift-ansible" \
      io.k8s.description="A containerized openshift-ansible image to use in CI - includes necessary packages to test clusters on AWS/GCP/Azure" \
      io.openshift.expose-services="" \
      io.openshift.tags="openshift,install,upgrade,ansible" \
      atomic.run="once"

ENV USER_UID=1001 \
    HOME=/opt/app-root/src/ \
    WORK_DIR=/usr/share/ansible/openshift-ansible \
    OPTS="-v"

# Add image scripts and files for running as a system container
COPY images/installer/root /
# Install openshift-ansible RPMs
RUN yum install -y centos-release-ansible-29 epel-release && \
    yum config-manager --enable built > /dev/null && \
    yum install --setopt=tsflags=nodocs -y \
      'ansible < 2.10' \
      openshift-ansible-test && \
    yum clean all

RUN /usr/local/bin/user_setup \
 && rm /usr/local/bin/usage.ocp

USER ${USER_UID}

WORKDIR ${WORK_DIR}
ENTRYPOINT [ "/usr/local/bin/entrypoint" ]
CMD [ "/usr/local/bin/run" ]
