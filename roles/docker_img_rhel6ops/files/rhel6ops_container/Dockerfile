FROM rhel6
MAINTAINER Thomas Wiest <twiest@redhat.com>

ENV CONTAINER docker
ENV USER root
ENV HOME /root
ENV TERM xterm
WORKDIR /root

# creature comforts
ADD bashrc /root/.bashrc

# Add the yum repos
ADD etc/yum.repos.d/ /etc/yum.repos.d

# Add yum vars
RUN echo -n 6 > /etc/yum/vars/majorrelease

# setup links for the yum mirror certs
RUN ln -s /run/secrets/etc-pki-entitlement/yum/client-cert.pem /var/lib/yum/client-cert.pem ; \
    ln -s /run/secrets/etc-pki-entitlement/yum/client-key.pem /var/lib/yum/client-key.pem


RUN rpm --import /etc/pki/rpm-gpg/* && \
yum clean metadata && \
yum -y remove subscription-manager && \
yum -y install vim-enhanced telnet && \
yum -y update && \
yum clean all
