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

from scatterbackup.units import size2bytes


class UnitsTestCase(unittest.TestCase):

    def test_size2bytes(self) -> None:
        # basic units
        self.assertEqual(1234, size2bytes("1234"))

        self.assertEqual(1000**0, size2bytes("1B"))
        self.assertEqual(1000**1, size2bytes("1kB"))
        self.assertEqual(1000**2, size2bytes("1MB"))
        self.assertEqual(1000**3, size2bytes("1GB"))
        self.assertEqual(1000**4, size2bytes("1TB"))
        self.assertEqual(1000**5, size2bytes("1PB"))
        self.assertEqual(1000**6, size2bytes("1EB"))
        self.assertEqual(1000**7, size2bytes("1ZB"))
        self.assertEqual(1000**8, size2bytes("1YB"))

        self.assertEqual(1024**1, size2bytes("1kiB"))
        self.assertEqual(1024**2, size2bytes("1MiB"))
        self.assertEqual(1024**3, size2bytes("1GiB"))
        self.assertEqual(1024**4, size2bytes("1TiB"))
        self.assertEqual(1024**5, size2bytes("1PiB"))
        self.assertEqual(1024**6, size2bytes("1EiB"))
        self.assertEqual(1024**7, size2bytes("1ZiB"))
        self.assertEqual(1024**8, size2bytes("1YiB"))

        # space
        self.assertEqual(5*1024**8, size2bytes(" 5YiB"))
        self.assertEqual(5*1024**8, size2bytes("  5YiB  "))
        self.assertEqual(5*1024**8, size2bytes("5YiB  "))

        # invalid input
        self.assertRaises(Exception, lambda: size2bytes("ABC"))
        self.assertRaises(Exception, lambda: size2bytes("MB"))
        self.assertRaises(Exception, lambda: size2bytes("MB1MB"))
        self.assertRaises(Exception, lambda: size2bytes("1MBa"))
        self.assertRaises(Exception, lambda: size2bytes("1.3.3MB"))


if __name__ == '__main__':
    unittest.main()


# EOF #
