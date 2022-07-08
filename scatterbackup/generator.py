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


from typing import cast, Callable, Iterator, Optional, Sequence

import os
import fnmatch
import logging

import scatterbackup
from scatterbackup.fileinfo import FileInfo


def match_excludes(path: str, excludes: Optional[Sequence[str]] = None) -> bool:
    if excludes is not None:
        for pattern in excludes:
            if fnmatch.fnmatch(path, pattern):
                return True
    return False


def scan_directory(path: str,
                   excludes: Optional[list[str]] = None,
                   onerror: Optional[Callable[[OSError], None]] = None) -> Iterator[tuple[str, list[str], list[str]]]:
    """Wrapper around scatterbackup.walk() that applies a list of exclude
    directives and returns result as absolute path
    """
    if excludes is None:
        excludes = []

    path = os.path.abspath(path)

    for root, dirs, files in scatterbackup.walk(path, onerror=onerror):
        result_dirs = []
        result_files = []

        off = 0
        for i, f in enumerate(dirs[:]):
            try:
                path = os.path.join(root, f)
                if not match_excludes(path, excludes):
                    result_dirs.append(path)
                else:
                    logging.info("excluding %s", path)
                    del dirs[i - off]
                    off += 1
            except OSError as err:
                if onerror is not None:
                    onerror(err)

        for f in files:
            try:
                path = os.path.join(root, f)
                if not match_excludes(path, excludes):
                    result_files.append(path)
            except OSError as err:
                if onerror is not None:
                    onerror(err)  # type: ignore

        yield (cast(str, root), result_dirs, result_files)


def scan_fileinfos(path: str,
                   excludes: Optional[list[str]] = None,
                   checksums: bool = False,
                   relative: bool = False,
                   onerror: Optional[Callable[[OSError], None]] = None) \
                   -> Iterator[tuple[str, list[FileInfo], list[FileInfo]]]:

    for root, dirs, files in scan_directory(path, excludes, onerror):
        result_dirs = []
        for d in dirs:
            try:
                result_dirs.append(FileInfo.from_file(d, checksums=checksums, relative=relative))
            except OSError as err:
                if onerror is not None:
                    onerror(err)

        result_files = []
        for f in files:
            try:
                result_files.append(FileInfo.from_file(f, checksums=checksums, relative=relative))
            except OSError as err:
                if onerror is not None:
                    onerror(err)  # type: ignore

        yield (root, result_dirs, result_files)


def generate_files(path: str,
                   excludes: Optional[Sequence[str]] = None,
                   onerror: Optional[Callable[[OSError], None]] = None) -> Iterator[str]:
    """Generate a list of files and directories below path"""

    yield path

    if os.path.isdir(path):
        for root, dirs, files in scatterbackup.walk(path, onerror=onerror):
            off = 0
            for i, f in enumerate(dirs[:]):
                try:
                    path = os.path.normpath(os.path.join(root, f))
                    if not match_excludes(path, excludes):
                        yield path
                    else:
                        logging.info("excluding %s", path)
                        del dirs[i - off]
                        off += 1
                except OSError as err:
                    if onerror is not None:
                        onerror(err)

            for f in files:
                try:
                    path = os.path.normpath(os.path.join(root, f))
                    if not match_excludes(path, excludes):
                        yield path
                except OSError as err:
                    if onerror is not None:
                        onerror(err)  # type: ignore


def generate_fileinfos(path: str,
                       relative: bool = False,
                       prefix: Optional[str] = None,
                       onerror: Optional[Callable[[OSError], None]] = None,
                       excludes: Optional[Sequence[str]] = None,
                       checksums: bool = False) -> Iterator[FileInfo]:

    for p in generate_files(path=path, onerror=onerror, excludes=excludes):
        try:
            fileinfo = FileInfo.from_file(p,
                                          checksums=checksums,
                                          relative=relative)
            if prefix is not None:
                fileinfo.path = os.path.join(prefix, fileinfo.path)

            yield fileinfo

        except OSError as err:
            if onerror is not None:
                onerror(err)


# EOF #
