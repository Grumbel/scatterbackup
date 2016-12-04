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
from scatterbackup.generator import generate_fileinfos, scan_directory, scan_fileinfos


class GeneratorTestCase(unittest.TestCase):

    def test_generator(self):
        output = ""
        for fileinfo in generate_fileinfos("tests/"):
            output += fileinfo.json()
        # FIXME: insert some proper check for validity
        self.assertTrue(True)

    def test_scan_directory(self):
        for root, dirs, files in scan_directory("tests/data/"):
            print(root)

    def test_scan_fileinfos(self):
        # pylint: disable=locally-disabled, no-self-use
        for root, dirs, files in scan_fileinfos("tests/data/"):
            for d in dirs:
                print(d.json())
            for f in files:
                print(f.json())


if __name__ == '__main__':
    unittest.main()


# EOF #
