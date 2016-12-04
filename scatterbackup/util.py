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


def split(pred, lst):
    """Like filter(), but return two list, first one with the elements
    where pred() is True, second where it is False"""

    lhs = []
    rhs = []

    for el in lst:
        if pred(el):
            lhs.append(el)
        else:
            rhs.append(el)

    return (lhs, rhs)


def full_join(lhs, rhs, key=lambda x: x):
    """Do a full outer join of two lists on key"""

    lhs = sorted(lhs, key=key)
    rhs = sorted(rhs, key=key)

    l = 0
    r = 0

    while l < len(lhs) and r < len(rhs):
        if key(lhs[l]) == key(rhs[r]):
            yield (lhs[l], rhs[r])
            l += 1
            r += 1
        elif key(lhs[l]) < key(rhs[r]):
            yield (lhs[l], None)
            l += 1
        elif key(lhs[l]) > key(rhs[r]):
            yield (None, rhs[r])
            r += 1
        else:
            assert False, "Never reached"

    for i in range(l, len(lhs)):
        yield (lhs[i], None)

    for i in range(r, len(rhs)):
        yield (None, rhs[i])


# EOF #
