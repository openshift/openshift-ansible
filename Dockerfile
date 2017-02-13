# Using playbook2image as a base
# See https://github.com/aweiteka/playbook2image for details on the image
# including documentation for the settings/env vars referenced below
FROM docker.io/aweiteka/playbook2image:latest

MAINTAINER OpenShift Team <dev@lists.openshift.redhat.com>

LABEL name="openshift-ansible" \
      summary="OpenShift's installation and configuration tool" \
      description="A containerized openshift-ansible image to let you run playbooks to install, upgrade, maintain and check an OpenShift cluster" \
      url="https://github.com/openshift/openshift-ansible" \
      io.k8s.display-name="openshift-ansible" \
      io.k8s.description="A containerized openshift-ansible image to let you run playbooks to install, upgrade, maintain and check an OpenShift cluster" \
      io.openshift.expose-services="" \
      io.openshift.tags="openshift,install,upgrade,ansible"

# The playbook to be run is specified via the PLAYBOOK_FILE env var.
# This sets a default of openshift_facts.yml as it's an informative playbook
# that can help test that everything is set properly (inventory, sshkeys)
ENV PLAYBOOK_FILE=playbooks/byo/openshift_facts.yml \
    OPTS="-v" \
    INSTALL_OC=true

# playbook2image's assemble script expects the source to be available in
# /tmp/src (as per the source-to-image specs) so we import it there
ADD . /tmp/src

# Running the 'assemble' script provided by playbook2image will install
# dependencies specified in requirements.txt and install the 'oc' client
# as per the INSTALL_OC environment setting above
RUN /usr/libexec/s2i/assemble

CMD [ "/usr/libexec/s2i/run" ]
