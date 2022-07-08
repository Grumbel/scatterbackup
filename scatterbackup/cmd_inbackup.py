# ScatterBackup - A chaotic backup solution
# Copyright (C) 2017 Ingo Ruhnke <grumbel@gmail.com>
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
import os
import sys
import shlex

import scatterbackup
import scatterbackup.util
from scatterbackup.database import Database
from scatterbackup.fileinfo import FileInfo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Check if file is in backup')
    parser.add_argument('FILE', action='store', type=str, nargs='+',
                        help='Files to check')
    parser.add_argument('-b', '--backup', type=str, default=[], action='append',
                        help="Directory that is considered backup")
    parser.add_argument('-d', '--database', type=str, default=None,
                        help="Store results in database")
    return parser.parse_args()


def fileinfos_from_path(db: Database, path: str) -> list[FileInfo]:
    fileinfos: list[FileInfo] = []

    if not os.path.isdir(path):
        print("{}: warning: not a directory, ignoring".format(path), file=sys.stderr)

    for root, dirs, files in os.walk(path):
        for f in files:
            result = list(db.get_by_path(os.path.join(root, f)))
            if result == []:
                print("{}: warning: not in database, ignoring".format(f), file=sys.stderr)
            fileinfos += result

    return fileinfos


def is_in_backup(fileinfo: FileInfo, backup: list[FileInfo]) -> None:
    found = False
    for b in backup:
        assert b.blob is not None
        assert fileinfo.blob is not None
        if b.blob.sha1 == fileinfo.blob.sha1:
            print("mv -vi {} {}".format(shlex.quote(fileinfo.path), "dup/"))
            # print("INBACKUP: {} -> {}".format(fileinfo.path, b.path))
            found = True

    if not found:
        print("NOTINBACKUP: {}".format(fileinfo.path))


def main() -> None:
    scatterbackup.util.sb_init()

    args = parse_args()
    db = Database(args.database or scatterbackup.util.make_default_database())

    files = [os.path.abspath(p) for p in args.FILE]
    fileinfos: list[FileInfo] = []
    for f in files:
        result = list(db.get_by_path(f))
        if result == []:
            print("{}: warning: not in database, ignoring".format(f), file=sys.stderr)
        fileinfos += result

    backup_fileinfos: list[FileInfo] = []
    for p in args.backup:
        backup_fileinfos += fileinfos_from_path(db, os.path.abspath(p))

    for f in fileinfos:
        is_in_backup(f, backup_fileinfos)


# EOF #
