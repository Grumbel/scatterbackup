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
import scatterbackup.util
from scatterbackup.util import sb_init
from scatterbackup.database import Database


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Compare two .sbtr files')
    parser.add_argument('-d', '--database', type=str, default=None,
                        help="Store results in database")
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="Be more verbose")
    parser.add_argument('--rebuild-directory-table', action='store_true', default=False,
                        help="Rebuild directory table")
    parser.add_argument('--cleanup-double-alive', action='store_true', default=False,
                        help="Cleanup double-alive FileInfos")
    parser.add_argument('--rebuild-indices', action='store_true', default=False,
                        help="Rebuild indices")
    parser.add_argument('--vacuum', action='store_true', default=False,
                        help="Call vacuum on the database")
    return parser.parse_args()


def main() -> None:
    sb_init()
    args = parse_args()
    db = Database(args.database or scatterbackup.util.make_default_database())

    db_changed = False
    if args.rebuild_directory_table:
        db.rebuild_directory_table()
        db_changed = True

    if args.cleanup_double_alive:
        db.cleanup_double_alive()
        db_changed = True

    if args.rebuild_indices:
        db.rebuild_indices()
        db_changed = True

    if args.vacuum:
        db.vacuum()
        db_changed = True

    if db_changed:
        db.commit()
    else:
        db.fsck()


# EOF #
