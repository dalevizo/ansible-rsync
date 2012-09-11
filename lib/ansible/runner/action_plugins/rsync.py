# (c) 2012, Timothy Appnel <tim@appnel.com>
#
# This file is part of Ansible
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
import subprocess

from ansible import utils
from ansible.runner.return_data import ReturnData


class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner

    def run(
        self,
        conn,
        tmp,
        module_name,
        inject,
        ):
        ''' handler for rsync operations '''

        # load up options

        options = utils.parse_kv(self.runner.module_args)
        source = options.get('src', None)
        dest = options.get('dest', None)

        # rsync param eventually

        cmd = 'rsync --archive --delay-updates --compress --temp-dir ' \
            + tmp
        v = options.get('verbosity', 0)
        if v:
            cmd = '%s -%s' % (cmd, 'v' * v)
        else:
            cmd = cmd + ' --quiet'
        if options.get('delete', False):
            cmd = cmd + ' --delete-after'
        source = utils.template(source, inject)
        dest = utils.template(dest, inject)
        if not self.runner.transport == 'local':
            cmd = cmd + " --rsh '%s -i %s'" % ('ssh',
                    self.runner.private_key_file)  # param or RSYNC_RSH env?
            if 'rsync_path' in inject:
                cmd = '%s --rsync-path %s' % (cmd,
                        inject['ansible_rsync_path'])
            mode = options.get('mode', 'copy')
            if mode == 'copy':
                dest = '%s@%s:%s' % (self.runner.remote_user,
                        conn.host, dest)
                source = utils.path_dwim(self.runner.basedir, source)
            elif mode == 'fetch':
                source = '%s@%s:%s' % (self.runner.remote_user,
                        conn.host, source)
                dest = utils.path_dwim(self.runner.basedir, dest)
        else:
            source = utils.path_dwim(self.runner.basedir, source)
            dest = utils.path_dwim(self.runner.basedir, dest)

        cmd = ' '.join([cmd, source, dest])
        cmd = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        (out, err) = cmd.communicate()
        if cmd.returncode:
            msg = err
        else:
            msg = out
        result = dict(msg=msg, rc=cmd.returncode)
        return ReturnData(conn=conn, result=result)

