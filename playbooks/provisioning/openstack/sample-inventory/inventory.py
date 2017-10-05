#!/usr/bin/env python

from __future__ import print_function

import json

import shade


if __name__ == '__main__':
    cloud = shade.openstack_cloud()

    inventory = {}

    # TODO(shadower): filter the servers based on the `OPENSHIFT_CLUSTER`
    # environment variable.
    cluster_hosts = [
        server for server in cloud.list_servers()
        if 'metadata' in server and 'clusterid' in server.metadata]

    masters = [server.name for server in cluster_hosts
               if server.metadata['host-type'] == 'master']

    etcd = [server.name for server in cluster_hosts
            if server.metadata['host-type'] == 'etcd']
    if not etcd:
        etcd = masters

    infra_hosts = [server.name for server in cluster_hosts
                   if server.metadata['host-type'] == 'node' and
                   server.metadata['sub-host-type'] == 'infra']

    app = [server.name for server in cluster_hosts
           if server.metadata['host-type'] == 'node' and
           server.metadata['sub-host-type'] == 'app']

    nodes = list(set(masters + infra_hosts + app))

    dns = [server.name for server in cluster_hosts
           if server.metadata['host-type'] == 'dns']

    lb = [server.name for server in cluster_hosts
          if server.metadata['host-type'] == 'lb']

    osev3 = list(set(nodes + etcd + lb))

    groups = [server.metadata.group for server in cluster_hosts
              if 'group' in server.metadata]

    inventory['cluster_hosts'] = {'hosts': [s.name for s in cluster_hosts]}
    inventory['OSEv3'] = {'hosts': osev3}
    inventory['masters'] = {'hosts': masters}
    inventory['etcd'] = {'hosts': etcd}
    inventory['nodes'] = {'hosts': nodes}
    inventory['infra_hosts'] = {'hosts': infra_hosts}
    inventory['app'] = {'hosts': app}
    inventory['dns'] = {'hosts': dns}
    inventory['lb'] = {'hosts': lb}

    for server in cluster_hosts:
        if 'group' in server.metadata:
            group = server.metadata.group
            if group not in inventory:
                inventory[group] = {'hosts': []}
            inventory[group]['hosts'].append(server.name)

    inventory['_meta'] = {'hostvars': {}}

    for server in cluster_hosts:
        ssh_ip_address = server.public_v4 or server.private_v4
        vars = {
            'ansible_host': ssh_ip_address
        }

        if server.public_v4:
            vars['public_v4'] = server.public_v4
        # TODO(shadower): what about multiple networks?
        if server.private_v4:
            vars['private_v4'] = server.private_v4

        node_labels = server.metadata.get('node_labels')
        if node_labels:
            vars['openshift_node_labels'] = node_labels

        inventory['_meta']['hostvars'][server.name] = vars

    print(json.dumps(inventory, indent=4, sort_keys=True))
