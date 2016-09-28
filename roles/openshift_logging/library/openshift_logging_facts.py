
DOCUMENTATION = """
---
module: openshift_logging_facts
version_added: ""
short_description: Gather facts about the OpenShift logging stack
description:
  - Determine the current facts about the OpenShift logging stack (e.g. cluster size)
options:
author: Red Hat, Inc
"""

EXAMPLES = """
- action: opneshift_logging_facts
"""

RETURN = """
"""

import copy
import json
import exceptions
import yaml
from subprocess import *

default_oc_options = ["-o","json"]

#constants used for various labels and selectors
COMPONENT_KEY="component"
LOGGING_INFRA_KEY="logging-infra"

#selectors for filtering resources
DS_FLUENTD_SELECTOR=LOGGING_INFRA_KEY + "=" + "fluentd"
LOGGING_SELECTOR=LOGGING_INFRA_KEY + "=" + "support"
ROUTE_SELECTOR = "component=support,logging-infra=support,provider=openshift"
COMPONENTS = ["kibana","curator","elasticsearch","fluentd", "kibana_ops", "curator_ops", "elasticsearch_ops"]

class OCBaseCommand(object):
    def __init__(self, binary, kubeconfig, namespace):
        self.binary = binary
        self.kubeconfig = kubeconfig
        self.user = self.getSystemAdmin(self.kubeconfig)
        self.namespace = namespace

    def getSystemAdmin(self,kubeconfig):
        with open(kubeconfig,'r') as f:
            config = yaml.load(f)
            for user in config["users"]:
                if user["name"].startswith("system:admin"):
                    return user["name"]
        raise Exception("Unable to find system:admin in: " + kubeconfig)

    def oc(self, sub, kind, namespace=None, name=None,addOptions=[]):
        cmd = [self.binary, sub, kind]
        if name != None:
            cmd = cmd + [name]
        if namespace != None:
            cmd = cmd + ["-n", namespace]
        cmd = cmd + ["--user="+self.user,"--config="+self.kubeconfig] + default_oc_options + addOptions
        try:
            process = Popen(cmd, stdout=PIPE, stderr=PIPE)
            out, err = process.communicate(cmd)
            if len(err) > 0:
                if 'not found' in err:
                    return {'items':[]}
                if 'No resources found' in err:
                    return {'items':[]}
                raise Exception(err)
        except Exception as e:
            err = "There was an exception trying to run the command '"+ " ".join(cmd) +"' " + str(e)
            raise Exception(err)

        return json.loads(out)

class OpenshiftLoggingFacts(OCBaseCommand):

    name = "facts"

    def __init__(self, logger, binary, kubeconfig, namespace):
        super(OpenshiftLoggingFacts, self).__init__(binary, kubeconfig, namespace)
        self.logger = logger
        self.facts = dict()

    def defaultKeysFor(self, kind):
        for comp in COMPONENTS:
            self.addFactsFor(comp, kind)

    def addFactsFor(self, comp, kind, name=None, facts=None):
        if self.facts.has_key(comp) == False:
            self.facts[comp] = dict()
        if self.facts[comp].has_key(kind) == False:
            self.facts[comp][kind] = dict()
        if name:
           self.facts[comp][kind][name] = facts

    def factsForRoutes(self, namespace):
        self.defaultKeysFor("routes")
        routeList =  self.oc("get","routes", namespace=namespace, addOptions=["-l",ROUTE_SELECTOR])
        if len(routeList["items"]) == 0:
            return None
        for route in routeList["items"]:
            name = route["metadata"]["name"]
            comp = self.comp(name)
            if comp != None:
                self.addFactsFor(comp, "routes", name, dict(host=route["spec"]["host"]))
        self.facts["agl_namespace"] = namespace


    def factsForDaemonsets(self, namespace):
        self.defaultKeysFor("daemonsets")
        dsList = self.oc("get", "daemonsets", namespace=namespace, addOptions=["-l",LOGGING_INFRA_KEY+"=fluentd"])
        if len(dsList["items"]) == 0:
            return
        for ds in dsList["items"]:
            name = ds["metadata"]["name"]
            comp = self.comp(name)
            spec = ds["spec"]["template"]["spec"]
            container = spec["containers"][0]
            result = dict(
                selector = ds["spec"]["selector"],
                image = container["image"],
                resources = container["resources"],
                nodeSelector = spec["nodeSelector"],
                serviceAccount = spec["serviceAccount"],
                terminationGracePeriodSeconds = spec["terminationGracePeriodSeconds"]
            )
            self.addFactsFor(comp, "daemonsets", name, result)

    def factsForPvcs(self, namespace):
        self.defaultKeysFor("pvcs")
        pvclist = self.oc("get", "pvc", namespace=namespace, addOptions=["-l",LOGGING_INFRA_KEY])
        if len(pvclist["items"]) == 0:
            return
        pvcs = []
        for pvc in pvclist["items"]:
            name = pvc["metadata"]["name"]
            comp = self.comp(name)
            self.addFactsFor(comp,"pvcs",name,dict())

    def factsForDeploymentConfigs(self, namespace):
        self.defaultKeysFor("deploymentconfigs")
        dclist = self.oc("get", "deploymentconfigs", namespace=namespace, addOptions=["-l",LOGGING_INFRA_KEY])
        if len(dclist["items"]) == 0:
            return
        dcs = dclist["items"]
        for dc in dcs:
            name = dc["metadata"]["name"]
            comp = self.comp(name)
            if comp != None:
                spec = dc["spec"]["template"]["spec"]
                facts = dict(
                    selector = dc["spec"]["selector"],
                    replicas = dc["spec"]["replicas"],
                    serviceAccount = spec["serviceAccount"],
                    containers = dict(),
                    volumes = dict()
                )
                if spec.has_key("volumes"):
                    for vol in spec["volumes"]:
                        clone = copy.deepcopy(vol)
                        clone.pop("name", None)
                        facts["volumes"][vol["name"]] = clone
                for container in spec["containers"]:
                    facts["containers"][container["name"]] = dict(
                        image = container["image"],
                        resources = container["resources"],
                    )
                self.addFactsFor(comp,"deploymentconfigs",name,facts)

    def factsForServices(self, namespace):
        self.defaultKeysFor("services")
        servicelist = self.oc("get", "services", namespace=namespace, addOptions=["-l",LOGGING_SELECTOR])
        if len(servicelist["items"]) == 0:
            return
        for service in servicelist["items"]:
            name = service["metadata"]["name"]
            comp = self.comp(name)
            if comp != None:
                self.addFactsFor(comp, "services", name, dict())

    def factsForConfigMaps(self, namespace):
        self.defaultKeysFor("configmaps")
        aList = self.oc("get", "configmaps", namespace=namespace, addOptions=["-l",LOGGING_SELECTOR])
        if len(aList["items"]) == 0:
            return
        for item in aList["items"]:
            name = item["metadata"]["name"]
            comp = self.comp(name)
            if comp != None:
                self.addFactsFor(comp, "configmaps", name, item["data"])

    def factsForOAuthClients(self, namespace):
        self.defaultKeysFor("oauthclients")
        aList = self.oc("get", "oauthclients", namespace=namespace, addOptions=["-l",LOGGING_SELECTOR])
        if len(aList["items"]) == 0:
            return
        for item in aList["items"]:
            name = item["metadata"]["name"]
            comp = self.comp(name)
            if comp != None:
                result = dict(
                    redirectURIs = item["redirectURIs"]
                )
                self.addFactsFor(comp, "oauthclients", name, result)

    def factsForSecrets(self, namespace):
        self.defaultKeysFor("secrets")
        aList = self.oc("get", "secrets", namespace=namespace)
        if len(aList["items"]) == 0:
            return
        for item in aList["items"]:
            name = item["metadata"]["name"]
            comp = self.comp(name)
            if comp != None and item["type"] == "Opaque":
                result = dict(
                    keys = item["data"].keys()
                )
                self.addFactsFor(comp, "secrets", name, result)

    def factsForSCCs(self, namespace):
        self.defaultKeysFor("sccs")
        scc = self.oc("get", "scc", name="privileged")
        if len(scc["users"]) == 0:
            return
        for item in scc["users"]:
            comp = self.comp(item)
            if comp != None:
                self.addFactsFor(comp, "sccs", "privileged", dict())

    def factsForClusterRoleBindings(self, namespace):
        self.defaultKeysFor("clusterrolebindings")
        role = self.oc("get", "clusterrolebindings", name="cluster-readers")
        if "subjects" not in role or  len(role["subjects"]) == 0:
            return
        for item in role["subjects"]:
            comp = self.comp(item["name"])
            if comp != None and namespace == item["namespace"]:
                self.addFactsFor(comp, "clusterrolebindings", "cluster-readers", dict())

# this needs to end up nested under the service account...
    def factsForRoleBindings(self, namespace):
        self.defaultKeysFor("rolebindings")
        role = self.oc("get", "rolebindings", namespace=namespace, name="logging-elasticsearch-view-role")
        if "subjects" not in role or len(role["subjects"]) == 0:
            return
        for item in role["subjects"]:
            comp = self.comp(item["name"])
            if comp != None and namespace == item["namespace"]:
                self.addFactsFor(comp, "rolebindings", "logging-elasticsearch-view-role", dict())

    def comp(self, name):
        if name.startswith("logging-curator-ops"):
            return "curator_ops"
        elif name.startswith("logging-kibana-ops") or name.startswith("kibana-ops"):
            return "kibana_ops"
        elif name.startswith("logging-es-ops") or name.startswith("logging-elasticsearch-ops"):
            return "elasticsearch_ops"
        elif name.startswith("logging-curator"):
            return "curator"
        elif name.startswith("logging-kibana") or name.startswith("kibana"):
            return "kibana"
        elif name.startswith("logging-es") or name.startswith("logging-elasticsearch"):
            return "elasticsearch"
        elif name.startswith("logging-fluentd") or name.endswith("aggregated-logging-fluentd"):
            return "fluentd"
        else:
            return None

    def do(self):
        self.factsForRoutes(self.namespace)
        self.factsForDaemonsets(self.namespace)
        self.factsForDeploymentConfigs(self.namespace)
        self.factsForServices(self.namespace)
        self.factsForConfigMaps(self.namespace)
        self.factsForSCCs(self.namespace)
        self.factsForOAuthClients(self.namespace)
        self.factsForClusterRoleBindings(self.namespace)
        self.factsForRoleBindings(self.namespace)
        self.factsForSecrets(self.namespace)
        self.factsForPvcs(self.namespace)

        return self.facts

def main():
    module = AnsibleModule(
        argument_spec=dict(
            admin_kubeconfig = {"required": True, "type": "str"},
            oc_bin = {"required": True, "type": "str"},
            openshift_logging_namespace = {"required": True, "type": "str"}
        ),
        supports_check_mode = False
    )
    try:
        cmd = OpenshiftLoggingFacts(module, module.params['oc_bin'], module.params['admin_kubeconfig'],module.params['openshift_logging_namespace'])
        module.exit_json(
                ansible_facts = {"openshift_logging_facts": cmd.do() }
        )
    except Exception as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
