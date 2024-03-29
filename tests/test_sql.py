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

from scatterbackup.sql import WHERE, AND, OR


class SQLTestCase(unittest.TestCase):

    def test_sql(self) -> None:
        self.assertEqual(WHERE(""), "")
        self.assertEqual(WHERE("1 < 2"), "WHERE 1 < 2")

        self.assertEqual(AND(), "")
        self.assertEqual(WHERE(AND("1 < 2", "3 < 10")), "WHERE (1 < 2) AND (3 < 10)")

        self.assertEqual(OR(), "")
        self.assertEqual(WHERE(OR("1 < 2", "3 < 10")), "WHERE (1 < 2) OR (3 < 10)")


if __name__ == '__main__':
    unittest.main()


# EOF #
