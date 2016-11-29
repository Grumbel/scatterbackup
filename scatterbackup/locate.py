# ScatterBackup - A chaotic backup solution
# Copyright (C) 2015 Ingo Ruhnke <grumbel@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import argparse

import scatterbackup
import scatterbackup.util
from scatterbackup.util import sb_init
from scatterbackup.generator import generate_fileinfos
from scatterbackup.vfs import VFS
from scatterbackup.database import Database, NullDatabase


def make_case_insensitive(pattern):
    result = ""
    in_class = False
    for c in pattern:
        if c == '[':
            in_class = True
        elif c == ']':
            in_class = False
        else:
            u = c.upper()
            if u != c:
                c = "[{}{}]".format(c, u)

        result += c
    return result


def parse_args():
    parser = argparse.ArgumentParser(description='Collect FileInfo')
    parser.add_argument('PATTERN', action='store', type=str, nargs='*',
                        help='Pattern to search for')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="be more verbose")
    parser.add_argument('-d', '--database', type=str, default=None,
                        help="Store results in database")
    parser.add_argument('-a', '--all-matches', action='store_true', default=None,
                        help="Return all matches, including past generations")
    parser.add_argument('-i', '--ignore-case', action='store_true',
                        help="Case insensitive search")
    parser.add_argument('-j', '--json', action='store_true',
                        help="Return results as json")
    parser.add_argument('-f', '--format', type=str,
                        help="Format string for results")
    return parser.parse_args()


def fileinfo_to_dict(fileinfo):
    """Flatten the FileInfo dictionary, so it can be used as format string input"""
    result = fileinfo.to_js_dict()
    # FIXME: shall blobinfo be flattened into fileinfo?
    if "blob" in result:
        result['md5'] = result['blob']['md5']
        result['sha1'] = result['blob']['sha1']
        # result['crc32'] = result['blob']['crc32']
    else:
        result['md5'] = "<unknown>"
        result['sha1'] = "<unknown>"
        result['crc32'] = "<unknown>"
    return result


def process_fileinfo_json(fileinfo):
    print(fileinfo.json())


def process_fileinfo_format(fileinfo, fmt):
    print(fmt.format_map(fileinfo_to_dict(fileinfo)))


def process_fileinfo_regular(fileinfo):
    print(fileinfo.path)


def main():
    sb_init()

    args = parse_args()
    db = Database(args.database or scatterbackup.util.make_default_database())

    if args.json:
        process_fileinfo = process_fileinfo_json
    elif args.format is not None:
        process_fileinfo = lambda fileinfo: process_fileinfo_format(fileinfo, args.format)
    else:
        process_fileinfo = process_fileinfo_regular

    if args.PATTERN == []:
        fileinfos = db.get_all()
        for fileinfo in fileinfos:
            process_fileinfo(fileinfo)
    else:
        for pattern in args.PATTERN:
            if args.ignore_case:
                pattern = make_case_insensitive(pattern)

            if args.verbose:
                print("Pattern: {}".format(pattern))

            fileinfos = db.get_by_glob(pattern)
            for fileinfo in fileinfos:
                process_fileinfo(fileinfo)

# EOF #
