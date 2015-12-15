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

    def __init__(self, filename):
        self.con = sqlite3.connect(filename)

    def init_tables(self):
        cur = self.con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS fileinfo(" +
                    "id INTEGER PRIMARY KEY, " +
                    "type TEXT, " +
                    "path TEXT, " +
                    "host TEXT, " +

                    "dev INTEGER, " +
                    "ino INTEGER, " +

                    "mode INTEGER, " +
                    "nlink INTEGER, " +

                    "uid INTEGER, " +
                    "gid INTEGER, " +

                    "rdev INTEGER, " +

                    "size INTEGER, " +
                    "blksize INTEGER, " +
                    "blocks INTEGER, " +

                    "atime INTEGER, " +
                    "ctime INTEGER, " +
                    "mtime INTEGER, " +

                    "time INTEGER" +

                    ")")

        cur.execute("CREATE TABLE IF NOT EXISTS blobinfo(" +
                    "id INTEGER PRIMARY KEY, " +
                    "fileinfo_id INTEGER, " +
                    "size INTEGER, " +
                    "md5 TEXT, " +
                    "sha1 TEXT" +
                    ")")

        cur.execute("CREATE TABLE IF NOT EXISTS linkinfo(" +
                    "id INTEGER PRIMARY KEY, " +
                    "fileinfo_id INTEGER, " +
                    "target TEXT " +
                    ")")

    def store(self, fileinfo):
        print("store...", fileinfo.path)
        cur = self.con.cursor()
        cur.execute("INSERT INTO fileinfo VALUES" +
                    "(NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (fileinfo.kind,
                     fileinfo.path,
                     fileinfo.host,
                     fileinfo.dev,
                     fileinfo.ino,
                     fileinfo.mode,
                     fileinfo.nlink,
                     fileinfo.uid,
                     fileinfo.gid,
                     fileinfo.rdev,
                     fileinfo.size,
                     fileinfo.blksize,
                     fileinfo.blocks,
                     fileinfo.atime,
                     fileinfo.ctime,
                     fileinfo.mtime,
                     fileinfo.time))

        fileinfo_id = cur.lastrowid

        if fileinfo.blob is not None:
            cur.execute("INSERT INTO blobinfo VALUES" +
                        "(NULL, ?, ?, ?, ?)",
                        (fileinfo_id, fileinfo.blob.size, fileinfo.blob.md5, fileinfo.blob.sha1))

        if fileinfo.target is not None:
            cur.execute("INSERT INTO linkinfo VALUES" +
                        "(NULL, ?, ?)",
                        (fileinfo_id, fileinfo.target))

    def commit(self):
        self.con.commit()


# EOF #
