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


import sys
import io
import gzip
import scatterbackup

"""The .sbtr file format contains FileInfo objects as newline-delimited JSON
"""


def open_sbtr(filename):
    if filename == "-":
        return sys.stdin
    elif filename.endswith(".gz"):
        return io.TextIOWrapper(gzip.open(filename, "r"))
    else:
        return open(filename, "r")


def fileinfos_from_sbtr(filename):
    result = {}
    with open_sbtr(filename) as fin:
        for line in fin:
            fileinfo = scatterbackup.FileInfo.from_json(line)
            result[fileinfo.path] = fileinfo
    return result


# EOF #
