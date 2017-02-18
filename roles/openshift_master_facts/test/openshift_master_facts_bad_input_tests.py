import copy
import os
import sys

from ansible.errors import AnsibleError
from nose.tools import raises

sys.path.insert(1, os.path.join(os.path.dirname(__file__), os.pardir, "lookup_plugins"))

from openshift_master_facts_default_predicates import LookupModule  # noqa: E402


class TestOpenShiftMasterFactsBadInput(object):
    def setUp(self):
        self.lookup = LookupModule()
        self.default_facts = {
            'openshift': {
                'common': {}
            }
        }

    @raises(AnsibleError)
    def test_missing_openshift_facts(self):
        facts = {}
        self.lookup.run(None, variables=facts)

    @raises(AnsibleError)
    def test_missing_deployment_type(self):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['short_version'] = '10.10'
        self.lookup.run(None, variables=facts)

    @raises(AnsibleError)
    def test_missing_short_version_and_missing_openshift_release(self):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['deployment_type'] = 'origin'
        self.lookup.run(None, variables=facts)

    @raises(AnsibleError)
    def test_unknown_deployment_types(self):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['short_version'] = '1.1'
        facts['openshift']['common']['deployment_type'] = 'bogus'
        self.lookup.run(None, variables=facts)

    @raises(AnsibleError)
    def test_unknown_origin_version(self):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['short_version'] = '0.1'
        facts['openshift']['common']['deployment_type'] = 'origin'
        self.lookup.run(None, variables=facts)

    @raises(AnsibleError)
    def test_unknown_ocp_version(self):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['short_version'] = '0.1'
        facts['openshift']['common']['deployment_type'] = 'openshift-enterprise'
        self.lookup.run(None, variables=facts)
