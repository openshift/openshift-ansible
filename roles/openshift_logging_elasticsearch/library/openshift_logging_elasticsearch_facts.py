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

import json

# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import
from subprocess import *   # noqa: F402,F403

# ignore pylint errors related to the module_utils import
# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import
from ansible.module_utils.basic import *   # noqa: F402,F403

import yaml

EXAMPLES = """
- action: opneshift_logging_facts
"""

RETURN = """
"""

DEFAULT_OC_OPTIONS = ["-o", "json"]

# constants used for various labels and selectors
COMPONENT_KEY = "component"
LOGGING_INFRA_KEY = "logging-infra"
CLUSTER_NAME_LABEL = "cluster-name"
ES_ROLE_LABEL = "es-node-role"
# selectors for filtering resources
LOGGING_SELECTOR = LOGGING_INFRA_KEY + "=" + "support"
ROUTE_SELECTOR = "component=support, logging-infra=support, provider=openshift"
COMPONENTS = ["elasticsearch"]
SA_PREFIX = "system:serviceaccount:"


class OCBaseCommand(object):
    ''' The base class used to query openshift '''

    def __init__(self, binary, kubeconfig, namespace):
        ''' the init method of OCBaseCommand class '''
        self.binary = binary
        self.kubeconfig = kubeconfig
        self.user = self.get_system_admin(self.kubeconfig)
        self.namespace = namespace

    # pylint: disable=no-self-use
    def get_system_admin(self, kubeconfig):
        ''' Retrieves the system admin '''
        with open(kubeconfig, 'r') as kubeconfig_file:
            config = yaml.load(kubeconfig_file)
            for user in config["users"]:
                if user["name"].startswith("system"):
                    return user["name"]
        raise Exception("Unable to find system:admin in: " + kubeconfig)

    # pylint: disable=too-many-arguments, dangerous-default-value
    def oc_command(self, sub, kind, namespace=None, name=None, add_options=None):
        ''' Wrapper method for the "oc" command '''
        cmd = [self.binary, sub, kind]
        if name is not None:
            cmd = cmd + [name]
        if namespace is not None:
            cmd = cmd + ["-n", namespace]
        if add_options is None:
            add_options = []
        cmd = cmd + ["--user=" + self.user, "--config=" + self.kubeconfig] + DEFAULT_OC_OPTIONS + add_options
        try:
            process = Popen(cmd, stdout=PIPE, stderr=PIPE)   # noqa: F405
            out, err = process.communicate(cmd)
            if len(err) > 0:
                if 'not found' in err:
                    return {'items': []}
                if 'No resources found' in err:
                    return {'items': []}
                raise Exception(err)
        except Exception as excp:
            err = "There was an exception trying to run the command '" + " ".join(cmd) + "' " + str(excp)
            raise Exception(err)

        return json.loads(out)


class OpenshiftLoggingFacts(OCBaseCommand):
    ''' The class structure for holding the OpenshiftLogging Facts'''
    name = "facts"

    def __init__(self, logger, binary, kubeconfig, namespace, cluster_name):
        # pylint: disable=too-many-arguments
        ''' The init method for OpenshiftLoggingFacts '''
        super(OpenshiftLoggingFacts, self).__init__(binary, kubeconfig, namespace)
        self.logger = logger
        self.cluster_name = cluster_name
        self.facts = dict()

    def default_keys_for(self, kind):
        ''' Sets the default key values for kind '''
        for comp in COMPONENTS:
            self.add_facts_for(comp, kind)

    def add_facts_for(self, kind, name=None, facts=None):
        ''' Add facts for the provided kind '''
#        if comp not in self.facts:
#            self.facts[comp] = dict()
        if kind not in self.facts:
            self.facts[kind] = dict()
        if name:
            self.facts[kind][name] = facts

    def append_facts_for(self, comp, kind, facts=None):
        ''' Append facts for the provided kind to the list'''
        if comp not in self.facts:
            self.facts[comp] = dict()
        if kind not in self.facts[comp]:
            self.facts[comp][kind] = list()
        if facts:
            self.facts[comp][kind].append(facts)

    def facts_for_routes(self, namespace):
        ''' Gathers facts for Routes in logging namespace '''
        self.default_keys_for("routes")
        route_list = self.oc_command("get", "routes", namespace=namespace, add_options=["-l", ROUTE_SELECTOR])
        if len(route_list["items"]) == 0:
            return None
        for route in route_list["items"]:
            name = route["metadata"]["name"]
            self.add_facts_for("routes", name, dict(host=route["spec"]["host"]))
        self.facts["agl_namespace"] = namespace

    def facts_for_pvcs(self, namespace):
        ''' Gathers facts for PVCS in logging namespace'''
        self.default_keys_for("pvcs")
        pvclist = self.oc_command("get", "pvc", namespace=namespace, add_options=["-l", LOGGING_INFRA_KEY])
        if len(pvclist["items"]) == 0:
            return
        for pvc in pvclist["items"]:
            name = pvc["metadata"]["name"]
            self.add_facts_for("pvcs", name, dict())

    def facts_for_ex_node_topology(self, namespace, es_role):
        ''' Gathers facts for DeploymentConfigs in logging namespace '''
        if es_role == "masterclientdata":
            # masterclientdata role exists only for older deployments,
            # so cluster_name will be either "logging-es" or "logging-es-ops"
            selector = "component=" + self.cluster_name[8:] + "," +\
                CLUSTER_NAME_LABEL + "!=" + self.cluster_name
        else:
            selector = CLUSTER_NAME_LABEL + "=" + self.cluster_name +\
                "," + ES_ROLE_LABEL + "=" + es_role
        dclist = self.oc_command("get", "deploymentconfigs",
                                 namespace=namespace,
                                 add_options=["-l", selector])
        if len(dclist["items"]) == 0:
            self.add_facts_for("existing_node_topology", es_role)
            return
        dcs = dclist["items"]
        for dc_item in dcs:
            spec = dc_item["spec"]["template"]["spec"]
            cont_spec = spec["containers"][0]
            resources = cont_spec.get("resources", dict())
            # Detect storage type
            claim_name = ""
            hostmount_path = []
            for volume in spec["volumes"]:
                if volume["name"].startswith("elasticsearch-storage"):
                    if "persistentVolumeClaim" in volume:
                        claim_name = volume["persistentVolumeClaim"]["claimName"]
                        storage_type = "pvc"
                    elif "hostPath" in volume:
                        storage_type = "hostmount"
                        hostmount_path.append(volume["hostPath"]["path"])
                    else:
                        storage_type = "emptydir"
            facts = dict(
                name=dc_item["metadata"]["name"],
                selector=dc_item["spec"]["selector"],
                replicas=dc_item["spec"]["replicas"],
                serviceAccount=spec["serviceAccount"],
                limits=resources.get("limits", dict()),
                requests=resources.get("requests", dict()),
                storage_group=spec["securityContext"]["supplementalGroups"][0],
                nodeSelector=spec.get("nodeSelector", dict()),
                image=cont_spec["image"],
                claim_name=claim_name,
                hostmount_path=hostmount_path,
                node_storage_type=storage_type
            )
            if es_role == "master":
                self.add_facts_for("existing_node_topology", es_role, facts)
            else:
                self.append_facts_for("existing_node_topology", es_role, facts)

    def facts_for_services(self, namespace):
        ''' Gathers facts for services in logging namespace '''
        self.default_keys_for("services")
        servicelist = self.oc_command("get", "services", namespace=namespace)
        if len(servicelist["items"]) == 0:
            return
        for service in servicelist["items"]:
            name = service["metadata"]["name"]
            self.add_facts_for("services", name, dict())

    def facts_for_configmaps(self, namespace):
        ''' Gathers facts for configmaps in logging namespace '''
        self.default_keys_for("configmaps")
        a_list = self.oc_command("get", "configmaps", namespace=namespace)
        if len(a_list["items"]) == 0:
            return
        for item in a_list["items"]:
            name = item["metadata"]["name"]
            self.add_facts_for("configmaps", name, item["data"])

    def facts_for_secrets(self, namespace):
        ''' Gathers facts for secrets in the logging namespace '''
        self.default_keys_for("secrets")
        a_list = self.oc_command("get", "secrets", namespace=namespace)
        if len(a_list["items"]) == 0:
            return
        for item in a_list["items"]:
            name = item["metadata"]["name"]
            if item["type"] == "Opaque":
                result = dict(
                    keys=item["data"].keys()
                )
                self.add_facts_for("secrets", name, result)

    def facts_for_sccs(self):
        ''' Gathers facts for SCCs used with logging '''
        self.default_keys_for("sccs")
        scc = self.oc_command("get", "scc", name="hostaccess")
        if len(scc.get("users", [])) == 0:
            return
        for item in scc["users"]:
            if item.startswith(SA_PREFIX + self.namespace):
                self.add_facts_for("sccs", "hostaccess", [item])

    def facts_for_clusterrolebindings(self, namespace):
        ''' Gathers ClusterRoleBindings used with logging '''
        self.default_keys_for("clusterrolebindings")
        role = self.oc_command("get", "clusterrolebindings", name="cluster-readers")
        if "subjects" not in role or len(role["subjects"]) == 0:
            return
        for item in role["subjects"]:
            if namespace == item.get("namespace"):
                self.add_facts_for("clusterrolebindings", "cluster-readers", dict())

# this needs to end up nested under the service account...
    def facts_for_rolebindings(self, namespace):
        ''' Gathers facts for RoleBindings used with logging '''
        self.default_keys_for("rolebindings")
        role = self.oc_command("get", "rolebindings", namespace=namespace, name="logging-elasticsearch-view-role")
        if "subjects" not in role or len(role["subjects"]) == 0:
            return
        for item in role["subjects"]:
            if namespace == item.get("namespace"):
                self.add_facts_for("rolebindings", "logging-elasticsearch-view-role", dict())

    # pylint: disable=no-self-use, too-many-return-statements
    def comp(self, name):
        ''' Does a comparison to evaluate the logging component '''
        if name.startswith(self.cluster_name):
            return "elasticsearch"
        else:
            return None

    def build_facts(self):
        ''' Builds the logging facts and returns them '''
        self.facts_for_ex_node_topology(self.namespace, "master")
        self.facts_for_ex_node_topology(self.namespace, "clientdata")
        self.facts_for_ex_node_topology(self.namespace, "masterclientdata")

        self.facts_for_services(self.namespace)
        self.facts_for_configmaps(self.namespace)
        self.facts_for_sccs()
        self.facts_for_clusterrolebindings(self.namespace)
        self.facts_for_rolebindings(self.namespace)
        self.facts_for_secrets(self.namespace)
        self.facts_for_pvcs(self.namespace)

        return self.facts


def main():
    ''' The main method '''
    module = AnsibleModule(   # noqa: F405
        argument_spec=dict(
            admin_kubeconfig={"default": "/etc/origin/master/admin.kubeconfig", "type": "str"},
            oc_bin={"required": True, "type": "str"},
            openshift_namespace={"required": True, "type": "str"},
            elasticsearch_clustername={"required": True, "type": "str"}
        ),
        supports_check_mode=False
    )
    try:
        cmd = OpenshiftLoggingFacts(module, module.params['oc_bin'],
                                    module.params['admin_kubeconfig'],
                                    module.params['openshift_namespace'],
                                    module.params['elasticsearch_clustername'])
        module.exit_json(
            ansible_facts={"openshift_logging_elasticsearch_facts": cmd.build_facts()}
        )
    # ignore broad-except error to avoid stack trace to ansible user
    # pylint: disable=broad-except
    except Exception as error:
        module.fail_json(msg=str(error))


if __name__ == '__main__':
    main()
