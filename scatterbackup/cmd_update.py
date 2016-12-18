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
        # for k, v in lhs.__dict__.items():
        #     if rhs.__dict__[k] != v:
        #        print("field changed: {}".format(k))
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
        self.verbose = 0
        self.checksums = True
        self.relative = False
        self.prefix = None
        self.excludes = []

    def log_error(self, err):
        # pylint: disable=no-self-use
        print("{}: cannot process path: {}: {}"
              .format(sys.argv[0], err.filename, err.strerror),
              file=sys.stderr)

    def log_info(self, verbose, msg):
        # pylint: disable=no-self-use
        if self.verbose >= verbose:
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
            # self.log_info(1, "{}: recycling checksums".format(fi.path))
            fi.blob = ref.blob
        elif self.checksums:
            self.log_info(1, "{}: calculating checksums".format(fi.path))
            try:
                fi.calc_checksums()
            except OSError as err:
                self.log_error(err)

    def process_dirs(self, fs_dirs, db_dirs):
        joined = join_fileinfos(fs_dirs, db_dirs)
        # for f, d in joined:
        #     print("   fs: {!r:40} db: {!r:40}".format(f, d))
        for fs_fi, db_fi in joined:
            if fs_fi is None:
                self.log_info(1, "{}: directory removed".format(db_fi.path))
                self.db.mark_removed_recursive(db_fi)
            elif db_fi is None:
                self.log_info(1, "{}: storing directory in db".format(fs_fi.path))
                self.db.store(fs_fi)
            else:
                if file_changed(fs_fi, db_fi):
                    # print("OLD:", fs_fi.json())
                    # print("NEW:", db_fi.json())
                    self.log_info(1, "{}: directory changed".format(fs_fi.path))
                    self.db.mark_removed(db_fi)
                    self.db.store(fs_fi)
                else:
                    self.log_info(3, "{}: directory already in db, nothing to do".format(fs_fi.path))

    def process_files(self, fs_files, db_files):
        joined = join_fileinfos(fs_files, db_files)
        # for f, d in joined:
        #   print("   fs: {!r:40} db: {!r:40}".format(f, d))
        for fs_fi, db_fi in joined:
            if fs_fi is None:
                self.log_info(1, "{}: file removed".format(db_fi.path))
                self.db.mark_removed(db_fi)
            elif db_fi is None:
                self.add_checksums(fs_fi, None)
                self.log_info(1, "{}: storing file in db".format(fs_fi.path))
                self.db.store(fs_fi)
            else:
                # recycle checksum from database
                self.add_checksums(fs_fi, db_fi)

                if file_changed(fs_fi, db_fi):
                    # print("OLD:", fs_fi.json())
                    # print("NEW:", db_fi.json())
                    self.log_info(1, "{}: file changed".format(fs_fi.path))
                    self.db.mark_removed(db_fi)
                    self.db.store(fs_fi)
                else:
                    self.log_info(3, "{}: file already in db, nothing to do".format(fs_fi.path))

    def process_directory(self, fi_fs, recursive=True):
        # root directory
        fi_db = self.db.get_one_by_path(fi_fs.path)
        self.process_dirs([fi_fs],
                          [fi_db] if fi_db is not None else [])

        # content of root directory
        fs_gen = scan_fileinfos(fi_fs.path,
                                relative=self.relative,
                                # prefix=prefix,  # FIXME: prefix not implemented
                                checksums=False,
                                excludes=self.excludes,
                                onerror=self.log_error)

        if not recursive:
            fs_gen = [next(fs_gen)]

        for root, fs_dirs, fs_files in fs_gen:
            self.log_info(2, "processing {}".format(root))
            result = self.db.get_directory_by_path(root)
            db_dirs, db_files = fileinfos_split(result)

            self.process_dirs(fs_dirs, db_dirs)
            self.process_files(fs_files, db_files)

    def process_file(self, fi_fs):
        fi_db = self.db.get_one_by_path(fi_fs.path)
        self.process_files([fi_fs],
                           [fi_db] if fi_db is not None else [])

    def process_path(self, path, recursive=True):
        fi = FileInfo.from_file(path)
        if fi.kind == "directory":
            self.process_directory(fi)
        else:
            self.process_file(fi)


def parse_args():
    parser = argparse.ArgumentParser(description='Collect FileInfo')
    parser.add_argument('PATH', action='store', type=str, nargs='*',
                        help='PATH to process')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Increase verbosity")
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
    parser.add_argument('-D', '--non-recursive', action='store_true', default=False,
                        help="Only process given directory")
    parser.add_argument('--debug-sql', action='store_true', default=False,
                        help="Debug SQL queries")
    return parser.parse_args()


def main():
    sb_init()

    args = parse_args()

    cfg = scatterbackup.config.Config()
    cfg.load(args.config)

    if args.dry_run:
        db = NullDatabase()
    else:
        db = Database(args.database or scatterbackup.util.make_default_database(), args.debug_sql)

    gen = db.init_generation(" ".join([shlex.quote(a) for a in sys.argv]))

    try:
        if args.import_file:
            # suspend auto-commit triggering on import
            db.max_insert_count = None
            db.max_insert_size = None

            with scatterbackup.sbtr.open_sbtr(args.import_file) as fin:
                i = 0
                for line in fin:
                    if i % 10000 == 0:
                        print("{} entries imported".format(i))
                    fileinfo = scatterbackup.FileInfo.from_json(line)
                    db.store(fileinfo)
                    i += 1
                print("{} entries imported".format(i))
        else:
            for path in (os.path.abspath(d) for d in args.PATH):
                update = UpdateAction(db)

                update.verbose = args.verbose
                update.checksums = not args.no_checksum
                update.relative = args.relative if args.prefix is None else True
                update.prefix = args.prefix
                update.excludes = cfg.excludes

                update.process_path(path, not args.non_recursive)

        db.deinit_generation(gen)
        db.commit()

    except KeyboardInterrupt:
        print("KeyboardInterrupt received, shutting down")
        # FIXME: Write a continuation point here
        db.commit()


# EOF #
