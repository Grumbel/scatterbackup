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


import os
import unittest

from scatterbackup.database import Database
from scatterbackup.fileinfo import FileInfo
from scatterbackup.generation import GenerationRange


class DatabaseTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.db = Database(":memory:")
        self.db.init_tables()
        self.db.store(FileInfo.from_file("tests/data/test.txt"))
        self.db.store(FileInfo.from_file("tests/data/symlink.lnk"))
        self.db.store(FileInfo.from_file("tests/data/subdir/test.txt"))

    def tearDown(self) -> None:
        del self.db

    def test_get_by_path(self) -> None:
        fileinfo = self.db.get_one_by_path(os.path.abspath("tests/data/test.txt"))
        assert fileinfo is not None
        self.assertEqual(fileinfo.path, os.path.abspath("tests/data/test.txt"))
        self.assertIsNone(self.db.get_one_by_path(os.path.abspath("non-existing-file.txt")))

    def test_get_directory_by_path(self) -> None:
        fileinfos = list(self.db.get_directory_by_path(os.path.abspath("tests/data/")))
        self.assertEqual(len(fileinfos), 2)
        self.assertEqual(fileinfos[0].path, os.path.abspath("tests/data/test.txt"))
        self.assertEqual(fileinfos[1].path, os.path.abspath("tests/data/symlink.lnk"))

    def test_get_duplicates(self) -> None:
        results = list(self.db.get_duplicates(os.path.abspath("tests/data/")))
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]), 2)
        results[0].sort(key=lambda fi: fi.path)
        self.assertEqual(results[0][0].path, os.path.abspath("tests/data/subdir/test.txt"))
        self.assertEqual(results[0][1].path, os.path.abspath("tests/data/test.txt"))

    def test_get_by_glob(self) -> None:
        results = list(self.db.get_by_glob(os.path.abspath("tests/*.txt")))
        self.assertEqual(len(results), 2)
        results.sort(key=lambda fi: fi.path)
        self.assertEqual(results[0].path, os.path.abspath("tests/data/subdir/test.txt"))
        self.assertEqual(results[1].path, os.path.abspath("tests/data/test.txt"))

        # check for cursor reuse
        gen = self.db.get_by_glob(os.path.abspath("tests/*.txt"))
        gen2 = self.db.get_by_glob(os.path.abspath("tests/*.txt"))
        next(gen)
        next(gen2)
        next(gen)  # this will throw if the generator gets invalidaded by cursor reuse

    def test_get_all(self) -> None:
        results = list(self.db.get_all())
        self.assertEqual(len(results), 3)

    def test_get_generation(self) -> None:
        gens = self.db.get_generations(GenerationRange(0, 100))
        self.assertEqual(len(gens), 0)


if __name__ == '__main__':
    unittest.main()


# EOF #
