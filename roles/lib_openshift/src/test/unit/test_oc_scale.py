'''
 Unit tests for oc scale
'''

import os
import six
import sys
import unittest
import mock

# Removing invalid variable names for tests so that I can
# keep them brief
# pylint: disable=invalid-name,no-name-in-module
# Disable import-error b/c our libraries aren't loaded in jenkins
# pylint: disable=import-error
# place class in our python path
module_path = os.path.join('/'.join(os.path.realpath(__file__).split('/')[:-4]), 'library')  # noqa: E501
sys.path.insert(0, module_path)
from oc_scale import OCScale, locate_oc_binary  # noqa: E402


class OCScaleTest(unittest.TestCase):
    '''
     Test class for OCVersion
    '''

    @mock.patch('oc_scale.Utils.create_tmpfile_copy')
    @mock.patch('oc_scale.OCScale.openshift_cmd')
    def test_state_list(self, mock_openshift_cmd, mock_tmpfile_copy):
        ''' Testing a get '''
        params = {'name': 'router',
                  'namespace': 'default',
                  'replicas': 2,
                  'state': 'list',
                  'kind': 'dc',
                  'kubeconfig': '/etc/origin/master/admin.kubeconfig',
                  'debug': False}

        dc = '''{"kind": "DeploymentConfig",
               "apiVersion": "v1",
               "metadata": {
                   "name": "router",
                   "namespace": "default",
                   "selfLink": "/oapi/v1/namespaces/default/deploymentconfigs/router",
                   "uid": "a441eedc-e1ae-11e6-a2d5-0e6967f34d42",
                   "resourceVersion": "6558",
                   "generation": 8,
                   "creationTimestamp": "2017-01-23T20:58:07Z",
                   "labels": {
                       "router": "router"
                   }
               },
               "spec": {
                   "replicas": 2,
               }
           }'''

        mock_openshift_cmd.side_effect = [
            {"cmd": '/usr/bin/oc get dc router -n default',
             'results': dc,
             'returncode': 0}]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        results = OCScale.run_ansible(params, False)

        assert not results['changed']
        assert results['result'][0] == 2

    @mock.patch('oc_scale.Utils.create_tmpfile_copy')
    @mock.patch('oc_scale.OCScale.openshift_cmd')
    def test_scale(self, mock_openshift_cmd, mock_tmpfile_copy):
        ''' Testing a get '''
        params = {'name': 'router',
                  'namespace': 'default',
                  'replicas': 3,
                  'state': 'list',
                  'kind': 'dc',
                  'kubeconfig': '/etc/origin/master/admin.kubeconfig',
                  'debug': False}

        dc = '''{"kind": "DeploymentConfig",
               "apiVersion": "v1",
               "metadata": {
                   "name": "router",
                   "namespace": "default",
                   "selfLink": "/oapi/v1/namespaces/default/deploymentconfigs/router",
                   "uid": "a441eedc-e1ae-11e6-a2d5-0e6967f34d42",
                   "resourceVersion": "6558",
                   "generation": 8,
                   "creationTimestamp": "2017-01-23T20:58:07Z",
                   "labels": {
                       "router": "router"
                   }
               },
               "spec": {
                   "replicas": 3,
               }
           }'''

        mock_openshift_cmd.side_effect = [
            {"cmd": '/usr/bin/oc get dc router -n default',
             'results': dc,
             'returncode': 0},
            {"cmd": '/usr/bin/oc create -f /tmp/router -n default',
             'results': '',
             'returncode': 0}
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        results = OCScale.run_ansible(params, False)

        assert not results['changed']
        assert results['result'][0] == 3

    @mock.patch('oc_scale.Utils.create_tmpfile_copy')
    @mock.patch('oc_scale.OCScale.openshift_cmd')
    def test_no_dc_scale(self, mock_openshift_cmd, mock_tmpfile_copy):
        ''' Testing a get '''
        params = {'name': 'not_there',
                  'namespace': 'default',
                  'replicas': 3,
                  'state': 'present',
                  'kind': 'dc',
                  'kubeconfig': '/etc/origin/master/admin.kubeconfig',
                  'debug': False}

        mock_openshift_cmd.side_effect = [
            {"cmd": '/usr/bin/oc -n default get dc not_there -o json',
             'results': [{}],
             'returncode': 1,
             'stderr': "Error from server: deploymentconfigs \"not_there\" not found\n",
             'stdout': ""},
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        results = OCScale.run_ansible(params, False)

        assert results['failed']
        assert results['msg']['returncode'] == 1

    @unittest.skipIf(six.PY3, 'py2 test only')
    @mock.patch('os.path.exists')
    @mock.patch('os.environ.get')
    def test_binary_lookup_fallback(self, mock_env_get, mock_path_exists):
        ''' Testing binary lookup fallback '''

        mock_env_get.side_effect = lambda _v, _d: ''

        mock_path_exists.side_effect = lambda _: False

        assert locate_oc_binary() == 'oc'

    @unittest.skipIf(six.PY3, 'py2 test only')
    @mock.patch('os.path.exists')
    @mock.patch('os.environ.get')
    def test_binary_lookup_in_path(self, mock_env_get, mock_path_exists):
        ''' Testing binary lookup in path '''

        oc_bin = '/usr/bin/oc'

        mock_env_get.side_effect = lambda _v, _d: '/bin:/usr/bin'

        mock_path_exists.side_effect = lambda f: f == oc_bin

        assert locate_oc_binary() == oc_bin

    @unittest.skipIf(six.PY3, 'py2 test only')
    @mock.patch('os.path.exists')
    @mock.patch('os.environ.get')
    def test_binary_lookup_in_usr_local(self, mock_env_get, mock_path_exists):
        ''' Testing binary lookup in /usr/local/bin '''

        oc_bin = '/usr/local/bin/oc'

        mock_env_get.side_effect = lambda _v, _d: '/bin:/usr/bin'

        mock_path_exists.side_effect = lambda f: f == oc_bin

        assert locate_oc_binary() == oc_bin

    @unittest.skipIf(six.PY3, 'py2 test only')
    @mock.patch('os.path.exists')
    @mock.patch('os.environ.get')
    def test_binary_lookup_in_home(self, mock_env_get, mock_path_exists):
        ''' Testing binary lookup in ~/bin '''

        oc_bin = os.path.expanduser('~/bin/oc')

        mock_env_get.side_effect = lambda _v, _d: '/bin:/usr/bin'

        mock_path_exists.side_effect = lambda f: f == oc_bin

        assert locate_oc_binary() == oc_bin

    @unittest.skipIf(six.PY2, 'py3 test only')
    @mock.patch('shutil.which')
    @mock.patch('os.environ.get')
    def test_binary_lookup_fallback_py3(self, mock_env_get, mock_shutil_which):
        ''' Testing binary lookup fallback '''

        mock_env_get.side_effect = lambda _v, _d: ''

        mock_shutil_which.side_effect = lambda _f, path=None: None

        assert locate_oc_binary() == 'oc'

    @unittest.skipIf(six.PY2, 'py3 test only')
    @mock.patch('shutil.which')
    @mock.patch('os.environ.get')
    def test_binary_lookup_in_path_py3(self, mock_env_get, mock_shutil_which):
        ''' Testing binary lookup in path '''

        oc_bin = '/usr/bin/oc'

        mock_env_get.side_effect = lambda _v, _d: '/bin:/usr/bin'

        mock_shutil_which.side_effect = lambda _f, path=None: oc_bin

        assert locate_oc_binary() == oc_bin

    @unittest.skipIf(six.PY2, 'py3 test only')
    @mock.patch('shutil.which')
    @mock.patch('os.environ.get')
    def test_binary_lookup_in_usr_local_py3(self, mock_env_get, mock_shutil_which):
        ''' Testing binary lookup in /usr/local/bin '''

        oc_bin = '/usr/local/bin/oc'

        mock_env_get.side_effect = lambda _v, _d: '/bin:/usr/bin'

        mock_shutil_which.side_effect = lambda _f, path=None: oc_bin

        assert locate_oc_binary() == oc_bin

    @unittest.skipIf(six.PY2, 'py3 test only')
    @mock.patch('shutil.which')
    @mock.patch('os.environ.get')
    def test_binary_lookup_in_home_py3(self, mock_env_get, mock_shutil_which):
        ''' Testing binary lookup in ~/bin '''

        oc_bin = os.path.expanduser('~/bin/oc')

        mock_env_get.side_effect = lambda _v, _d: '/bin:/usr/bin'

        mock_shutil_which.side_effect = lambda _f, path=None: oc_bin

        assert locate_oc_binary() == oc_bin
