#!/usr/bin/env python3

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

import scatterbackup.vfs
from scatterbackup.fileinfo import FileInfo


class VFSTestCase(unittest.TestCase):

    def test_foobar(self) -> None:
        vfs = scatterbackup.vfs.VFS()
        vfs.add(FileInfo("/foo/bar.txt"))
        vfs.add(FileInfo("/foo/foo.zip"))
        vfs.add(FileInfo("/foo/foo.txt"))
        fileinfos = vfs.get_fileinfos_by_glob("/foo/*.txt")
        self.assertEqual(2, len(fileinfos))


if __name__ == '__main__':
    unittest.main()


# EOF #
