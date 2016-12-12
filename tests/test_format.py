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
from scatterbackup.format import FileInfoFormater, Bytes


class FormatTestCase(unittest.TestCase):

    def test_bytes(self):
        b = Bytes(592023984)
        self.assertEqual("592.02MB", "{::MB}".format(b))
        self.assertEqual("564.60MiB", "{::MiB}".format(b))
        self.assertEqual("   564.60MiB", "{:>12:MiB}".format(b))
        self.assertEqual("    592.02MB", "{:>12:h}".format(b))
        self.assertEqual("592023984B", "{::B}".format(b))
        self.assertEqual("592023984", "{::r}".format(b))
        self.assertEqual("592.02MB", "{}".format(b))

    # def test_format(self):
    #     fi_map = FileInfoFormater(None)
    #     self.assertEqual("592.02MB", "{size::MB}".format_map(fi_map))
    #     self.assertEqual("551.37MiB", "{size::MiB}".format_map(fi_map))
    #     self.assertEqual("   551.37MiB", "{size:>12:MiB}".format_map(fi_map))


# EOF #
