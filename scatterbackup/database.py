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

import sqlite3


class Database:

    def __init__(self):
        self.sql = sqlite3.connect('/tmp/scatterbackup.sqlite3')

    def init_tables(self):
        c = self.sql.cursor()
        c.execute("CREATE TABLE fileinfo(path TEXT, host TEXT, md5 TEXT, sha1 TEXT, mtime TEXT, size INTEGER)")

    def store(self, fileinfo):
        pass

# EOF #
