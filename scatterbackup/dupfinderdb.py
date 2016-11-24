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
import os

import scatterbackup
import scatterbackup.util
from scatterbackup.generator import generate_fileinfos
from scatterbackup.vfs import VFS
from scatterbackup.database import Database, NullDatabase


def parse_args():
    parser = argparse.ArgumentParser(description='Find duplicate files')
    parser.add_argument('DIRECTORY', action='store', type=str, nargs=1,
                        help='directory containing the filese')
    parser.add_argument('-d', '--database', type=str, default=None,
                        help="Store results in database")
    return parser.parse_args()


def main():
    args = parse_args()
    db = Database(args.database or scatterbackup.util.make_default_database())
    path = os.path.abspath(args.DIRECTORY[0])
    duplicates = db.get_duplicates(path)
    for dups in duplicates:
        for dup in dups:
            print(dup[0], dup[1])
        print()


# EOF #