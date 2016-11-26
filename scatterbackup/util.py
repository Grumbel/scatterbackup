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


import io
import os
import sys
import logging
import xdg.BaseDirectory


def sb_init():
    # Python 3.5.2 still doesn't have "surrogateescape" enabled by
    # default on stdout/stderr, so we have to do it manually. Test with:
    #   print(os.fsdecode(b"\xff"))
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, errors="surrogateescape", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, errors="surrogateescape", line_buffering=True)

    logging.basicConfig(level=logging.DEBUG)

def sb_print(*args):
    for i, arg in enumerate(args):
        sys.stdout.buffer.write(os.fsencode(str(arg)))
        if i < len(args) - 1:
            sys.stdout.buffer.write(b' ')
    sys.stdout.buffer.write(b'\n')


def advance_walk_to(walk, directory):
    """Advance the given os.walk() generator to the given directory."""
    # FIXME: implement this
    return walk


def make_default_database():
    cache_dir = make_cache_directory()
    db_file = os.path.join(cache_dir, "database1.sqlite3")
    return db_file


def make_cache_directory():
    cache_dir = os.path.join(xdg.BaseDirectory.xdg_cache_home, "scatterbackup")

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    return cache_dir


def make_config_directory():
    cache_dir = os.path.join(xdg.BaseDirectory.xdg_config_home, "scatterbackup")

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    return cache_dir


# EOF #
