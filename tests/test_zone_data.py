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

class TestZoneData(unittest.TestCase):
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

    def test_reading_zone_file_to_db(self):
        '''Tests looking up nameservers'''
        zone_data = gtld_data.ZoneData.load_from_file('tests/data/db.internic', origin='internic')
        self.assertEqual(len(zone_data.domains), 2)
