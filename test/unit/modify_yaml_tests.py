""" Tests for the modify_yaml Ansible module. """
# pylint: disable=missing-docstring,invalid-name

import os
import sys

sys.path = [os.path.abspath(os.path.dirname(__file__) + "/../../library/")] + sys.path

# pylint: disable=import-error
from modify_yaml import set_key  # noqa: E402


def test_simple_nested_value():
    cfg = {"section": {"a": 1, "b": 2}}
    changes = set_key(cfg, 'section.c', 3)
    assert len(changes) == 1
    assert cfg['section']['c'] == 3


# Tests a previous bug where property would land in section above where it should,
# if the destination section did not yet exist:
def test_nested_property_in_new_section():
    cfg = {
        "masterClients": {
            "externalKubernetesKubeConfig": "",
            "openshiftLoopbackKubeConfig": "openshift-master.kubeconfig",
        },
    }
    yaml_key = 'masterClients.externalKubernetesClientConnectionOverrides.acceptContentTypes'
    yaml_value = 'application/vnd.kubernetes.protobuf,application/json'
    set_key(cfg, yaml_key, yaml_value)
    assert cfg['masterClients']['externalKubernetesClientConnectionOverrides']['acceptContentTypes'] == yaml_value
