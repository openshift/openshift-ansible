# pylint: skip-file
# flake8: noqa

# pylint: disable=too-many-instance-attributes
class OCSDNValidator(OpenShiftCLI):
    ''' Class to wrap the oc command line tools '''

    def __init__(self, kubeconfig):
        ''' Constructor for OCSDNValidator '''
        # namespace has no meaning for SDN validation, hardcode to 'default'
        super(OCSDNValidator, self).__init__('default', kubeconfig)

    def get(self, kind, invalid_filter):
        ''' return SDN information '''

        rval = self._get(kind)
        if rval['returncode'] != 0:
            return False, rval, []

        return True, rval, filter(invalid_filter, rval['results'][0]['items'])

    # pylint: disable=too-many-return-statements
    @staticmethod
    def run_ansible(params):
        ''' run the idempotent ansible code

            params comes from the ansible portion of this module
        '''

        sdnvalidator = OCSDNValidator(params['kubeconfig'])
        all_invalid = {}
        failed = False

        checks = (
            (
                'hostsubnet',
                lambda x: x['metadata']['name'] != x['host'],
                u'hostsubnets where metadata.name != host',
            ),
            (
                'netnamespace',
                lambda x: x['metadata']['name'] != x['netname'],
                u'netnamespaces where metadata.name != netname',
            ),
        )

        for resource, invalid_filter, invalid_msg in checks:
            success, rval, invalid = sdnvalidator.get(resource, invalid_filter)
            if not success:
                return {'failed': True, 'msg': 'Failed to GET {}.'.format(resource), 'state': 'list', 'results': rval}
            if invalid:
                failed = True
                all_invalid[invalid_msg] = invalid

        if failed:
            return {'failed': True, 'msg': 'All SDN objects are not valid.', 'state': 'list', 'results': all_invalid}

        return {'msg': 'All SDN objects are valid.'}
