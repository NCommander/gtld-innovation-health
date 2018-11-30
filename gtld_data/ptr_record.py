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

from gtld_data.config import gtld_lookup_config
from gtld_data.domain_status import DomainStatus
from gtld_data.db import gtld_db

import dns.resolver
import dns.rdatatype
import dns.reversename

class PtrRecord(object):
    def __hash__(self):
        return hash(self.reverse_lookup_name + self.ip_address)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __init__(self, ip_address, name):
        self._zonefile_id = None
        self._domain_id = None
        self.db_id = None
        self.ip_address = ip_address
        self.reverse_lookup_name = name
    
    @classmethod
    def from_db(cls, cursor, db_id):
        ptr_select = """SELECT id, zone_file_id, ip_address, reverse_lookup_name FROM ptr_records WHERE id=?"""
        cursor.execute(ptr_select, [int(db_id)])
        row = cursor.fetchone()
        ptr_obj = cls(None, None)
        ptr_obj._db_row_to_self(row)
        return ptr_obj

    @classmethod
    def read_all_from_db(cls, cursor, zonefile_id):
        '''Reads all nameservers for a given zonefile id'''
        ptr_select_all = """SELECT id, zone_file_id, ip_address, reverse_lookup_name FROM ptr_records WHERE zone_file_id=?"""
        cursor.execute(ptr_select_all, [int(zonefile_id)])

        ptr_set = set()
        while True:
            row = cursor.fetchone()
            if row is None:
                break

            ptr_obj = cls(None, None)
            ptr_obj._db_row_to_self(row)
            ptr_set.add(ptr_obj)
        
        return ptr_set

    def _db_row_to_self(self, db_dict):
        '''Converts db_dict to class data'''
        self.db_id = db_dict[0]
        self._zonefile_id = db_dict[1]
        self.ip_address = db_dict[2]
        self.reverse_lookup_name = db_dict[3]

    def to_db(self, cursor):
        '''Stores nameserver in the database'''
        # Load the list of nameservers and append a database id to the dict
        ptr_insert = """INSERT INTO ptr_records (zone_file_id, ip_address, reverse_lookup_name) VALUES (?, ?, ?) RETURNING id"""
        ptr_select = """SELECT id FROM ptr_records WHERE ip_address = ? AND reverse_lookup_name = ?"""

        domain_ptr_select = """SELECT id FROM domain_ptr_records WHERE domain_id = ? AND ptr_record_id = ?"""
        domain_ptrs_insert = """INSERT INTO domain_ptr_records(domain_id, ptr_record_id) VALUES (?, ?)"""

        # Try doing a SELECT before inserting
        cursor.execute(ptr_select, [self.ip_address, self.reverse_lookup_name])
        row = cursor.fetchone()
        if row is not None:
            self.db_id = int(row[0])
        else:
            cursor.execute(ptr_insert, (self._zonefile_id, self.ip_address, self.reverse_lookup_name))
            self.db_id = int(cursor.fetchone()[0])

        # Now try to link it to the domain table if possible
        if self._domain_id is not None:
            cursor.execute(domain_ptr_select, [self._domain_id, self.db_id])
            row = cursor.fetchone()
            if row is None:
                cursor.execute(domain_ptrs_insert, [self._domain_id, self.db_id])
