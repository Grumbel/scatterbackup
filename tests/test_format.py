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


import unittest

from scatterbackup.fileinfo import FileInfo
from scatterbackup.format import FileInfoFormatter, Bytes


class FormatTestCase(unittest.TestCase):

    def test_bytes(self) -> None:
        b = Bytes(592023984)
        self.assertEqual("592.02MB", "{::MB}".format(b))
        self.assertEqual("564.60MiB", "{::MiB}".format(b))
        self.assertEqual("   564.60MiB", "{:>12:MiB}".format(b))
        self.assertEqual("    592.02MB", "{:>12:h}".format(b))
        self.assertEqual("592023984B", "{::B}".format(b))
        self.assertEqual("592023984", "{::r}".format(b))
        self.assertEqual("592.02MB", "{}".format(b))
        self.assertEqual("564.60MiB", "{::H}".format(b))

    def test_format(self) -> None:
        fileinfo = FileInfo.from_file("tests/data/test.txt")
        fi_map = FileInfoFormatter(fileinfo)
        self.assertEqual("0.00MB", "{size::MB}".format_map(fi_map))
        self.assertEqual("6df4d50a41a5d20bc4faad8a6f09aa8f", "{md5}".format_map(fi_map))


# EOF #
