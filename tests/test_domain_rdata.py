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

import dns.rdatatype

import gtld_data
from gtld_data import  gtld_db, gtld_lookup_config

from tests.database_unit_test import DatabaseUnitTest

class TestDomainRData(DatabaseUnitTest):
    def test_read_write_database(self):
        '''Tests reading and writing nameserver records from the database'''

        gtld_db.database_connection.begin()
        cursor = gtld_db.database_connection.cursor()
        zd_id = self.create_zone_data(cursor)
        domain_id = self.create_domain_record(cursor, zd_id, "test.example.")

        # Create an rdata record, and see if we can read/write it back
        rdata = gtld_data.DomainRData()
        rdata._domain_id = domain_id
        rdata.rrtype = "A"
        rdata.rdata = "192.168.1.1"
        rdata.to_db(cursor)

        # Now read it back
        rdata2 = gtld_data.DomainRData.from_db(cursor, rdata.db_id)
        self.assertEqual(rdata.rrtype, rdata2.rrtype)
        self.assertEqual(rdata.rdata, rdata2.rdata)
