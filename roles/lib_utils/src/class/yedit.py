# flake8: noqa
# pylint: skip-file


class YeditException(Exception):
    ''' Exception class for Yedit '''
    pass


# pylint: disable=too-many-public-methods,too-many-instance-attributes
class Yedit(object):
    ''' Class to modify yaml files '''
    re_valid_key = r"(((\[-?\d+\])|([0-9a-zA-Z%s/_-]+)).?)+$"
    re_key = r"(?:\[(-?\d+)\])|([0-9a-zA-Z{}/_-]+)"
    com_sep = set(['.', '#', '|', ':'])

    # pylint: disable=too-many-arguments
    def __init__(self,
                 filename=None,
                 content=None,
                 content_type='yaml',
                 separator='.',
                 backup_ext=None,
                 backup=False):
        self.content = content
        self._separator = separator
        self.filename = filename
        self.__yaml_dict = content
        self.content_type = content_type
        self.backup = backup
        if backup_ext is None:
            self.backup_ext = ".{}".format(time.strftime("%Y%m%dT%H%M%S"))
        else:
            self.backup_ext = backup_ext

        self.load(content_type=self.content_type)
        if self.__yaml_dict is None:
            self.__yaml_dict = {}

    @property
    def separator(self):
        ''' getter method for separator '''
        return self._separator

    @separator.setter
    def separator(self, inc_sep):
        ''' setter method for separator '''
        self._separator = inc_sep

    @property
    def yaml_dict(self):
        ''' getter method for yaml_dict '''
        return self.__yaml_dict

    @yaml_dict.setter
    def yaml_dict(self, value):
        ''' setter method for yaml_dict '''
        self.__yaml_dict = value

    @staticmethod
    def parse_key(key, sep='.'):
        '''parse the key allowing the appropriate separator'''
        common_separators = list(Yedit.com_sep - set([sep]))
        return re.findall(Yedit.re_key.format(''.join(common_separators)), key)

    @staticmethod
    def valid_key(key, sep='.'):
        '''validate the incoming key'''
        common_separators = list(Yedit.com_sep - set([sep]))
        if not re.match(Yedit.re_valid_key.format(''.join(common_separators)), key):
            return False

        return True

    # pylint: disable=too-many-return-statements,too-many-branches
    @staticmethod
    def remove_entry(data, key, index=None, value=None, sep='.'):
        ''' remove data at location key '''
        if key == '' and isinstance(data, dict):
            if value is not None:
                data.pop(value)
            elif index is not None:
                raise YeditException("remove_entry for a dictionary does not have an index {}".format(index))
            else:
                data.clear()

            return True

        elif key == '' and isinstance(data, list):
            ind = None
            if value is not None:
                try:
                    ind = data.index(value)
                except ValueError:
                    return False
            elif index is not None:
                ind = index
            else:
                del data[:]

            if ind is not None:
                data.pop(ind)

            return True

        if not (key and Yedit.valid_key(key, sep)) and \
           isinstance(data, (list, dict)):
            return None

        key_indexes = Yedit.parse_key(key, sep)
        for arr_ind, dict_key in key_indexes[:-1]:
            if dict_key and isinstance(data, dict):
                data = data.get(dict_key)
            elif (arr_ind and isinstance(data, list) and
                  int(arr_ind) <= len(data) - 1):
                data = data[int(arr_ind)]
            else:
                return None

        # process last index for remove
        # expected list entry
        if key_indexes[-1][0]:
            if isinstance(data, list) and int(key_indexes[-1][0]) <= len(data) - 1:  # noqa: E501
                del data[int(key_indexes[-1][0])]
                return True

        # expected dict entry
        elif key_indexes[-1][1]:
            if isinstance(data, dict):
                del data[key_indexes[-1][1]]
                return True

    @staticmethod
    def add_entry(data, key, item=None, sep='.'):
        ''' Get an item from a dictionary with key notation a.b.c
            d = {'a': {'b': 'c'}}}
            key = a#b
            return c
        '''
        if key == '':
            pass
        elif (not (key and Yedit.valid_key(key, sep)) and
              isinstance(data, (list, dict))):
            return None

        key_indexes = Yedit.parse_key(key, sep)
        for arr_ind, dict_key in key_indexes[:-1]:
            if dict_key:
                if isinstance(data, dict) and dict_key in data and data[dict_key]:  # noqa: E501
                    data = data[dict_key]
                    continue

                elif data and not isinstance(data, dict):
                    raise YeditException("Unexpected item type found while going through key " +
                                         "path: {} (at key: {})".format(key, dict_key))

                data[dict_key] = {}
                data = data[dict_key]

            elif (arr_ind and isinstance(data, list) and
                  int(arr_ind) <= len(data) - 1):
                data = data[int(arr_ind)]
            else:
                raise YeditException("Unexpected item type found while going through key path: {}".format(key))

        if key == '':
            data = item

        # process last index for add
        # expected list entry
        elif key_indexes[-1][0] and isinstance(data, list) and int(key_indexes[-1][0]) <= len(data) - 1:  # noqa: E501
            data[int(key_indexes[-1][0])] = item

        # expected dict entry
        elif key_indexes[-1][1] and isinstance(data, dict):
            data[key_indexes[-1][1]] = item

        # didn't add/update to an existing list, nor add/update key to a dict
        # so we must have been provided some syntax like a.b.c[<int>] = "data" for a
        # non-existent array
        else:
            raise YeditException("Error adding to object at path: {}".format(key))

        return data

    @staticmethod
    def get_entry(data, key, sep='.'):
        ''' Get an item from a dictionary with key notation a.b.c
            d = {'a': {'b': 'c'}}}
            key = a.b
            return c
        '''
        if key == '':
            pass
        elif (not (key and Yedit.valid_key(key, sep)) and
              isinstance(data, (list, dict))):
            return None

        key_indexes = Yedit.parse_key(key, sep)
        for arr_ind, dict_key in key_indexes:
            if dict_key and isinstance(data, dict):
                data = data.get(dict_key)
            elif (arr_ind and isinstance(data, list) and
                  int(arr_ind) <= len(data) - 1):
                data = data[int(arr_ind)]
            else:
                return None

        return data

    @staticmethod
    def _write(filename, contents):
        ''' Actually write the file contents to disk. This helps with mocking. '''

        tmp_filename = filename + '.yedit'

        with open(tmp_filename, 'w') as yfd:
            fcntl.flock(yfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yfd.write(contents)
            fcntl.flock(yfd, fcntl.LOCK_UN)

        os.rename(tmp_filename, filename)

    def write(self):
        ''' write to file '''
        if not self.filename:
            raise YeditException('Please specify a filename.')

        if self.backup and self.file_exists():
            shutil.copy(self.filename, '{}{}'.format(self.filename, self.backup_ext))

        # Try to set format attributes if supported
        try:
            self.yaml_dict.fa.set_block_style()
        except AttributeError:
            pass

        # Try to use RoundTripDumper if supported.
        if self.content_type == 'yaml':
            try:
                Yedit._write(self.filename, yaml.dump(self.yaml_dict, Dumper=yaml.RoundTripDumper))
            except AttributeError:
                Yedit._write(self.filename, yaml.safe_dump(self.yaml_dict, default_flow_style=False))
        elif self.content_type == 'json':
            Yedit._write(self.filename, json.dumps(self.yaml_dict, indent=4, sort_keys=True))
        else:
            raise YeditException('Unsupported content_type: {}.'.format(self.content_type) +
                                 'Please specify a content_type of yaml or json.')

        return (True, self.yaml_dict)

    def read(self):
        ''' read from file '''
        # check if it exists
        if self.filename is None or not self.file_exists():
            return None

        contents = None
        with open(self.filename) as yfd:
            contents = yfd.read()

        return contents

    def file_exists(self):
        ''' return whether file exists '''
        if os.path.exists(self.filename):
            return True

        return False

    def load(self, content_type='yaml'):
        ''' return yaml file '''
        contents = self.read()

        if not contents and not self.content:
            return None

        if self.content:
            if isinstance(self.content, dict):
                self.yaml_dict = self.content
                return self.yaml_dict
            elif isinstance(self.content, str):
                contents = self.content

        # check if it is yaml
        try:
            if content_type == 'yaml' and contents:
                # Try to set format attributes if supported
                try:
                    self.yaml_dict.fa.set_block_style()
                except AttributeError:
                    pass

                # Try to use RoundTripLoader if supported.
                try:
                    self.yaml_dict = yaml.load(contents, yaml.RoundTripLoader)
                except AttributeError:
                    self.yaml_dict = yaml.safe_load(contents)

                # Try to set format attributes if supported
                try:
                    self.yaml_dict.fa.set_block_style()
                except AttributeError:
                    pass

            elif content_type == 'json' and contents:
                self.yaml_dict = json.loads(contents)
        except yaml.YAMLError as err:
            # Error loading yaml or json
            raise YeditException('Problem with loading yaml file. {}'.format(err))

        return self.yaml_dict

    def get(self, key):
        ''' get a specified key'''
        try:
            entry = Yedit.get_entry(self.yaml_dict, key, self.separator)
        except KeyError:
            entry = None

        return entry

    def pop(self, path, key_or_item):
        ''' remove a key, value pair from a dict or an item for a list'''
        try:
            entry = Yedit.get_entry(self.yaml_dict, path, self.separator)
        except KeyError:
            entry = None

        if entry is None:
            return (False, self.yaml_dict)

        if isinstance(entry, dict):
            # AUDIT:maybe-no-member makes sense due to fuzzy types
            # pylint: disable=maybe-no-member
            if key_or_item in entry:
                entry.pop(key_or_item)
                return (True, self.yaml_dict)
            return (False, self.yaml_dict)

        elif isinstance(entry, list):
            # AUDIT:maybe-no-member makes sense due to fuzzy types
            # pylint: disable=maybe-no-member
            ind = None
            try:
                ind = entry.index(key_or_item)
            except ValueError:
                return (False, self.yaml_dict)

            entry.pop(ind)
            return (True, self.yaml_dict)

        return (False, self.yaml_dict)

    def delete(self, path, index=None, value=None):
        ''' remove path from a dict'''
        try:
            entry = Yedit.get_entry(self.yaml_dict, path, self.separator)
        except KeyError:
            entry = None

        if entry is None:
            return (False, self.yaml_dict)

        result = Yedit.remove_entry(self.yaml_dict, path, index, value, self.separator)
        if not result:
            return (False, self.yaml_dict)

        return (True, self.yaml_dict)

    def exists(self, path, value):
        ''' check if value exists at path'''
        try:
            entry = Yedit.get_entry(self.yaml_dict, path, self.separator)
        except KeyError:
            entry = None

        if isinstance(entry, list):
            if value in entry:
                return True
            return False

        elif isinstance(entry, dict):
            if isinstance(value, dict):
                rval = False
                for key, val in value.items():
                    if entry[key] != val:
                        rval = False
                        break
                else:
                    rval = True
                return rval

            return value in entry

        return entry == value

    def append(self, path, value):
        '''append value to a list'''
        try:
            entry = Yedit.get_entry(self.yaml_dict, path, self.separator)
        except KeyError:
            entry = None

        if entry is None:
            self.put(path, [])
            entry = Yedit.get_entry(self.yaml_dict, path, self.separator)
        if not isinstance(entry, list):
            return (False, self.yaml_dict)

        # AUDIT:maybe-no-member makes sense due to loading data from
        # a serialized format.
        # pylint: disable=maybe-no-member
        entry.append(value)
        return (True, self.yaml_dict)

    # pylint: disable=too-many-arguments
    def update(self, path, value, index=None, curr_value=None):
        ''' put path, value into a dict '''
        try:
            entry = Yedit.get_entry(self.yaml_dict, path, self.separator)
        except KeyError:
            entry = None

        if isinstance(entry, dict):
            # AUDIT:maybe-no-member makes sense due to fuzzy types
            # pylint: disable=maybe-no-member
            if not isinstance(value, dict):
                raise YeditException('Cannot replace key, value entry in dict with non-dict type. ' +
                                     'value=[{}] type=[{}]'.format(value, type(value)))

            entry.update(value)
            return (True, self.yaml_dict)

        elif isinstance(entry, list):
            # AUDIT:maybe-no-member makes sense due to fuzzy types
            # pylint: disable=maybe-no-member
            ind = None
            if curr_value:
                try:
                    ind = entry.index(curr_value)
                except ValueError:
                    return (False, self.yaml_dict)

            elif index is not None:
                ind = index

            if ind is not None and entry[ind] != value:
                entry[ind] = value
                return (True, self.yaml_dict)

            # see if it exists in the list
            try:
                ind = entry.index(value)
            except ValueError:
                # doesn't exist, append it
                entry.append(value)
                return (True, self.yaml_dict)

            # already exists, return
            if ind is not None:
                return (False, self.yaml_dict)
        return (False, self.yaml_dict)

    def put(self, path, value):
        ''' put path, value into a dict '''
        try:
            entry = Yedit.get_entry(self.yaml_dict, path, self.separator)
        except KeyError:
            entry = None

        if entry == value:
            return (False, self.yaml_dict)

        # deepcopy didn't work
        # Try to use ruamel.yaml and fallback to pyyaml
        try:
            tmp_copy = yaml.load(yaml.round_trip_dump(self.yaml_dict,
                                                      default_flow_style=False),
                                 yaml.RoundTripLoader)
        except AttributeError:
            tmp_copy = copy.deepcopy(self.yaml_dict)

        # set the format attributes if available
        try:
            tmp_copy.fa.set_block_style()
        except AttributeError:
            pass

        result = Yedit.add_entry(tmp_copy, path, value, self.separator)
        if result is None:
            return (False, self.yaml_dict)

        # When path equals "" it is a special case.
        # "" refers to the root of the document
        # Only update the root path (entire document) when its a list or dict
        if path == '':
            if isinstance(result, list) or isinstance(result, dict):
                self.yaml_dict = result
                return (True, self.yaml_dict)

            return (False, self.yaml_dict)

        self.yaml_dict = tmp_copy

        return (True, self.yaml_dict)

    def create(self, path, value):
        ''' create a yaml file '''
        if not self.file_exists():
            # deepcopy didn't work
            # Try to use ruamel.yaml and fallback to pyyaml
            try:
                tmp_copy = yaml.load(yaml.round_trip_dump(self.yaml_dict,
                                                          default_flow_style=False),
                                     yaml.RoundTripLoader)
            except AttributeError:
                tmp_copy = copy.deepcopy(self.yaml_dict)

            # set the format attributes if available
            try:
                tmp_copy.fa.set_block_style()
            except AttributeError:
                pass

            result = Yedit.add_entry(tmp_copy, path, value, self.separator)
            if result is not None:
                self.yaml_dict = tmp_copy
                return (True, self.yaml_dict)

        return (False, self.yaml_dict)

    @staticmethod
    def get_curr_value(invalue, val_type):
        '''return the current value'''
        if invalue is None:
            return None

        curr_value = invalue
        if val_type == 'yaml':
            curr_value = yaml.safe_load(str(invalue))
        elif val_type == 'json':
            curr_value = json.loads(invalue)

        return curr_value

    @staticmethod
    def parse_value(inc_value, vtype=''):
        '''determine value type passed'''
        true_bools = ['y', 'Y', 'yes', 'Yes', 'YES', 'true', 'True', 'TRUE',
                      'on', 'On', 'ON', ]
        false_bools = ['n', 'N', 'no', 'No', 'NO', 'false', 'False', 'FALSE',
                       'off', 'Off', 'OFF']

        # It came in as a string but you didn't specify value_type as string
        # we will convert to bool if it matches any of the above cases
        if isinstance(inc_value, str) and 'bool' in vtype:
            if inc_value not in true_bools and inc_value not in false_bools:
                raise YeditException('Not a boolean type. str=[{}] vtype=[{}]'.format(inc_value, vtype))
        elif isinstance(inc_value, bool) and 'str' in vtype:
            inc_value = str(inc_value)

        # There is a special case where '' will turn into None after yaml loading it so skip
        if isinstance(inc_value, str) and inc_value == '':
            pass
        # If vtype is not str then go ahead and attempt to yaml load it.
        elif isinstance(inc_value, str) and 'str' not in vtype:
            try:
                inc_value = yaml.safe_load(inc_value)
            except Exception:
                raise YeditException('Could not determine type of incoming value. ' +
                                     'value=[{}] vtype=[{}]'.format(type(inc_value), vtype))

        return inc_value

    @staticmethod
    def process_edits(edits, yamlfile):
        '''run through a list of edits and process them one-by-one'''
        results = []
        for edit in edits:
            value = Yedit.parse_value(edit['value'], edit.get('value_type', ''))
            if edit.get('action') == 'update':
                # pylint: disable=line-too-long
                curr_value = Yedit.get_curr_value(
                    Yedit.parse_value(edit.get('curr_value')),
                    edit.get('curr_value_format'))

                rval = yamlfile.update(edit['key'],
                                       value,
                                       edit.get('index'),
                                       curr_value)

            elif edit.get('action') == 'append':
                rval = yamlfile.append(edit['key'], value)

            else:
                rval = yamlfile.put(edit['key'], value)

            if rval[0]:
                results.append({'key': edit['key'], 'edit': rval[1]})

        return {'changed': len(results) > 0, 'results': results}

    # pylint: disable=too-many-return-statements,too-many-branches
    @staticmethod
    def run_ansible(params):
        '''perform the idempotent crud operations'''
        yamlfile = Yedit(filename=params['src'],
                         backup=params['backup'],
                         content_type=params['content_type'],
                         backup_ext=params['backup_ext'],
                         separator=params['separator'])

        state = params['state']

        if params['src']:
            rval = yamlfile.load()

            if yamlfile.yaml_dict is None and state != 'present':
                return {'failed': True,
                        'msg': 'Error opening file [{}].  Verify that the '.format(params['src']) +
                               'file exists, that it is has correct permissions, and is valid yaml.'}

        if state == 'list':
            if params['content']:
                content = Yedit.parse_value(params['content'], params['content_type'])
                yamlfile.yaml_dict = content

            if params['key']:
                rval = yamlfile.get(params['key'])

            return {'changed': False, 'result': rval, 'state': state}

        elif state == 'absent':
            if params['content']:
                content = Yedit.parse_value(params['content'], params['content_type'])
                yamlfile.yaml_dict = content

            if params['update']:
                rval = yamlfile.pop(params['key'], params['value'])
            else:
                rval = yamlfile.delete(params['key'], params['index'], params['value'])

            if rval[0] and params['src']:
                yamlfile.write()

            return {'changed': rval[0], 'result': rval[1], 'state': state}

        elif state == 'present':
            # check if content is different than what is in the file
            if params['content']:
                content = Yedit.parse_value(params['content'], params['content_type'])

                # We had no edits to make and the contents are the same
                if yamlfile.yaml_dict == content and \
                   params['value'] is None:
                    return {'changed': False, 'result': yamlfile.yaml_dict, 'state': state}

                yamlfile.yaml_dict = content

            # If we were passed a key, value then
            # we enapsulate it in a list and process it
            # Key, Value passed to the module : Converted to Edits list #
            edits = []
            _edit = {}
            if params['value'] is not None:
                _edit['value'] = params['value']
                _edit['value_type'] = params['value_type']
                _edit['key'] = params['key']

                if params['update']:
                    _edit['action'] = 'update'
                    _edit['curr_value'] = params['curr_value']
                    _edit['curr_value_format'] = params['curr_value_format']
                    _edit['index'] = params['index']

                elif params['append']:
                    _edit['action'] = 'append'

                edits.append(_edit)

            elif params['edits'] is not None:
                edits = params['edits']

            if edits:
                results = Yedit.process_edits(edits, yamlfile)

                # if there were changes and a src provided to us we need to write
                if results['changed'] and params['src']:
                    yamlfile.write()

                return {'changed': results['changed'], 'result': results['results'], 'state': state}

            # no edits to make
            if params['src']:
                # pylint: disable=redefined-variable-type
                rval = yamlfile.write()
                return {'changed': rval[0],
                        'result': rval[1],
                        'state': state}

            # We were passed content but no src, key or value, or edits.  Return contents in memory
            return {'changed': False, 'result': yamlfile.yaml_dict, 'state': state}
        return {'failed': True, 'msg': 'Unkown state passed'}
