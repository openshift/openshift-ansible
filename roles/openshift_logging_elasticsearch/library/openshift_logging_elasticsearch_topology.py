'''
---
module: openshift_logging_elasticsearch_facts
version_added: ""
short_description: Gather facts about the OpenShift logging stack
description:
  - Determine the current facts about the OpenShift logging stack (e.g. cluster size)
options:
author: Red Hat, Inc
'''

# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import
from subprocess import *   # noqa: F402,F403

# ignore pylint errors related to the module_utils import
# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import
from ansible.module_utils.basic import *   # noqa: F402,F403

EXAMPLES = """
- action: openshift_logging_topology
"""

RETURN = """
"""

# constants used for various labels and selectors
# selectors for filtering resources
MASTER_CPU_LIMIT = "500m"
MASTER_MEM_LIMIT = "1Gi"
CLIENTDATA_CPU_LIMIT = "4000m"
CLIENTDATA_MEM_LIMIT = "8Gi"
CLIENTDATA_MEM_REQUESTS = "8Gi"


class OpenshiftLoggingTopology(object):
    ''' The class structure for holding the OpenshiftLogging Topologys'''
    # pylint: disable=too-many-instance-attributes

    def __init__(self, logger, existing_topology, node_topology,
                 cluster_name, cluster_size, cpu_limit, memory_limit,
                 pv_selector, pvc_dynamic, pvc_size, pvc_prefix,
                 storage_group, nodeselector, storage_type):
        # pylint: disable=too-many-arguments
        ''' The init method for OpenshiftLoggingFacts '''
        self.logger = logger
        self.cluster_name = cluster_name
        self._existing_topology = existing_topology
        self._node_topology = node_topology
        self._reconciled_topology = dict()
        if not node_topology:
            # Topology is not provided, variables used to create one
            self._cluster_size = cluster_size
            self._cpu_limit = cpu_limit if cpu_limit else CLIENTDATA_CPU_LIMIT
            self._memory_limit = memory_limit if memory_limit else CLIENTDATA_MEM_LIMIT
            self._pv_selector = pv_selector
            self._pvc_dynamic = pvc_dynamic
            self._pvc_size = pvc_size
            self._pvc_prefix = pvc_prefix
            self._storage_group = storage_group
            self._nodeselector = nodeselector
            self._storage_type = storage_type
        self.facts = dict()

    def add_facts_for(self, kind, facts=None):
        ''' Add facts for the provided kind '''
        self.facts[kind] = facts

    def append_facts_for(self, comp, kind, facts=None):
        ''' Append facts for the provided kind to the list'''
        if comp not in self.facts:
            self.facts[comp] = dict()
        if kind not in self.facts[comp]:
            self.facts[comp][kind] = list()
        if facts:
            self.facts[comp][kind].append(facts)

    def build_topology_from_vars(self):
        '''builds ES node topology from the variables passed to the module'''
        masters = dict(limits=dict(cpu=MASTER_CPU_LIMIT,
                                   memory=MASTER_MEM_LIMIT),
                       requests=dict(memory=MASTER_MEM_LIMIT))
        clientdata_nd = dict(limits=dict(cpu=self._cpu_limit,
                                         memory=self._memory_limit),
                             requests=dict(memory=self._memory_limit),
                             pvc_size=self._pvc_size,
                             storage_group=self._storage_group)
        if self._cluster_size <= 3:
            masters['replicas'] = self._cluster_size
        else:
            masters['replicas'] = 3

        if self._nodeselector:
            masters['nodeSelector'] = self._nodeselector
            clientdata_nd['nodeSelector'] = self._nodeselector

        if self._storage_type:
            clientdata_nd['node_storage_type'] = self._storage_type
        else:
            clientdata_nd['node_storage_type'] = 'emptydir'

        if self._pv_selector:
            clientdata_nd['pv_selector'] = self._pv_selector

        clientdata = list()
        for node in range(self._cluster_size):
            cur_nd = clientdata_nd.copy()
            cur_nd['pvc_name'] = self._pvc_prefix + '-' + str(node)
            clientdata.append(cur_nd)

        if self._cluster_size > 1:
            self._node_topology = dict(masters=masters,
                                       clientdata=clientdata)
        else:
            self._node_topology = dict(clientdatamaster=clientdata[0])


    @staticmethod
    def reconcile_masters(masters_ex, masters_des):
        '''We can scale masters however we want'''
        # pylint: disable=unused-argument
        return masters_des

    @staticmethod
    def find_similar_clientdata_node(nodes_ex, cur_node):
        '''Find similar suitable clientdata node among nodes_ex'''
        nd_storage = cur_node.get('node_storage_type', 'emptydir')
        for node_idx, _ in enumerate(nodes_ex):
            # Check that node is the same
            if nodes_ex[node_idx].get('nodeSelector', {}) == cur_node.get('nodeSelector', {}) and\
               nodes_ex[node_idx].get('node_storage_type') == nd_storage:
                if (nd_storage == 'emptydir') or \
                   ((nd_storage == 'hostmount' and
                     nodes_ex[node_idx].get('hostmount_path') == cur_node.get('hostmount_path'))):
                    return node_idx
                elif nd_storage == 'pvc' and\
                        nodes_ex[node_idx].get('pv_selector') == cur_node.get('pv_selector') and\
                        nodes_ex[node_idx].get('pvc_size') <= cur_node.get('pvc_size'):
                    return node_idx
        raise Exception("Unable to reconcile Elasticsearch node topology. "
                        "Existing node doesn't fit in the desired topology")

    def reconcile_clientdata(self, clientdata_ex, clientdata_des):
        '''Reconsile desired and existing clientdata node topologies'''
        if not clientdata_ex:
            return True
        if not clientdata_des:
            raise Exception("No desired clientdata nodes defined for existing clientdata nodes")
        desired_clientdata = clientdata_des[:]
        if len(clientdata_ex) > len(clientdata_des):
            # TODO: Crash and burn, we can't scale down.
            raise Exception("Scaling down Elasticsearch cluster is not supported")
        for node in clientdata_ex:
            ex_nd_id = self.find_similar_clientdata_node(desired_clientdata, node)
            del desired_clientdata[ex_nd_id]

    def reconcile_clientdatamaster(self, cdm_ex, cdm_des):
        '''We assume we get just 1 existing clientdata node'''
        # pylint: disable=unused-argument

        if not cdm_ex:
            return cdm_des
        if len(cdm_ex) > 1:
            raise Exception("Multi-node clientdatamaster nodes must be converted to separate roles")
        return cdm_des

    def reconcile_node_topology(self):
        '''Reconcile Elasticsearch node topology'''

        masters = OpenshiftLoggingTopology.reconcile_masters(
            self._existing_topology.get('masters', {}),
            self._node_topology.get('masters', {}))
        clientdata = self.reconcile_clientdata(
            self._existing_topology.get('clientdata', []),
            self._node_topology.get('clientdata',{}))
        clientdatamaster = self.reconcile_clientdatamaster(
            self._existing_topology.get('clientdatamaster', []),
            self._node_topology.get('clientdatamaster',{}))
        self._reconciled_topology = dict(masters=masters,
                                         clientdata=clientdata,
                                         clientdatamaster=clientdatamaster)

    def build_facts(self):
        ''' Builds the logging facts and returns them '''

        self.add_facts_for("existing_topology", self._existing_topology)

        if not self._node_topology:
            # We assume that no topology was provided and we'll build
            # the desired topology from vars
            self.build_topology_from_vars()
        self.add_facts_for("node_topology", self._node_topology)

        self.reconcile_node_topology()

        return self.facts


def main():
    ''' The main method '''
    module = AnsibleModule(   # noqa: F405
        argument_spec=dict(
            existing_topology={"default": "{}", "type": "dict"},
            desired_topology={"required": False, "type": "dict", "default": "{}"},
            elasticsearch_clustername={"required": True, "type": "str"},
            elasticsearch_cluster_size={"required": False, "type": "int"},
            elasticsearch_cpu_limit={"required": False, "type": "str"},
            elasticsearch_memory_limit={"required": False, "type": "str"},
            elasticsearch_pv_selector={"required": False, "type": "dict"},
            elasticsearch_pvc_dynamic={"required": False, "type": "str"},
            elasticsearch_pvc_size={"required": False, "type": "str"},
            elasticsearch_pvc_prefix={"required": False, "type": "str"},
            elasticsearch_storage_group={"required": False, "type": "int"},
            elasticsearch_nodeselector={"required": False, "type": "dict"},
            elasticsearch_storage_type={"required": False, "type": "str"}
        ),
        supports_check_mode=False
    )
    try:
        cmd = OpenshiftLoggingTopology(module, module.params['existing_topology'],
                                       module.params['desired_topology'],
                                       module.params['elasticsearch_clustername'],
                                       module.params['elasticsearch_cluster_size'],
                                       module.params['elasticsearch_cpu_limit'],
                                       module.params['elasticsearch_memory_limit'],
                                       module.params['elasticsearch_pv_selector'],
                                       module.params['elasticsearch_pvc_dynamic'],
                                       module.params['elasticsearch_pvc_size'],
                                       module.params['elasticsearch_pvc_prefix'],
                                       module.params['elasticsearch_storage_group'],
                                       module.params['elasticsearch_nodeselector'],
                                       module.params['elasticsearch_storage_type'])
        module.exit_json(
            ansible_facts={"openshift_logging_elasticsearch_topology": cmd.build_facts()}
        )
    # ignore broad-except error to avoid stack trace to ansible user
    # pylint: disable=broad-except
    except Exception as error:
        module.fail_json(msg=str(error))


if __name__ == '__main__':
    main()
