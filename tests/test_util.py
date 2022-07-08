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

from scatterbackup.util import full_join, split


class UtilTestCase(unittest.TestCase):

    def test_split(self) -> None:
        lst = [2, 1, 4, 3, 5]
        result = split(lambda x: x < 4, lst)
        self.assertEqual(result[0], [2, 1, 3])
        self.assertEqual(result[1], [4, 5])

    def test_full_join(self) -> None:
        lhs = [2, 1, 4, 3, 5]
        rhs = [7, 5, 4, 6, 3]
        result = list(full_join(lhs, rhs))
        expected = [(1, None),
                    (2, None),
                    (3, 3),
                    (4, 4),
                    (5, 5),
                    (None, 6),
                    (None, 7)]
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()


# EOF #
