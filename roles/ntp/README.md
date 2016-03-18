# Ansible Role: NTP

[![Build Status](https://travis-ci.org/geerlingguy/ansible-role-ntp.svg?branch=master)](https://travis-ci.org/geerlingguy/ansible-role-ntp)

Installs NTP on RedHat/CentOS and Debian/Ubuntu Linux servers.

## Requirements

None.

## Role Variables

Available variables are listed below, along with default values (see `defaults/main.yml`):

    ntp_enabled: true

Whether to start the ntpd service and enable it at system boot. On many virtual machines that run inside a container (like OpenVZ or VirtualBox), it's recommended you don't run the NTP daemon, since the host itself should be set to synchronize time for all it's child VMs.

    ntp_timezone: America/Chicago

Set the timezone for your server.

    ntp_manage_config: false

Set to true to allow this role to manage the NTP configuration file (`/etc/ntp.conf`).

    ntp_servers:
     - 0.pool.ntp.org iburst
     - 1.pool.ntp.org iburst
     - 2.pool.ntp.org iburst
     - 3.pool.ntp.org iburst

Specify the NTP servers you'd like to use. Only takes effect if you allow this role to manage NTP's configuration, by setting `ntp_manage_config` to `true`.

## Dependencies

None.

## Example Playbook

    - hosts: all
      roles:
        - geerlingguy.ntp

*Inside `vars/main.yml`*:

    ntp_timezone: America/Chicago

## License

MIT / BSD

## Author Information

This role was created in 2014 by [Jeff Geerling](http://jeffgeerling.com/), author of [Ansible for DevOps](http://ansiblefordevops.com/).
