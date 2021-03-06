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
import logging
import itertools
from collections import defaultdict

import scatterbackup.util
import scatterbackup.config
import scatterbackup.database
import scatterbackup.time
from scatterbackup.time import format_time
from scatterbackup.util import sb_init, split
from scatterbackup.units import bytes2human_decimal
from scatterbackup.generation import GenerationRange
from scatterbackup.format import Time, Bytes


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


def compare_fileinfo(old, new):
    changes = []

    if old.kind != new.kind:
        changes.append("type: {} -> {}".format(old.kind, new.kind))

    if old.ino != new.ino:
        changes.append("ino: {} -> {}".format(old.ino, new.ino))

    if old.mode != new.mode:
        changes.append("mode: {} -> {}".format(old.mode, new.mode))

    if old.nlink != new.nlink:
        changes.append("nlink: {} -> {}".format(old.nlink, new.nlink))

    if old.uid != new.uid:
        changes.append("uid: {} -> {}".format(old.uid, new.uid))

    if old.gid != new.gid:
        changes.append("gid: {} -> {}".format(old.gid, new.gid))

    if old.size != new.size:
        bytes_diff = new.size - old.size
        if bytes_diff < 0:
            sign = "-"
        else:
            sign = "+"
        changes.append("size: {}{}".format(sign, Bytes(abs(bytes_diff))))

    if old.blksize != new.blksize:
        changes.append("blksize: {}".format(new.blksize - old.blksize))

    if old.blocks != new.blocks:
        changes.append("blocks: {}".format(new.blocks - old.blocks))

    # to much noise
    # if old.atime != new.atime:
    #    changes.append("atime: {} -> {}".format(Time(old.atime), Time(new.atime)))

    if old.ctime != new.ctime:
        changes.append("ctime: {} -> {}".format(Time(old.ctime), Time(new.ctime)))

    if old.mtime != new.mtime:
        changes.append("mtime: {} -> {}".format(Time(old.mtime), Time(new.mtime)))

    # self.blob = None
    # self.target = None

    return ", ".join(changes)


def gather_changed(fileinfos):
    by_path = defaultdict(list)
    for fi in fileinfos:
        by_path[fi.path].append(fi)

    changed, rest = split(lambda fs: len(fs) != 1,
                          by_path.values())
    rest = [fi[0] for fi in rest]

    results = []
    for group in changed:
        old = min(group, key=lambda fi: fi.birth)
        new = max(group, key=lambda fi: fi.birth)
        results.append((old, new, compare_fileinfo(old, new)))

    return results, rest


def gather_renamed(fileinfos):
    by_ino = defaultdict(list)
    for fi in fileinfos:
        by_ino[fi.ino].append(fi)

    renamed, rest = split(lambda fs: len(fs) != 1,
                          by_ino.values())
    rest = [fi[0] for fi in rest]

    results = []
    for group in renamed:
        old = min(group, key=lambda fi: fi.birth)
        new = max(group, key=lambda fi: fi.birth)
        results.append((old, new))

    return results, rest


def gather_added_deleted(fileinfos, gen):
    return split(lambda fs: fs.birth == gen,
                 fileinfos)


def build_report(fileinfos, gen):
    changed, fileinfos = gather_changed(fileinfos)
    renamed, fileinfos = gather_renamed(fileinfos)
    added, deleted = gather_added_deleted(fileinfos, gen)

    report = itertools.chain(
        (("deleted", g) for g in deleted),
        (("changed", g) for g in changed),
        (("renamed", g) for g in renamed),
        (("added", g) for g in added))

    return report


def print_report(report):
    report = sorted(report, key=lambda g: g[1][0].path if isinstance(g[1], tuple) else g[1].path)

    for status, g in report:
        if status == "changed":
            if g[0].blob == g[1].blob:
                # skip files that have the same content, make this an
                # option
                pass
            else:
                print_fileinfo(status, g[0])
                print_fileinfo("  to", g[1])
                print("  ", g[2])
        elif status == "renamed":
            print_fileinfo(status, g[0])
            print_fileinfo("  to", g[1])
        elif status == "added":
            print_fileinfo(status, g)
        elif status == "deleted":
            print_fileinfo(status, g)
        else:
            logging.error("unknown status: '%s' for %s", status, g)


def print_fileinfo(status, fileinfo):
    print("{:8} {:>10}  {}  {}"
          .format(status,
                  # fileinfo.ino,
                  bytes2human_decimal(fileinfo.size),
                  fileinfo.blob and fileinfo.blob.sha1,
                  fileinfo.path))


def path_to_glob(path):
    # FIXME: This heuristic to automatically generate a pattern for
    # the database query is a bit primitive
    if os.path.isdir(path):
        return os.path.join(path, "*")
    else:
        return path


def process_path(db, args, paths, gen_range):
    path_globs = [path_to_glob(os.path.abspath(path)) for path in paths]

    for gen in range(gen_range.start, gen_range.end):
        grange = GenerationRange(gen, gen+1, GenerationRange.INCLUDE_CHANGED)

        generation = db.get_generations(grange)[0]

        fileinfos = list(db.get_by_glob(path_globs, grange))

        # TODO: filter directory entries by default, might be a good
        # idea to make this an option
        fileinfos = [fi for fi in fileinfos if fi.kind != "directory"]

        if fileinfos == []:
            pass
        else:
            print("\n-- generation {}: [{} - {}] - {}"
                  .format(gen,
                          Time(generation.start_time),
                          Time(generation.end_time),
                          generation.command))
            report = build_report(fileinfos, gen)
            print_report(report)


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

    dbrange = db.get_generations_range()
    gen_range = GenerationRange.from_string(args.generation, dbrange)

    if args.PATH == []:
        print_generations(db, args, gen_range)
    else:
        process_path(db, args, args.PATH, gen_range)


# EOF #
