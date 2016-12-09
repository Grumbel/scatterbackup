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

import scatterbackup


class UtilTestCase(unittest.TestCase):

    def test_walk(self):
        result = list(scatterbackup.walk("tests/data"))
        expected = [('tests/data',
                     ['subdir'],
                     ['test.txt', 'symlink.lnk']),
                    ('tests/data/subdir',
                     [],
                     ['test.txt'])]
        self.assertListEqual(result, expected)


if __name__ == '__main__':
    unittest.main()


# EOF #
