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

from scatterbackup.generation import GenerationRange


class GeneratorTestCase(unittest.TestCase):

    def test_generation_range(self):
        self.assertEqual(GenerationRange.from_string("10:20"), GenerationRange(10, 20))
        self.assertEqual(GenerationRange.from_string(":20"), GenerationRange(None, 20))
        self.assertEqual(GenerationRange.from_string("10:"), GenerationRange(10, None))
        self.assertEqual(GenerationRange.from_string(":"), GenerationRange.MATCH_ALL)
        self.assertEqual(GenerationRange.from_string(""), GenerationRange.MATCH_ALL)
        self.assertRaises(Exception, lambda: GenerationRange.from_string("ERROR"))
        self.assertRaises(Exception, lambda: GenerationRange.from_string("ERROR:"))
        self.assertRaises(Exception, lambda: GenerationRange.from_string(":ERROR"))


if __name__ == '__main__':
    unittest.main()


# EOF #
