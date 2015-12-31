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
import sys
from scatterbackup.generator import generate_fileinfos


def on_report(fileinfo, fout=sys.stdout):
    fout.write(fileinfo.json())
    fout.write("\n")


def process_directory(directory, checksums, relative, prefix,
                      on_report_cb):
    if prefix is not None:
        relative = True

    on_report_cb(scatterbackup.FileInfo.from_file(directory))

    fileidx = 1
    for fileinfo in generate_fileinfos(directory, relative=relative, prefix=prefix, checksums=checksums):
        on_report_cb(fileinfo)
        fileidx += 1


def main():
    parser = argparse.ArgumentParser(description='Collect FileInfo')
    parser.add_argument('DIRECTORY', action='store', type=str, nargs='+',
                        help='directory containing the mod')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="be more verbose")
    parser.add_argument('-q', '--quiet', action='store_true', default=False,
                        help="be less verbose")
    parser.add_argument('-n', '--no-checksum', action='store_true', default=False,
                        help="don't calculate checksums")
    parser.add_argument('-R', '--relative', action='store_true', default=False,
                        help="Path names are stored relative")
    parser.add_argument('-p', '--prefix', type=str, default=None,
                        help="Use a fake prefix to make a relative path absolute")
    parser.add_argument('--host', type=str, default=None,
                        help="Set the host name")
    parser.add_argument('-H', '--no-host', action='store_true', default=False,
                        help="Set the host name to None")
    parser.add_argument('-d', '--database', type=str, default=None,
                        help="Store results in database")
    parser.add_argument('-o', '--output', type=str, default=None,
                        help="Set the output filename")
    args = parser.parse_args()

    on_report_cb = on_report
    if args.output:
        fout = open(args.output, "w")

        def on_report_with_file(fileinfo, fout=fout):
            on_report(fileinfo, fout)

        on_report_cb = on_report_with_file

    if args.database:
        db = scatterbackup.Database(args.database)

        def on_report_with_database(fileinfo):
            db.store(fileinfo)

        on_report_cb = on_report_with_database

    for d in args.DIRECTORY:
        process_directory(d, not args.no_checksum, args.relative, args.prefix, on_report_cb)

    if args.database:
        db.commit()


# EOF #
