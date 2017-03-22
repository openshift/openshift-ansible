import pytest
import json

try:
    import urllib2
    from urllib2 import HTTPError, URLError
except ImportError:
    from urllib.error import HTTPError, URLError
    import urllib.request as urllib2

from openshift_checks.logging.kibana import Kibana


def canned_kibana(exec_oc=None):
    """Create a Kibana check object with canned exec_oc method"""
    check = Kibana("dummy")  # fails if a module is actually invoked
    if exec_oc:
        check._exec_oc = exec_oc
    return check


def assert_error(error, expect_error):
    if expect_error:
        assert error
        assert expect_error in error
    else:
        assert not error


plain_kibana_pod = {
    "metadata": {
        "labels": {"component": "kibana", "deploymentconfig": "logging-kibana"},
        "name": "logging-kibana-1",
    },
    "status": {
        "containerStatuses": [{"ready": True}, {"ready": True}],
        "conditions": [{"status": "True", "type": "Ready"}],
    }
}
not_running_kibana_pod = {
    "metadata": {
        "labels": {"component": "kibana", "deploymentconfig": "logging-kibana"},
        "name": "logging-kibana-2",
    },
    "status": {
        "containerStatuses": [{"ready": True}, {"ready": False}],
        "conditions": [{"status": "True", "type": "Ready"}],
    }
}


@pytest.mark.parametrize('pods, expect_error', [
    (
        [],
        "There are no Kibana pods deployed",
    ),
    (
        [plain_kibana_pod],
        None,
    ),
    (
        [not_running_kibana_pod],
        "No Kibana pod is in a running state",
    ),
    (
        [plain_kibana_pod, not_running_kibana_pod],
        "The following Kibana pods are not currently in a running state",
    ),
])
def test_check_kibana(pods, expect_error):
    check = canned_kibana()
    error = check.check_kibana(pods)
    assert_error(error, expect_error)


@pytest.mark.parametrize('route, expect_url, expect_error', [
    (
        None,
        None,
        'no_route_exists',
    ),

    # test route with no ingress
    (
        {
            "metadata": {
                "labels": {"component": "kibana", "deploymentconfig": "logging-kibana"},
                "name": "logging-kibana",
            },
            "status": {
                "ingress": [],
            },
            "spec": {
                "host": "hostname",
            }
        },
        None,
        'route_not_accepted',
    ),

    # test route with no host
    (
        {
            "metadata": {
                "labels": {"component": "kibana", "deploymentconfig": "logging-kibana"},
                "name": "logging-kibana",
            },
            "status": {
                "ingress": [{
                    "status": True,
                }],
            },
            "spec": {},
        },
        None,
        'route_missing_host',
    ),

    # test route that looks fine
    (
        {
            "metadata": {
                "labels": {"component": "kibana", "deploymentconfig": "logging-kibana"},
                "name": "logging-kibana",
            },
            "status": {
                "ingress": [{
                    "status": True,
                }],
            },
            "spec": {
                "host": "hostname",
            },
        },
        "https://hostname/",
        None,
    ),
])
def test_get_kibana_url(route, expect_url, expect_error):
    check = canned_kibana(lambda cmd, args, task_vars: json.dumps(route) if route else "")

    url, error = check._get_kibana_url({})
    if expect_url:
        assert url == expect_url
    else:
        assert not url
    if expect_error:
        assert error == expect_error
    else:
        assert not error


@pytest.mark.parametrize('exec_result, expect', [
    (
        'urlopen error [Errno 111] Connection refused',
        'at least one router routing to it?',
    ),
    (
        'urlopen error [Errno -2] Name or service not known',
        'DNS configured for the Kibana hostname?',
    ),
    (
        'Status code was not [302]: HTTP Error 500: Server error',
        'did not return the correct status code',
    ),
    (
        'bork bork bork',
        'bork bork bork',  # should pass through
    ),
])
def test_verify_url_internal_failure(exec_result, expect):
    check = Kibana(execute_module=lambda module_name, args, task_vars: dict(failed=True, msg=exec_result))
    check._get_kibana_url = lambda task_vars: ('url', None)

    error = check._check_kibana_route({})
    assert_error(error, expect)


@pytest.mark.parametrize('lib_result, expect', [
    (
        HTTPError('url', 500, "it broke", hdrs=None, fp=None),
        'it broke',
    ),
    (
        URLError('it broke'),
        'it broke',
    ),
    (
        302,
        'returned the wrong error code',
    ),
    (
        200,
        None,
    ),
])
def test_verify_url_external_failure(lib_result, expect, monkeypatch):

    class _http_return:

        def __init__(self, code):
            self.code = code

        def getcode(self):
            return self.code

    def urlopen(url, context):
        if type(lib_result) is int:
            return _http_return(lib_result)
        raise lib_result
    monkeypatch.setattr(urllib2, 'urlopen', urlopen)

    check = canned_kibana()
    check._get_kibana_url = lambda task_vars: ('url', None)
    check._verify_url_internal = lambda url, task_vars: None

    error = check._check_kibana_route({})
    assert_error(error, expect)
