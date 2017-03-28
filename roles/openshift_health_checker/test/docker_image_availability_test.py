import pytest

from openshift_checks.docker_image_availability import DockerImageAvailability


@pytest.mark.xfail(strict=True)  # TODO: remove this once this test is fully implemented.
@pytest.mark.parametrize('task_vars,expected_result', [
    (
        dict(
            openshift=dict(common=dict(
                service_type='origin',
                is_containerized=False,
            )),
            openshift_release='v3.5',
            deployment_type='origin',
            openshift_image_tag='',  # FIXME: should not be required
        ),
        {'changed': False},
    ),
    # TODO: add more parameters here to test the multiple possible inputs that affect behavior.
])
def test_docker_image_availability(task_vars, expected_result):
    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        return {'info': {}}  # TODO: this will vary depending on input parameters.

    check = DockerImageAvailability(execute_module=execute_module)
    result = check.run(tmp=None, task_vars=task_vars)
    assert result == expected_result
