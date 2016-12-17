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
import os
import scatterbackup.sbtr
from scatterbackup.util import sb_init
from scatterbackup.database import Database


def path_excluded(path, excludes):
    for ex in excludes:
        if path.startswith(ex):
            return True
    return False


def diff(db, oldpath, newpath, excludes, verbose=False):
    oldglob = os.path.join(oldpath, '*')
    newglob = os.path.join(newpath, '*')

    oldfileinfos = db.get_by_glob(oldglob)

    for oldfileinfo in oldfileinfos:
        path = os.path.relpath(oldfileinfo.path, oldpath)

        if path_excluded(path, excludes):
            continue

        newfileinfo = db.get_one_by_path(os.path.join(newpath, path))
        if newfileinfo is None:
            print("removed {}".format(path))
        else:
            if oldfileinfo.blob == newfileinfo.blob:
                if verbose:
                    print("ok {}".format(path))
            else:
                print("modified {}".format(path))

    newfileinfos = db.get_by_glob(newglob)
    for newfileinfo in newfileinfos:
        path = os.path.relpath(newfileinfo.path, newpath)

        if path_excluded(path, excludes):
            continue

        oldfileinfo = db.get_one_by_path(os.path.join(oldpath, path))

        if oldfileinfo is None:
            print("added {}".format(path))


def parse_args():
    parser = argparse.ArgumentParser(description='Compare two .sbtr files')
    parser.add_argument('OLDPATH', action='store', type=str, nargs=1,
                        help='old subtree')
    parser.add_argument('NEWPATH', action='store', type=str, nargs=1,
                        help='new subtree')
    parser.add_argument('-d', '--database', type=str, default=None,
                        help="Store results in database")
    parser.add_argument('-e', '--exclude', type=str, action='append', default=[],
                        help="Subpath to exclude")
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="Be more verbose")
    return parser.parse_args()


def main():
    sb_init()
    args = parse_args()
    db = Database(args.database or scatterbackup.util.make_default_database())
    diff(db,
         os.path.abspath(args.OLDPATH[0]),
         os.path.abspath(args.NEWPATH[0]),
         [os.path.normpath(p) + "/" for p in args.exclude],
         args.verbose)


# EOF #
