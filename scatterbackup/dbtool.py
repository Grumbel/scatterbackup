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


import logging
import argparse

import scatterbackup.diff
import scatterbackup.database


def main():
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(description='scatterbackup database tool')
    parser.add_argument('DATABASE', action='store', type=str, nargs=1,
                        help='database file to load')
    parser.add_argument('-i', '--import', action='store', type=str, dest="import_file",
                        help='.sbtr file to import')
    args = parser.parse_args()

    db = scatterbackup.database.Database(args.DATABASE[0])

    if args.import_file is not None:
        logging.info("loading %s", args.import_file)
        fileinfos = scatterbackup.diff.fileinfos_from_file(args.import_file)
        logging.info("%s: %d entries loaded", args.import_file, len(fileinfos))
        for k, v in fileinfos.items():
            db.store(v)
        logging.info("database commit")
        db.commit()


# EOF #
