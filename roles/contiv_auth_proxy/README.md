Role Name
=========

Role to install Contiv API Proxy and UI

Requirements
------------

Docker needs to be installed to run the auth proxy container.

Role Variables
--------------

auth_proxy_image specifies the image with version tag to be used to spin up the auth proxy container.
auth_proxy_cert, auth_proxy_key specify files to use for the proxy server certificates.
auth_proxy_port is the host port and auth_proxy_datastore the cluster data store address.

Dependencies
------------

docker

Example Playbook
----------------

- hosts: netplugin-node
  become: true
      roles:
        - { role: auth_proxy, auth_proxy_port: 10000, auth_proxy_datastore: etcd://netmaster:22379 }
