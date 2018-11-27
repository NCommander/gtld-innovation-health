# Copyright 2018 Michael Casadevall <michael@casadevall.pro>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the 
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

'''Holds the record of a domain'''

import fdb

from gtld_data.config import gtld_lookup_config

CREATION_FILES = [
    'sql/0001_base.sql'
]

class Database(object):
    def __init__(self):
        self.database_connection = None

    def connect(self):
        '''Connects to an existing database'''
        self.database_connection = fdb.connect(database=gtld_lookup_config.database_path,
                                               user=gtld_lookup_config.database_username,
                                               password=gtld_lookup_config.database_password)

    def create_database(self):
        '''Creates a new database from scratch'''
        self.database_connection = fdb.create_database(database=gtld_lookup_config.database_path,
                                                       user=gtld_lookup_config.database_username,
                                                       password=gtld_lookup_config.database_password)

        # Load in the schema files and execute them
        for file in CREATION_FILES:
            with open(file, 'r') as f:
                sql_cmds = f.read()

                # FSQL will only accept a single statement per execute() which is annoying
                self.database_connection.begin()
                for statement in sql_cmds.split(';'):
                    if statement.rstrip() == "":
                        continue # Skip blanks, and trailing newline at the end
                    cursor = self.database_connection.cursor()
                    cursor.execute(statement.rstrip())
                self.database_connection.commit()

gtld_db = Database()