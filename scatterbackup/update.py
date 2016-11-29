# ScatterBackup - A chaotic backup solution
# Copyright (C) 2016 Ingo Ruhnke <grumbel@gmail.com>
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

import scatterbackup.sbtr
import scatterbackup
import scatterbackup.util
import scatterbackup.config
from scatterbackup.util import sb_init
from scatterbackup.generator import generate_fileinfos
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


def file_changed(lhs, rhs):
    return lhs != rhs


def process_directory(db, directory, checksums, relative, prefix, excludes,
                      on_report_cb, verbose=False):

    if prefix is not None:
        relative = True

    gen = generate_fileinfos(directory,
                             relative=relative,
                             prefix=prefix,
                             checksums=False,
                             excludes=excludes,
                             onerror=on_error)

    for fileinfo in gen:
        # if fileinfo.kind == 'directory':
        if verbose:
            print("processing:", fileinfo.path)

        old_fileinfo = db.get_by_path(fileinfo.path)

        if fileinfo.kind == 'file' and checksums:
            if old_fileinfo is None or \
               old_fileinfo.mtime != fileinfo.mtime or \
               old_fileinfo.size != fileinfo.size:
                try:
                    print("{}: calculating checksums".format(fileinfo.path))
                    fileinfo.calc_checksums()
                except OSError as err:
                    on_error(err)
            else:
                if old_fileinfo.blob is not None and old_fileinfo.blob.is_complete():
                    fileinfo.blob = old_fileinfo.blob
                else:
                    print("{}: calculating checksums".format(fileinfo.path))
                    fileinfo.calc_checksums()

        if (fileinfo.kind == 'file' and (old_fileinfo is None or old_fileinfo.blob is None)) \
           or file_changed(old_fileinfo, fileinfo):
            # FIXME: only do if things changed
            on_report_cb(fileinfo)
        else:
            if verbose:
                print("{}: already in database".format(fileinfo.path))


def parse_args():
    parser = argparse.ArgumentParser(description='Collect FileInfo')
    parser.add_argument('DIRECTORY', action='store', type=str, nargs='*',
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
    parser.add_argument('-d', '--database', type=str, default=None,
                        help="Store results in database")
    parser.add_argument('-c', '--config', type=str, default=None,
                        help="Load configuration file")
    parser.add_argument('-i', '--import-file', type=str, default=None,
                        help="Import data from .js file")
    parser.add_argument('-o', '--output', type=str, default=None,
                        help="Set the output filename")
    return parser.parse_args()


def main():
    sb_init()

    args = parse_args()

    cfg = scatterbackup.config.Config()
    cfg.load(args.config)

    if args.dry_run:
        db = NullDatabase()
    else:
        db = Database(args.database or scatterbackup.util.make_default_database())

    def my_on_report_cb(fileinfo, db=db):
        on_report_with_database(db, fileinfo)
    on_report_cb = my_on_report_cb

    try:
        if args.import_file:
            with scatterbackup.sbtr.open_sbtr(args.import_file) as fin:
                for line in fin:
                    fileinfo = scatterbackup.FileInfo.from_json(line)
                    on_report_cb(fileinfo)
        else:
            for d in args.DIRECTORY:
                process_directory(db, d, not args.no_checksum, args.relative, args.prefix, cfg.excludes,
                                  on_report_cb, verbose=args.verbose)
        db.commit()
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, shutting down")
        # FIXME: Write a continuation point here
        db.commit()


# EOF #
