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
import dns.rdatatype

import os
import tempfile

import gtld_data
from gtld_data import  gtld_db, gtld_lookup_config

from tests.database_unit_test import DatabaseUnitTest

class TestNameserverRecord(DatabaseUnitTest):
    def test_read_write_database(self):
        '''Tests reading and writing nameserver records from the database'''

        # Create a fake zone entry for us to play with
        gtld_db.database_connection.begin()
        cursor = gtld_db.database_connection.cursor()
        db_id = self.create_zone_data(cursor)

        # Create a nameserver record
        nameserver_obj = gtld_data.NameserverRecord("test.example.")
        nameserver_obj._zonefile_id = db_id
        nameserver_obj.to_db(cursor)

        # Now read it back
        nameserver_obj2 = gtld_data.NameserverRecord.from_db(cursor, nameserver_obj.db_id)
        self.assertEqual(nameserver_obj.nameserver, nameserver_obj2.nameserver)
        self.assertEqual(nameserver_obj.count, nameserver_obj2.count)
        cursor.close()

    def test_read_all(self):
        gtld_db.database_connection.begin()
        cursor = gtld_db.database_connection.cursor()
        db_id = self.create_zone_data(cursor)

        # Create a nameserver record
        nameserver_obj1 = gtld_data.NameserverRecord("test1.example.")
        nameserver_obj1._zonefile_id = db_id
        nameserver_obj1.to_db(cursor)

        nameserver_obj2 = gtld_data.NameserverRecord("test2.example.")
        nameserver_obj2._zonefile_id = db_id
        nameserver_obj2.to_db(cursor)


        nameserver_obj3 = gtld_data.NameserverRecord("test3.example.")
        nameserver_obj3._zonefile_id = db_id
        nameserver_obj3.to_db(cursor)

        ns_set = gtld_data.NameserverRecord.read_all_from_db(cursor, db_id)
        self.assertEqual(len(ns_set), 3)
        self.assertIn(nameserver_obj1, ns_set)
        self.assertIn(nameserver_obj2, ns_set)
        self.assertIn(nameserver_obj3, ns_set)
