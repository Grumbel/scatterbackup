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

import scatterbackup
import scatterbackup.database
import scatterbackup.config
from scatterbackup.units import bytes2human
from scatterbackup.util import sb_init


def parse_args():
    parser = argparse.ArgumentParser(description='Print disk usage')
    parser.add_argument('PATH', action='store', type=str, nargs='*',
                        help='Path to process')
    parser.add_argument('-d', '--database', type=str, default=None,
                        help="Store results in database")
    parser.add_argument('-c', '--config', type=str, default=None,
                        help="Load configuration file")
    parser.add_argument('-s', '--summarize', action='store_true', default=False,
                        help="Only display summary")
    return parser.parse_args()


def main():
    sb_init()

    args = parse_args()

    cfg = scatterbackup.config.Config()
    cfg.load(args.config)

    db = scatterbackup.database.Database(args.database or scatterbackup.util.make_default_database())

    file_count = 0
    total_bytes = 0
    for path in args.PATH:
        path = os.path.abspath(path)
        print(path)
        for fileinfo in db.get_by_glob(path):
            if not args.summarize:
                print("{:10}  {}".format(fileinfo.size, fileinfo.path))
            file_count += 1
            total_bytes += fileinfo.size

    print("Total: {} in {} files".format(bytes2human(total_bytes), file_count))


# EOF #
