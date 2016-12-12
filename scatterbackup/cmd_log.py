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


import os
import argparse
import scatterbackup.util
import scatterbackup.config
import scatterbackup.database
import scatterbackup.time
from scatterbackup.util import sb_init
from scatterbackup.units import bytes2human_decimal


def parse_args():
    parser = argparse.ArgumentParser(description='Collect FileInfo')
    parser.add_argument('PATH', action='store', type=str, nargs='*',
                        help='PATH to log')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="be more verbose")
    parser.add_argument('-q', '--quiet', action='store_true', default=False,
                        help="be less verbose")
    parser.add_argument('-d', '--database', type=str, default=None,
                        help="Store results in database")
    parser.add_argument('-c', '--config', type=str, default=None,
                        help="Load configuration file")
    parser.add_argument('-r', '--recursive', type=str, default=None,
                        help="Recursivly process all subdirectories")
    return parser.parse_args()


def main():
    sb_init()

    args = parse_args()

    cfg = scatterbackup.config.Config()
    cfg.load(args.config)

    db = scatterbackup.database.Database(args.database or scatterbackup.util.make_default_database())

    for path in args.PATH:
        path = os.path.abspath(path)
        fileinfos = db.get_by_path(path, all_matches=True)
        if fileinfos is None:
            print("{}: error: path not found".format(path))
        else:
            fileinfos = sorted(fileinfos, key=lambda fileinfo: fileinfo.birth)

            for fileinfo in fileinfos:
                print("{:18} {!r:>5}  {!r:>5}  {!r:>10}  {:>10}  {}  {}"
                      .format(scatterbackup.time.format_time(fileinfo.time),
                              fileinfo.birth,
                              fileinfo.death,
                              fileinfo.ino,
                              bytes2human_decimal(fileinfo.size),
                              fileinfo.blob and fileinfo.blob.sha1,
                              fileinfo.path))

            # http://svnbook.red-bean.com/en/1.7/svn.ref.svn.c.log.html


# EOF #
