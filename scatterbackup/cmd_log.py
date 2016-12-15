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
import datetime
from collections import defaultdict

import scatterbackup.util
import scatterbackup.config
import scatterbackup.database
import scatterbackup.time
from scatterbackup.time import format_time
from scatterbackup.util import sb_init
from scatterbackup.units import bytes2human_decimal
from scatterbackup.generation import GenerationRange
from scatterbackup.format import Time


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


def process_path(db, args, paths, gen_range):
    path_globs = [os.path.join(os.path.abspath(path), "*") for path in paths]

    dbrange = db.get_generations_range()
    gen_range.clip_to(dbrange)

    for gen in range(gen_range.start, gen_range.end):
        grange = GenerationRange(gen, gen+1, GenerationRange.INCLUDE_CHANGED)

        generation = db.get_generations(grange)[0]

        fileinfos = db.get_by_glob(path_globs, grange)

        group_by_path = defaultdict(list)
        for f in (j for j in fileinfos if j.kind != "directory"):
            group_by_path[f.path].append(f)

        if group_by_path == {}:
            pass
        else:
            print("\n-- generation {}: [{} - {}] - {}"
                  .format(gen,
                          Time(generation.start_time),
                          Time(generation.end_time),
                          generation.command))

            for p, group in group_by_path.items():
                fileinfo = group[-1]

                if len(group) > 1:
                    status = "changed"
                elif fileinfo.birth == gen:
                    status = "added"
                elif fileinfo.death == gen:
                    status = "deleted"

                # TODO: make summary of changes:
                # compare(group[0], group[1])

                # TODO: insert rename detection

                print("{:8} {:>10}  {}  {}"
                      .format(status,
                              # fileinfo.ino,
                              bytes2human_decimal(fileinfo.size),
                              fileinfo.blob and fileinfo.blob.sha1,
                              fileinfo.path))


def print_generations(db, args, gen_range):
    generations = db.get_generations(gen_range)
    for gen in generations:
        print("{}  {}  {}  {}  {}".format(gen.generation,
                                          format_time(gen.start_time),
                                          format_time(gen.end_time),
                                          (datetime.timedelta(microseconds=(gen.end_time - gen.start_time) / 1000)
                                           if gen.start_time is not None and gen.end_time is not None
                                           else "  <unknown>   "),
                                          gen.command))


def main():
    sb_init()

    args = parse_args()

    cfg = scatterbackup.config.Config()
    cfg.load(args.config)

    db = scatterbackup.database.Database(args.database or scatterbackup.util.make_default_database())

    gen_range = GenerationRange.from_string(args.generation)

    if args.PATH == []:
        print_generations(db, args, gen_range)
    else:
        process_path(db, args, args.PATH, gen_range)


# EOF #
