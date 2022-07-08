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


"""The .sbtr file format contains FileInfo objects as newline-delimited JSON
"""


from typing import cast, IO

import sys
import io
import os
import gzip

import scatterbackup
from scatterbackup.generator import generate_fileinfos
from scatterbackup.fileinfo import FileInfo


def open_sbtr(filename: str) -> IO[str]:
    if filename == "-":
        return sys.stdin
    elif filename.endswith(".gz"):
        return io.TextIOWrapper(cast(IO[bytes], gzip.open(filename, "r")))
    else:
        return open(filename, "r")


def fileinfos_from_sbtr(filename: str) -> dict[str, FileInfo]:
    """Read FileInfo objects from .sbtr file or from compressed .sbtr.gz file"""
    result = {}
    with open_sbtr(filename) as fin:
        for line in fin:
            fileinfo = scatterbackup.FileInfo.from_json(line)
            result[fileinfo.path] = fileinfo
    return result


def fileinfos_from_path(path: str, checksums: bool = True, relative: bool = False) -> dict[str, FileInfo]:
    """Read FileInfo objects from path, which can be a .sbtr, .sbtr.gz or directory"""
    if os.path.isdir(path):
        return {fileinfo.path: fileinfo for
                fileinfo in generate_fileinfos(path, checksums=checksums, relative=relative)}
    else:
        # ignoring `checksums` and `relative` here, we have to use
        # what is stored in the .sbtr
        return fileinfos_from_sbtr(path)


# EOF #
