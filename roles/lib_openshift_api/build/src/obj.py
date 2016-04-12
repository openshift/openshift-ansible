# pylint: skip-file

class OCObject(OpenShiftCLI):
    ''' Class to wrap the oc command line tools '''

    # pylint allows 5. we need 6
    # pylint: disable=too-many-arguments
    def __init__(self,
                 kind,
                 namespace,
                 rname=None,
                 kubeconfig='/etc/origin/master/admin.kubeconfig',
                 verbose=False):
        ''' Constructor for OpenshiftOC '''
        super(OCObject, self).__init__(namespace, kubeconfig)
        self.kind = kind
        self.namespace = namespace
        self.name = rname
        self.kubeconfig = kubeconfig
        self.verbose = verbose

    def get(self):
        '''return a deploymentconfig by name '''
        return self._get(self.kind, rname=self.name)

    def delete(self):
        '''return all pods '''
        return self._delete(self.kind, self.name)

    def create(self, files=None, content=None):
        '''Create a deploymentconfig '''
        if files:
            return self._create(files[0])

        return self._create(Utils.create_files_from_contents(content))


    # pylint: disable=too-many-function-args
    def update(self, files=None, content=None, force=False):
        '''run update dc

           This receives a list of file names and takes the first filename and calls replace.
        '''
        if files:
            return self._replace(files[0], force)

        return self.update_content(content, force)

    def update_content(self, content, force=False):
        '''update the dc with the content'''
        return self._replace_content(self.kind, self.name, content, force=force)

    def needs_update(self, files=None, content=None, content_type='yaml'):
        ''' check to see if we need to update '''
        objects = self.get()
        if objects['returncode'] != 0:
            return objects

        # pylint: disable=no-member
        data = None
        if files:
            data = Utils.get_resource_file(files[0], content_type)

            # if equal then no need.  So not equal is True
            return not Utils.check_def_equal(data, objects['results'][0], skip_keys=None, debug=False)
        else:
            data = content

            for key, value in data.items():
                if key == 'metadata':
                    continue
                if not objects['results'][0].has_key(key):
                    return True
                if value != objects['results'][0][key]:
                    return True

        return False

