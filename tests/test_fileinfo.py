#!/usr/bin/env python3

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

import unittest
from scatterbackup.fileinfo import FileInfo


class FileInfoTestCase(unittest.TestCase):

    def test_from_file(self):
        fileinfo = FileInfo.from_file("tests/data/test.txt")
        self.assertEqual(11, fileinfo.size)
        self.assertEqual("6df4d50a41a5d20bc4faad8a6f09aa8f", fileinfo.blob.md5)
        self.assertEqual("bc9faaae1e35d52f3dea9651da12cd36627b8403", fileinfo.blob.sha1)

    # def test_json(self):
    #     fileinfo = FileInfo.from_file("tests/test.txt")
    #     jstxt = fileinfo.json()
    #     fileinfo2 = FileInfo.from_json(jstxt)
    #     self.assertEqual(fileinfo, fileinfo2)


if __name__ == '__main__':
    unittest.main()


# EOF #
