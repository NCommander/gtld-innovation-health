#!/usr/bin/env pyhton3
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

'''Dumps all the nameservers seen in a given zone with their quantity'''

import argparse
import operator

from gtld_data import gtld_db
import gtld_data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('zonefile', help='Zonefile to load')
    parser.add_argument('--origin', help="Origin of the zone file")

    args = parser.parse_args()

    print("Creating database ...")
    gtld_data.gtld_db.create_database()

    gtld_db.database_connection.begin()
    cursor = gtld_db.database_connection.cursor()

    print("Loading zone data, this may take a moment")
    zone_data = gtld_data.ZoneData.load_from_file(cursor, args.zonefile, origin=args.origin)


    print("Unique domains: " + str(len(zone_data.domains)))
    zone_processor = gtld_data.ZoneProcessor(zone_data)
    zone_processor.get_reverse_zone_information(cursor, zone_data.domains)
    zone_data.to_db(cursor)
    gtld_db.database_connection.commit()
    cursor.close()

if __name__ == "__main__":
    main()
