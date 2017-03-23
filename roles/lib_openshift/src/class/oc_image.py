# pylint: skip-file

# pylint: disable=too-many-arguments
class OCImage(OpenShiftCLI):
    ''' Class to wrap the oc command line tools
    '''
    def __init__(self,
                 namespace,
                 registry_url,
                 image_name,
                 image_tag,
                 kubeconfig='/etc/origin/master/admin.kubeconfig',
                 verbose=False):
        ''' Constructor for OpenshiftOC '''
        super(OCImage, self).__init__(namespace, kubeconfig)
        self.namespace = namespace
        self.registry_url = registry_url
        self.image_name = image_name
        self.image_tag = image_tag
        self.kubeconfig = kubeconfig
        self.verbose = verbose

    def get(self):
        '''return a image by name '''
        results = self._get('imagestream', self.image_name)
        results['exists'] = False
        if results['returncode'] == 0 and results['results'][0]:
            results['exists'] = True

        if results['returncode'] != 0 and '"%s" not found' % self.image_name in results['stderr']:
            results['returncode'] = 0

        return results

    def create(self, url=None, name=None, tag=None):
        '''Create an image '''

        return self._import_image(url, name, tag)


    @staticmethod
    def run_ansible(params, check_mode):
        ''' run the ansible idempotent code '''
    
        ocimage = OCImage(params['namespace'],
                          params['registry_url'],
                          params['image_name'],
                          params['image_tag'],
                          kubeconfig=params['kubeconfig'],
                          verbose=params['debug'])

        state = params['state']

        api_rval = ocimage.get()

        #####
        # Get
        #####
        if state == 'list':
            if api_rval['returncode'] != 0:
                return {"failed": True, "msg": api_rval}
            return {"changed": False, "results": api_rval, "state": "list"}

        if not params['image_name']:
            return {"failed": True, "msg": 'Please specify a name when state is absent|present.'}

        if state == 'present':

            ########
            # Create
            ########
            if not Utils.exists(api_rval['results'], params['image_name']):

                if check_mode:
                    return {"changed": False, "msg": 'CHECK_MODE: Would have performed a create'}

                api_rval = ocimage.create(params['registry_url'],
                                          params['image_name'],
                                          params['image_tag'])

                if api_rval['returncode'] != 0:
                    return {"failed": True, "msg": api_rval}

                return {"changed": True, "results": api_rval, "state": "present"}


            # image exists, no change
            return {"changed": False, "results": api_rval, "state": "present"}

        return {"failed": True, "changed": False, "results": "Unknown state passed. {0}".format(state), "state": "unknown"}
