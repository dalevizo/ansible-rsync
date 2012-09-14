#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Timothy Appnel <tim@appnel.com>
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

from ansible import utils
from ansible.runner.return_data import ReturnData


class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner

    def _process_origin(self, host, path):
        if host in ['127.0.0.1', 'localhost']:
            return utils.path_dwim(self.runner.basedir, path)
        else:
            return '%s@%s:%s' % (self.runner.remote_user, host, path)

    def run(
        self,
        conn,
        tmp,
        module_name,
        inject,
        ):
        ''' generates params and passes them on to the rsync module '''

        options = utils.parse_kv(self.runner.module_args)
        source = utils.template(options.get('src', None))
        dest = utils.template(options.get('dest', None))
        try:
            options['rsync_path'] = inject['ansible_rsync_path']
        except KeyError:
            pass
        if not self.runner.transport == 'local':
            options['private_key'] = self.runner.private_key_file
            options['tmp_dir'] = tmp
            try:
                delegate = inject['delegate_to']
            except KeyError:
                delegate = 'localhost'
            source = self._process_origin(delegate, source)
            inv_hostname = inject['host_variables']['inventory_hostname'
                    ]
            dest = self._process_origin(inv_hostname, dest)
            if mode == 'pull':
                (source, dest) = (dest, source)
        else:
            source = utils.path_dwim(self.runner.basedir, source)
            dest = utils.path_dwim(self.runner.basedir, dest)
        options['src'] = source
        options['dest'] = dest

        # run the rsync module

        self.runner.module_args = ' '.join(['%s=%s' % (k, v) for (k,
                v) in options.items()])
        return self.runner._execute_module(conn, tmp, 'rsync',
                self.runner.module_args, inject=inject)


