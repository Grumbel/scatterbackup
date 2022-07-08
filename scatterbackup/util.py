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


from typing import Any, Callable, Sequence, TypeVar, Iterator, Optional

import io
import os
import sys
import logging
import xdg.BaseDirectory


T = TypeVar('T')


def sb_init() -> None:
    # Python 3.5.2 still doesn't have "surrogateescape" enabled by
    # default on stdout/stderr, so we have to do it manually. Test with:
    #   print(os.fsdecode(b"\xff"))
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors="surrogateescape", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors="surrogateescape", line_buffering=True)

    logging.basicConfig(level=logging.DEBUG)


def make_default_database() -> str:
    cache_dir = make_cache_directory()
    db_file = os.path.join(cache_dir, "database1.sqlite3")
    return db_file


def make_cache_directory() -> str:
    cache_dir = os.path.join(xdg.BaseDirectory.xdg_data_home, "scatterbackup")

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    return cache_dir


def make_config_directory() -> str:
    cache_dir = os.path.join(xdg.BaseDirectory.xdg_config_home, "scatterbackup")

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    return cache_dir


def split(pred: Callable[[T], bool], lst: Sequence[T]) -> tuple[list[T], list[T]]:
    """Like filter(), but return two list, first one with the elements
    where pred() is True, second where it is False"""

    lhs: list[Any] = []
    rhs: list[Any] = []

    for el in lst:
        if pred(el):
            lhs.append(el)
        else:
            rhs.append(el)

    return (lhs, rhs)


def full_join(lhs: Sequence[T], rhs: Sequence[T],
              key: Callable[[T], Any] = lambda x: x) -> Iterator[tuple[Optional[T], Optional[T]]]:
    """Do a full outer join of two lists on key"""

    lhs = sorted(lhs, key=key)
    rhs = sorted(rhs, key=key)

    lhs_idx = 0
    rhs_idx = 0

    while lhs_idx < len(lhs) and rhs_idx < len(rhs):
        if key(lhs[lhs_idx]) == key(rhs[rhs_idx]):
            yield (lhs[lhs_idx], rhs[rhs_idx])
            lhs_idx += 1
            rhs_idx += 1
        elif key(lhs[lhs_idx]) < key(rhs[rhs_idx]):
            yield (lhs[lhs_idx], None)
            lhs_idx += 1
        elif key(lhs[lhs_idx]) > key(rhs[rhs_idx]):
            yield (None, rhs[rhs_idx])
            rhs_idx += 1
        else:
            assert False, "Never reached"

    for i in range(lhs_idx, len(lhs)):
        yield (lhs[i], None)

    for i in range(rhs_idx, len(rhs)):
        yield (None, rhs[i])


# EOF #
