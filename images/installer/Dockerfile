FROM quay.io/centos/centos:stream9

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
RUN yum install -y epel-release 'dnf-command(config-manager)' && \
    yum config-manager --enable built > /dev/null && \
    yum install --setopt=tsflags=nodocs -y \
      python3.11 python3.11-pip python3.11-urllib3 \
      openshift-ansible-test && \
    yum clean all

# Add a symlink to pip3.x.
# Any future use of pip3 can be used after this link is set, rather than specifically calling pip3.x.
RUN ln -s /usr/bin/pip3.11 /usr/bin/pip3

# for ec2_ami_info (in workers-rhel-aws-provision CI step) which requires boto3
RUN pip3 install --no-cache-dir boto3 botocore ansible-core

# ansible-galaxy will not be available until ansible-core is installed
RUN ansible-galaxy collection install -p /usr/share/ansible/collections amazon.aws && \
    find $HOME/.ansible -delete

RUN /usr/local/bin/user_setup \
 && rm /usr/local/bin/usage.ocp

USER ${USER_UID}

WORKDIR ${WORK_DIR}
ENTRYPOINT [ "/usr/local/bin/entrypoint" ]
CMD [ "/usr/local/bin/run" ]
