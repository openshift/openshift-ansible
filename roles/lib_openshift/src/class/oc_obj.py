# pylint: skip-file
# flake8: noqa

# pylint: disable=too-many-instance-attributes
class OCObject(OpenShiftCLI):
    ''' Class to wrap the oc command line tools '''

    # pylint allows 5. we need 6
    # pylint: disable=too-many-arguments
    def __init__(self,
                 kind,
                 namespace,
                 rname=None,
                 selector=None,
                 kubeconfig='/etc/origin/master/admin.kubeconfig',
                 verbose=False,
                 all_namespaces=False):
        ''' Constructor for OpenshiftOC '''
        super(OCObject, self).__init__(namespace, kubeconfig=kubeconfig, verbose=verbose,
                                       all_namespaces=all_namespaces)
        self.kind = kind
        self.name = rname
        self.selector = selector

    def get(self):
        '''return a kind by name '''
        results = self._get(self.kind, rname=self.name, selector=self.selector)
        if results['returncode'] != 0 and 'stderr' in results and \
           '\"%s\" not found' % self.name in results['stderr']:
            results['returncode'] = 0

        return results

    def delete(self):
        '''return all pods '''
        return self._delete(self.kind, self.name)

    def create(self, files=None, content=None):
        '''
           Create a config

           NOTE: This creates the first file OR the first conent.
           TODO: Handle all files and content passed in
        '''
        if files:
            return self._create(files[0])

        content['data'] = yaml.dump(content['data'])
        content_file = Utils.create_tmp_files_from_contents(content)[0]

        return self._create(content_file['path'])

    # pylint: disable=too-many-function-args
    def update(self, files=None, content=None, force=False):
        '''update a current openshift object

           This receives a list of file names or content
           and takes the first and calls replace.

           TODO: take an entire list
        '''
        if files:
            return self._replace(files[0], force)

        if content and 'data' in content:
            content = content['data']

        return self.update_content(content, force)

    def update_content(self, content, force=False):
        '''update an object through using the content param'''
        return self._replace_content(self.kind, self.name, content, force=force)

    def needs_update(self, files=None, content=None, content_type='yaml'):
        ''' check to see if we need to update '''
        objects = self.get()
        if objects['returncode'] != 0:
            return objects

        data = None
        if files:
            data = Utils.get_resource_file(files[0], content_type)
        elif content and 'data' in content:
            data = content['data']
        else:
            data = content

            # if equal then no need.  So not equal is True
        return not Utils.check_def_equal(data, objects['results'][0], skip_keys=None, debug=False)

    # pylint: disable=too-many-return-statements,too-many-branches
    @staticmethod
    def run_ansible(params, check_mode=False):
        '''perform the ansible idempotent code'''

        ocobj = OCObject(params['kind'],
                         params['namespace'],
                         params['name'],
                         params['selector'],
                         kubeconfig=params['kubeconfig'],
                         verbose=params['debug'],
                         all_namespaces=params['all_namespaces'])

        state = params['state']

        api_rval = ocobj.get()

        #####
        # Get
        #####
        if state == 'list':
            return {'changed': False, 'results': api_rval, 'state': 'list'}

        if not params['name']:
            return {'failed': True, 'msg': 'Please specify a name when state is absent|present.'}  # noqa: E501

        ########
        # Delete
        ########
        if state == 'absent':
            if not Utils.exists(api_rval['results'], params['name']):
                return {'changed': False, 'state': 'absent'}

            if check_mode:
                return {'changed': True, 'msg': 'CHECK_MODE: Would have performed a delete'}

            api_rval = ocobj.delete()

            return {'changed': True, 'results': api_rval, 'state': 'absent'}

        if state == 'present':
            ########
            # Create
            ########
            if not Utils.exists(api_rval['results'], params['name']):

                if check_mode:
                    return {'changed': True, 'msg': 'CHECK_MODE: Would have performed a create'}

                # Create it here
                api_rval = ocobj.create(params['files'], params['content'])
                if api_rval['returncode'] != 0:
                    return {'failed': True, 'msg': api_rval}

                # return the created object
                api_rval = ocobj.get()

                if api_rval['returncode'] != 0:
                    return {'failed': True, 'msg': api_rval}

                # Remove files
                if params['files'] and params['delete_after']:
                    Utils.cleanup(params['files'])

                return {'changed': True, 'results': api_rval, 'state': "present"}

            ########
            # Update
            ########
            # if a file path is passed, use it.
            update = ocobj.needs_update(params['files'], params['content'])
            if not isinstance(update, bool):
                return {'failed': True, 'msg': update}

            # No changes
            if not update:
                if params['files'] and params['delete_after']:
                    Utils.cleanup(params['files'])

                return {'changed': False, 'results': api_rval['results'][0], 'state': "present"}

            if check_mode:
                return {'changed': True, 'msg': 'CHECK_MODE: Would have performed an update.'}

            api_rval = ocobj.update(params['files'],
                                    params['content'],
                                    params['force'])


            if api_rval['returncode'] != 0:
                return {'failed': True, 'msg': api_rval}

            # return the created object
            api_rval = ocobj.get()

            if api_rval['returncode'] != 0:
                return {'failed': True, 'msg': api_rval}

            return {'changed': True, 'results': api_rval, 'state': "present"}
