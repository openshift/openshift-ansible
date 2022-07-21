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
# Add origin repo for including the oc client
COPY images/installer/origin-extra-root /
# Install openshift-ansible RPMs
RUN yum install -y epel-release && \
    yum config-manager --enable built > /dev/null && \
    yum install --setopt=tsflags=nodocs -y \
      'ansible-core < 2.14' \
      python38-dateutil python38-urllib3 \
      openshift-ansible-test && \
    yum clean all

# for ec2_ami_info (in workers-rhel-aws-provision CI step) which requires boto3
RUN ansible-galaxy collection install -p /usr/share/ansible/collections amazon.aws && \
    find $HOME/.ansible -delete && \
    pip3 install boto3

RUN /usr/local/bin/user_setup \
 && rm /usr/local/bin/usage.ocp

USER ${USER_UID}

WORKDIR ${WORK_DIR}
ENTRYPOINT [ "/usr/local/bin/entrypoint" ]
CMD [ "/usr/local/bin/run" ]
