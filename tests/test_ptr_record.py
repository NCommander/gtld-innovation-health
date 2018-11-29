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

class TestPtrRecord(DatabaseUnitTest):
    def test_read_write_database(self):
        '''Tests reading and writing nameserver records from the database'''

        # Create a fake zone entry for us to play with
        gtld_db.database_connection.begin()
        cursor = gtld_db.database_connection.cursor()
        db_id = self.create_zone_data(cursor)

        # Create a nameserver record
        ptr_obj = gtld_data.PtrRecord("10.10.10.1", "test.example.")
        ptr_obj._zonefile_id = db_id
        ptr_obj.to_db(cursor)

        # Now read it back
        ptr_obj2 = gtld_data.PtrRecord.from_db(cursor, ptr_obj.db_id)
        self.assertEqual(ptr_obj.reverse_lookup_name, ptr_obj2.reverse_lookup_name)
        self.assertEqual(ptr_obj.ip_address, ptr_obj2.ip_address)
        cursor.close()

    def test_read_all(self):
        gtld_db.database_connection.begin()
        cursor = gtld_db.database_connection.cursor()
        db_id = self.create_zone_data(cursor)

        # Create a nameserver record
        ptr_obj1 = gtld_data.PtrRecord("10.10.10.1", "test1.example.")
        ptr_obj1._zonefile_id = db_id
        ptr_obj1.to_db(cursor)

        ptr_obj2 = gtld_data.PtrRecord("10.10.10.2", "test2.example.")
        ptr_obj2._zonefile_id = db_id
        ptr_obj2.to_db(cursor)


        ptr_obj3 = gtld_data.PtrRecord("10.10.10.3", "test3.example.")
        ptr_obj3._zonefile_id = db_id
        ptr_obj3.to_db(cursor)

        ptr_set = gtld_data.PtrRecord.read_all_from_db(cursor, db_id)
        self.assertEqual(len(ptr_set), 3)
        self.assertIn(ptr_obj1, ptr_set)
        self.assertIn(ptr_obj2, ptr_set)
        self.assertIn(ptr_obj3, ptr_set)
