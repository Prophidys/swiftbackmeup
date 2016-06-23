# Copyright 2016 Yanis Guenane <yguenane@redhat.com>
# Author: Yanis Guenane <yguenane@redhat.com>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from swiftbackmeup import configuration
from swiftbackmeup import parser
from swiftbackmeup import utils
from swiftbackmeup import lists
from swiftbackmeup.databases import mariadb
from swiftbackmeup.databases import postgresql


_CONF = {
    'clean_local_copy': True,
    'create_container': True,
    'purge_backup': False,
}

_METHODS = ['list_backups', 'list_backups_remote']

def main():

    options = parser.parse()

    if options.conf:
        _CONF['file_path'] = options.conf

    global_configuration = configuration.load_configuration(_CONF)

    configuration.verify_mandatory_parameter(global_configuration)
    backups = configuration.expand_configuration(global_configuration)
    backups = utils.filter_databases(options.databases, backups)
    modes = global_configuration.get('mode')

    # swiftbackmeup backup ...
    if 'version' not in options:
        # If a --list-* options has been specified, call the proper method
        # and exit
        #
        for method in _METHODS:
            if getattr(options, method):
                if method == 'list_backups':
                    lists.list_backups(backups, options)
                elif method == 'list_backups_remote':
                    lists.list_backups_remote(backups, options, modes)
                return
 

        for backup in backups:
            if options.mode in backup['subscriptions']:
                backup['filename'] = utils.build_filename(backup,
                                                          modes[options.mode])
                if backup['type'] == 'postgresql':
                    cur_backup = postgresql.PostgreSQL(backup)
                elif backup['type'] == 'mariadb':
                    cur_backup = mariadb.MariaDB(backup)
                cur_backup.run()
                cur_backup.upload()
                if backup['clean_local_copy']:
                    cur_backup.clean_local_copy()

    # swiftbackmeup restore ...
    else:
        for backup in backups:
            if backup['type'] == 'postgresql':
                cur_backup = postgresql.PostgreSQL(backup)
            elif backup['type'] == 'mariadb':
                cur_backup = mariadb.MariaDB(backup)
            cur_backup.restore(options.version)
