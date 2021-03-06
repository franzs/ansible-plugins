# Ansible lookup plugin for getting the content of the first available file
# (c) 2015,2016 David Lundgren <dlundgren@syberisle.net>
#
# MIT License

# For each item will find the first file and return the path
DOCUMENTATION = """
    author: David Lundgren
    lookup: first_found
    options:
        lookup_file_paths:
            type: list
            default: []
            ini:
                - key: lookup_file_paths
                  section: defaults
            yaml:
                key: defaults.lookup_file_paths
"""

import os

from ansible import utils
from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

# ansible 2.4
try:
    from ansible.parsing.plugin_docs import read_docstring

    # load the definitions
    dstring = read_docstring(__file__.replace('.pyc', '.py'), verbose = False, ignore_errors = False)
    if dstring.get('doc', False):
        if 'options' in dstring['doc'] and isinstance(dstring['doc']['options'], dict):
            C.config.initialize_plugin_configuration_definitions('lookup', 'first_found', dstring['doc']['options'])
except:
    None

class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        anydict = False
        skip = False

        for term in terms:
            if isinstance(term, dict):
                anydict = True
                total_search = []

        if anydict:
            for term in terms:
                if isinstance(term, dict):
                    files = term.get('files', [])
                    paths = term.get('paths', [])
                    skip = utils.boolean(term.get('skip', False))

                    filelist = files
                    if isinstance(files, str):
                        files = files.replace(',', ' ')
                        files = files.replace(';', ' ')
                        filelist = files.split(' ')

                    pathlist = paths
                    if paths:
                        if isinstance(paths, str):
                            paths = paths.replace(',', ' ')
                            paths = paths.replace(':', ' ')
                            paths = paths.replace(';', ' ')
                            pathlist = paths.split(' ')

                    if not pathlist:
                        total_search = filelist
                    else:
                        for path in pathlist:
                            for fn in filelist:
                                f = os.path.join(path, fn)
                                total_search.append(f)
                else:
                    total_search.append(term)
        else:
            total_search = terms

        paths = self.get_paths(variables)
        for fn in total_search:
            for path in paths:
                path = os.path.join(path, fn)
                if os.path.exists(path):
                    return [path]
        else:
            if skip:
                return []
            else:
                return [None]

    def get_paths(self, vars):
        paths = []
        basedir = self.get_basedir(vars)
        try:
            # Ansible 2.4
            lookupPaths = C.config.get_config_value('lookup_file_paths', None, 'lookup', 'first_found')
        except AttributeError:
            # Ansible 2.3
            lookupPaths = C.get_config(C.p, C.DEFAULTS, 'lookup_file_paths', None, [], value_type='list')
        except TypeError:
            # Ansible 2.2.x and below
            lookupPaths = C.get_config(C.p, C.DEFAULTS, 'lookup_file_paths', None, [], islist=True)

        for path in lookupPaths:
            path = utils.path.unfrackpath(path)
            if os.path.exists(path):
                paths.append(path)

        if '_original_file' in vars:
            for roledir in ('templates', 'vars'):
                path = utils.path.path_dwim(self.basedir, os.path.join(self.basedir, '..', roledir))
                if os.path.exists(path):
                    paths.append(path)

        if 'playbook_dir' in vars:
            paths.append(vars['playbook_dir'])

        paths.append(self._loader.path_dwim(basedir))

        unq = []
        [unq.append(i) for i in paths if not unq.count(i)]

        return unq
