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

import gtld_data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('zonefile', help='Zonefile to load')
    parser.add_argument('outfile', help="Output File (in CSV)")
    parser.add_argument('--origin', help="Origin of the zone file")

    args = parser.parse_args()

    print("Loading zone data, this may take a moment")
    zd = gtld_data.ZoneData.load_from_file(args.zonefile, args.origin)

    print("Processing zone into useful data")

    print("Unique domains: " + str(len(zd.domains)))

    sorted_d = sorted(zd.known_nameservers.items(), key=lambda k_v: k_v[1]['count'], reverse=True)
    with open(args.outfile, 'w') as f:
        for domain in sorted_d:
            f.write(domain[0] + "," + str(domain[1]['count']) + "\n")
        f.write("\n")

        
if __name__ == "__main__":
    main()
