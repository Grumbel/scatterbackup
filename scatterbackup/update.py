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
import sys

import scatterbackup
from scatterbackup.generator import generate_fileinfos
from scatterbackup.vfs import VFS
from scatterbackup.database import Database, NullDatabase

# sb-update / -v -n
# sb-update / -q
# sb-update -i .sbtr


def on_report_with_database(db, fileinfo):
    db.store(fileinfo)


def on_report(fileinfo, fout=sys.stdout):
    fout.write(fileinfo.json())
    fout.write("\n")


def on_error(err):
    sys.stderr.write("{}: cannot process path: {}: {}\n".format(
        sys.argv[0], err.filename, err.strerror))


def process_directory(db, directory, checksums, relative, prefix,
                      on_report_cb):

    if prefix is not None:
        relative = True

    gen = generate_fileinfos(directory,
                             relative=relative,
                             prefix=prefix,
                             checksums=False,
                             onerror=on_error)

    for fileinfo in gen:
        # if fileinfo.kind == 'directory':
        print("processing:", fileinfo.path)

        old_fileinfo = db.get_by_path(fileinfo.path)
        if checksums:
            if old_fileinfo is None or \
               old_fileinfo.mtime != fileinfo.mtime or old_fileinfo.size != fileinfo.size:
                try:
                    fileinfo.calc_checksums()
                except OSError as err:
                    on_error(err)

        # FIXME: only do if things changed
        on_report_cb(fileinfo)


def parse_args():
    parser = argparse.ArgumentParser(description='Collect FileInfo')
    parser.add_argument('DIRECTORY', action='store', type=str, nargs='+',
                        help='directory containing the mod')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="be more verbose")
    parser.add_argument('-q', '--quiet', action='store_true', default=False,
                        help="be less verbose")
    parser.add_argument('-n', '--dry-run', action='store_true', default=False,
                        help="Don't update the database, print updates to stdout")
    parser.add_argument('-N', '--no-checksum', action='store_true', default=False,
                        help="don't calculate checksums")
    parser.add_argument('-R', '--relative', action='store_true', default=False,
                        help="Path names are stored relative")
    parser.add_argument('-p', '--prefix', type=str, default=None,
                        help="Use a fake prefix to make a relative path absolute")
    parser.add_argument('--host', type=str, default=None,
                        help="Set the host name")
    parser.add_argument('-H', '--no-host', action='store_true', default=False,
                        help="Set the host name to None")
    parser.add_argument('-d', '--database', type=str, default=None, required=True,
                        help="Store results in database")
    parser.add_argument('-o', '--output', type=str, default=None,
                        help="Set the output filename")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.dry_run:
        db = NullDatabase()
    else:
        db = Database(args.database)

    on_report_cb = lambda fileinfo, db=db: on_report_with_database(db, fileinfo)

    try:
        for d in args.DIRECTORY:
            process_directory(db, d, not args.no_checksum, args.relative, args.prefix, on_report_cb)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, shutting down")
        # FIXME: Write a continuation point here
        db.commit()


# EOF #
