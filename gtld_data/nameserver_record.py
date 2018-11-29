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

class NameserverRecord(object):
    def __hash__(self):
        return hash(self.nameserver)

    def __eq__(self, other):
        return self.nameserver == other.nameserver

    def __init__(self, name):
        self._zonefile_id = None
        self.db_id = None
        self.nameserver = name
        self.count = 0
    
    def increment_count(self):
        self.count = self.count+1

    @classmethod
    def from_db(cls, cursor, db_id):
        nameserver_select = """SELECT id, zone_file_id, nameserver, domain_count FROM nameservers WHERE id=?"""
        cursor.execute(nameserver_select, [int(db_id)])
        row = cursor.fetchone()
        nameserver_obj = cls(None)
        nameserver_obj._db_rows_to_self(row)
        return nameserver_obj

    @classmethod
    def read_all_from_db(cls, cursor, zonefile_id):
        '''Reads all nameservers for a given zonefile id'''
        nameserver_select = """SELECT id, zone_file_id, nameserver, domain_count FROM nameservers WHERE zone_file_id=?"""
        cursor.execute(nameserver_select, [int(zonefile_id)])

        ns_set = set()
        while True:
            row = cursor.fetchone()
            if row is None:
                break

            nameserver_obj = cls(None)
            nameserver_obj._db_rows_to_self(row)
            ns_set.add(nameserver_obj)
        
        return ns_set

    def _db_rows_to_self(self, db_dict):
        '''Converts db_dict to class data'''
        self.db_id = db_dict[0]
        self._zonefile_id = db_dict[1]
        self.nameserver = db_dict[2]
        self.domain_count = db_dict[3]

    def to_db(self, cursor):
        '''Stores nameserver in the database'''
        # Load the list of nameservers and append a database id to the dict
        nameserver_insert = """INSERT INTO nameservers (zone_file_id, nameserver, domain_count) VALUES (?, ?, ?) RETURNING id"""
        cursor.execute(nameserver_insert, (self._zonefile_id, self.nameserver, self.count))
        self.db_id = int(cursor.fetchone()[0])
