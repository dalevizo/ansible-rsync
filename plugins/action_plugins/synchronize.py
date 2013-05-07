#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012-2013, Timothy Appnel <tim@appnel.com>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os.path

from ansible import utils
from ansible.runner.return_data import ReturnData


class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner

    def _process_origin(
        self,
        host,
        path,
        user,
        ):
        if not host in ['127.0.0.1', 'localhost']:
            return '%s@%s:%s' % (user, host, path)
        else:
            return self.rsync_path(path)

    def rsync_path(self, path):
        return os.path.relpath(os.path.expanduser(path),
                               os.path.expanduser('~'))

    def run(
        self,
        conn,
        tmp,
        module_name,
        module_args,
        inject,
        complex_args=None,
        **kwargs
        ):
        ''' generates params and passes them on to the rsync module '''

        # load up options

        options = {}
        if complex_args:
            options.update(complex_args)
        options.update(utils.parse_kv(module_args))
        source = options.get('src', None)
        dest = options.get('dest', None)

        try:
            options['rsync_path'] = inject['ansible_rsync_path']
        except KeyError:
            pass
        if not self.runner.transport == 'local':
            options['private_key'] = \
                inject.get('ansible_ssh_private_key_file',
                           self.runner.private_key_file)
            options['tmp_dir'] = tmp
            try:
                delegate = inject['delegate_to']
            except KeyError:
                pass
            if not delegate:
                delegate = 'localhost'
            inv_hostname = inject.get('ansible_ssh_host',
                    inject['inventory_hostname'])
            if options.get('mode', 'push') == 'pull':
                (delegate, inv_hostname) = (inv_hostname, delegate)
            actual_user = inject.get('ansible_ssh_user',
                    self.runner.remote_user)
            source = self._process_origin(delegate, source, actual_user)
            dest = self._process_origin(inv_hostname, dest, actual_user)
        else:
            source = self.rsync_path(source)
            dest = self.rsync_path(dest)

        options['src'] = source
        options['dest'] = dest
        try:
            del options['mode']
        except KeyError:
            pass

        # run the rsync module

        self.runner.module_args = ' '.join(['%s=%s' % (k, v) for (k,
                v) in options.items()])
        return self.runner._execute_module(conn, tmp, 'synchronize',
                self.runner.module_args, inject=inject)


