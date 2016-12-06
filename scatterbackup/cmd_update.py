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
import shlex
import os
import timeit

import scatterbackup.sbtr
import scatterbackup
import scatterbackup.util
import scatterbackup.config
from scatterbackup.util import sb_init, full_join, split
from scatterbackup.generator import scan_fileinfos
from scatterbackup.database import Database, NullDatabase
from scatterbackup.fileinfo import FileInfo

# sb-update / -v -n
# sb-update / -q
# sb-update -i .sbtr


def on_report_with_database(db, fileinfo):
    db.store(fileinfo)


def on_report(fileinfo, fout=sys.stdout):
    fout.write(fileinfo.json())
    fout.write("\n")


def file_changed(lhs, rhs):
    if lhs != rhs:
        for k, v in lhs.__dict__.items():
            if rhs.__dict__[k] != v:
                print("field changed: {}".format(k))
        return True
    else:
        return False


def fileinfos_split(fileinfos):
    return split(lambda el: el.kind == "directory", fileinfos)


def join_fileinfos(lhs, rhs):
    return full_join(lhs, rhs, lambda fileinfo: fileinfo.path)


class UpdateAction:

    def __init__(self, db):
        self.db = db
        self.verbose = False
        self.checksums = True
        self.relative = False
        self.prefix = None
        self.excludes = []

    def error(self, err):
        # pylint: disable=locally-disabled, no-self-use
        print("{}: cannot process path: {}: {}"
              .format(sys.argv[0], err.filename, err.strerror),
              file=sys.stderr)

    def message(self, msg):
        if self.verbose:
            print(msg)

    def add_checksums(self, fi, ref):
        if fi.kind != 'file':
            return  # no checksum needed

        if ref is not None and \
           ref.blob is not None and \
           ref.blob.is_complete() and \
           ref.mtime == fi.mtime and \
           ref.size == fi.size:
            # recycle checksum from reference FileInfo
            self.message("{}: recycling checksums".format(fi.path))
            fi.blob = ref.blob
        elif self.checksums:
            self.message("{}: calculating checksums".format(fi.path))
            try:
                fi.calc_checksums()
            except OSError as err:
                self.error(err)

    def process_dirs(self, fs_dirs, db_dirs):
        joined = join_fileinfos(fs_dirs, db_dirs)
        # for f, d in joined:
        #     print("   fs: {!r:40} db: {!r:40}".format(f, d))
        for fs_fi, db_fi in joined:
            if fs_fi is None:
                self.message("{}: mark as removed recursive".format(db_fi.path))
                self.db.mark_removed_recursive(db_fi)
            elif db_fi is None:
                self.message("{}: storing in db".format(fs_fi.path))
                self.db.store(fs_fi)
            else:
                if file_changed(fs_fi, db_fi):
                    print("OLD:", fs_fi.json())
                    print("NEW:", db_fi.json())
                    self.message("{}: directory changed".format(fs_fi.path))
                    self.db.mark_removed(db_fi)
                    self.db.store(fs_fi)
                else:
                    self.message("{}: directory already in db, nothing to do".format(fs_fi.path))

    def process_files(self, fs_files, db_files):
        joined = join_fileinfos(fs_files, db_files)
        # for f, d in joined:
        #    print("   fs: {!r:40} db: {!r:40}".format(f, d))
        for fs_fi, db_fi in joined:
            if fs_fi is None:
                self.message("{}: mark as removed".format(db_fi.path))
                self.db.mark_removed(db_fi)
            elif db_fi is None:
                self.message("{}: calculating checksum and storing in db".format(fs_fi.path))
                self.add_checksums(fs_fi, None)
                self.db.store(fs_fi)
            else:
                # recycle checksum from database
                self.add_checksums(fs_fi, db_fi)

                if file_changed(fs_fi, db_fi):
                    print("OLD:", fs_fi.json())
                    print("NEW:", db_fi.json())
                    self.message("{}: file changed".format(fs_fi.path))
                    self.db.mark_removed(db_fi)
                    self.db.store(fs_fi)
                else:
                    self.message("{}: file already in db, nothing to do".format(fs_fi.path))

    def process_directory(self, directory):
        # root directory
        fi_db = self.db.get_by_path(directory)
        self.process_dirs([FileInfo.from_file(directory)],
                          [fi_db] if fi_db is not None else [])

        # content of root directory
        fs_gen = scan_fileinfos(directory,
                                relative=self.relative,
                                # prefix=prefix,  # FIXME: prefix not implemented
                                checksums=False,
                                excludes=self.excludes,
                                onerror=self.error)

        for root, fs_dirs, fs_files in fs_gen:
            start_time = timeit.default_timer()
            result = self.db.get_directory_by_path(root)
            print("{} seconds elapsed for {}".format(timeit.default_timer() - start_time, root))
            db_dirs, db_files = fileinfos_split(result)

            self.process_dirs(fs_dirs, db_dirs)
            self.process_files(fs_files, db_files)

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

    db.init_generation(" ".join([shlex.quote(a) for a in sys.argv]))

    try:
        if args.import_file:
            with scatterbackup.sbtr.open_sbtr(args.import_file) as fin:
                for line in fin:
                    fileinfo = scatterbackup.FileInfo.from_json(line)
                    db.store(fileinfo)
        else:
            for directory in (os.path.abspath(d) for d in args.DIRECTORY):
                update = UpdateAction(db)

                update.verbose = args.verbose
                update.checksums = not args.no_checksum
                update.relative = args.relative if args.prefix is None else True
                update.prefix = args.prefix
                update.excludes = cfg.excludes

                update.process_directory(directory)

        db.commit()

    except KeyboardInterrupt:
        print("KeyboardInterrupt received, shutting down")
        # FIXME: Write a continuation point here
        db.commit()


# EOF #
