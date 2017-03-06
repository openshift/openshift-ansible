'''
 Unit tests for oc version
'''
from lib_openshift.library import oc_version

MODULE_UNDER_TEST = oc_version
CLASS_UNDER_TEST = oc_version.OCVersion


def test_get(mock_run_cmd):
    ''' Testing a get '''
    params = {'kubeconfig': '/etc/origin/master/admin.kubeconfig',
              'state': 'list',
              'debug': False}

    mock_run_cmd.side_effect = [
        (0, ("oc v3.4.0.39\nkubernetes v1.4.0+776c994\n"
             "features: Basic-Auth GSSAPI Kerberos SPNEGO\n\n"
             "Server https://internal.api.opstest.openshift.com"
             "openshift v3.4.0.39\n"
             "kubernetes v1.4.0+776c994\n"),
         '')
    ]

    results = CLASS_UNDER_TEST.run_ansible(params)

    results['changed'] is False
    assert results['results']['oc_short'] == '3.4'
    assert results['results']['oc_numeric'] == '3.4.0.39'
    assert results['results']['kubernetes_numeric'] == '1.4.0'
