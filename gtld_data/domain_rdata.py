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

'''Holds domain records'''

from gtld_data.config import gtld_lookup_config
from gtld_data.domain_status import DomainStatus
from gtld_data.db import gtld_db

import dns.resolver
import dns.rdatatype
import dns.reversename

class DomainRData(object):
    def __hash__(self):
        return hash(self.rrtype + self.rdata)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __init__(self):
        self._domain_id = None
        self.db_id = None
        self.rrtype = None
        self.rdata = None
    
    @classmethod
    def from_db(cls, cursor, db_id):
        ptr_select = """SELECT id, domain_id, rrtype, rdata FROM domain_rdata WHERE id=?"""
        cursor.execute(ptr_select, [int(db_id)])
        row = cursor.fetchone()
        rdata_obj = cls()
        rdata_obj._db_row_to_self(row)
        return rdata_obj

    @classmethod
    def read_all_from_db_for_domain(cls, cursor, domain_id):
        '''Reads all nameservers for a given zonefile id'''
        ptr_select_all = """SELECT id, domain_id, rrtype, rdata FROM domain_rdata WHERE domain_id=?"""
        cursor.execute(ptr_select_all, [int(domain_id)])

        ptr_set = set()
        while True:
            row = cursor.fetchone()
            if row is None:
                break

            ptr_obj = cls()
            ptr_obj._db_row_to_self(row)
            ptr_set.add(ptr_obj)
        
        return ptr_set

    def _db_row_to_self(self, db_dict):
        '''Converts db_dict to class data'''
        self.db_id = db_dict[0]
        self._domain_id = db_dict[1]
        self.rrtype = db_dict[2]
        self.rdata = db_dict[3]

    def to_db(self, cursor):
        '''Stores nameserver in the database'''
        # Load the list of nameservers and append a database id to the dict
        nameserver_insert = """INSERT INTO domain_rdata (domain_id, rrtype, rdata) VALUES (?, ?, ?) RETURNING id"""
        cursor.execute(nameserver_insert, (self._domain_id, self.rrtype, self.rdata))
        self.db_id = int(cursor.fetchone()[0])
