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
import re
import argparse
import datetime
import scatterbackup.util
import scatterbackup.config
import scatterbackup.database
import scatterbackup.time
from scatterbackup.time import format_time
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
    parser.add_argument('-g', '--generation', type=str, default=None,
                        help="Generations to list")
    return parser.parse_args()


def process_path(db, args):
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


def print_generations(db, args, start, end):
    generations = db.get_generations(start, end)
    for gen in generations:
        print("{}  {}  {}  {}  {}".format(gen.generation,
                                          format_time(gen.start_time),
                                          format_time(gen.end_time),
                                          (datetime.timedelta(microseconds=(gen.end_time - gen.start_time) / 1000)
                                           if gen.start_time is not None and gen.end_time is not None
                                           else "  <unknown>   "),
                                          gen.command))


def parse_generation(text):
    start = None
    end = None

    if text:
        text = text.strip()
        m = re.match(r"^([0-9]+):([0-9]+)$", text)
        if m:
            start, end = m.groups()
        else:
            m = re.match(r"^([0-9]+):$", text)
            if m:
                start, = m.groups()
            else:
                m = re.match(r"^:([0-9]+)$", text)
                if m:
                    end, = m.groups()
                    start = "1"
                else:
                    m = re.match(r"^([0-9]+)$", text)
                    if m:
                        start, = m.groups()
                        end = str(int(start) + 1)
                    else:
                        raise Exception("invalid generation string: {}".format(text))

        start = int(start) if start else None
        end = int(end) if end else None

        if start is not None and end is not None and start >= end:
            raise Exception("invalid generation range: {}-{}".format(start, end))

    return (start, end)


def main():
    sb_init()

    args = parse_args()

    cfg = scatterbackup.config.Config()
    cfg.load(args.config)

    db = scatterbackup.database.Database(args.database or scatterbackup.util.make_default_database())

    if args.PATH == []:
        start, end = parse_generation(args.generation)
        print_generations(db, args, start, end)
    else:
        process_path(db, args)


# EOF #
