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
from scatterbackup import BlobInfo


class BlobInfoTestCase(unittest.TestCase):

    def test_from_file(self):
        blobinfo = BlobInfo.from_file("tests/data/test.txt")
        self.assertEqual(11, blobinfo.size)
        self.assertEqual("6df4d50a41a5d20bc4faad8a6f09aa8f", blobinfo.md5)
        self.assertEqual("bc9faaae1e35d52f3dea9651da12cd36627b8403", blobinfo.sha1)
        self.assertEqual(460961799, blobinfo.crc32)


if __name__ == '__main__':
    unittest.main()


# EOF #
