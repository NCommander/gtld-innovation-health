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

import unittest
import os
import tempfile

import gtld_data
from gtld_data import  gtld_db, gtld_lookup_config

class DatabaseUnitTest(unittest.TestCase):
    def setUp(self):
        self.db_filename = None
        file_descriptor, self.db_filename = tempfile.mkstemp()
        os.close(file_descriptor) # Don't need to write anything to it
        gtld_lookup_config.database_path = self.db_filename

        # Just need a randomly generated filename
        os.remove(self.db_filename)
        gtld_db.create_database()

    def tearDown(self):
        gtld_db.database_connection.close()
        os.remove(self.db_filename)

    def create_zone_data(self, cursor):
        zd = gtld_data.ZoneData()
        zd.soa = "1"
        zd.origin = "example"
        zd.to_db(cursor)

        return zd.db_id

    def create_nameserver_record(self, cursor, zd_id, nameserver):
        nameserver_obj = gtld_data.NameserverRecord(nameserver)
        nameserver_obj._zonefile_id = zd_id
        nameserver_obj.domain_count = 1
        nameserver_obj.to_db(cursor)
        return nameserver_obj

    def create_ptr_record(self, cursor, zd_id, ip_address, reverse_name):
        ptr_obj = gtld_data.PtrRecord(ip_address, reverse_name)
        ptr_obj._zonefile_id = zd_id
        ptr_obj.to_db(cursor)
        return ptr_obj
