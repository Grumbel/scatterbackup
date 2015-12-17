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
from scatterbackup.fileinfo import FileInfo


class Database:

    def __init__(self, filename):
        self.con = sqlite3.connect(filename)

    def init_tables(self):
        cur = self.con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS fileinfo(" +
                    "id INTEGER PRIMARY KEY, " +
                    "type TEXT, " +
                    "path TEXT, " +

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
                    "(NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (fileinfo.kind,
                     fileinfo.path,
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

    def get_by_path(self, path):
        cur = self.con.cursor()
        cur.execute("SELECT * FROM fileinfo WHERE path = ?", (path,))
        rows = cur.fetchall()
        if len(rows) > 1:
            raise Exception("duplicates in database")
        elif len(rows) == 0:
            return None
        else:
            row = rows[0]
            fileinfo = FileInfo(path)

            # rowid = row[0]
            fileinfo.kind = row[1]
            fileinfo.path = row[2]
            fileinfo.dev = row[3]
            fileinfo.ino = row[4]
            fileinfo.mode = row[5]
            fileinfo.nlink = row[6]
            fileinfo.uid = row[7]
            fileinfo.gid = row[8]
            fileinfo.rdev = row[9]
            fileinfo.size = row[10]
            fileinfo.blksize = row[11]
            fileinfo.blocks = row[12]
            fileinfo.atime = row[13]
            fileinfo.ctime = row[14]
            fileinfo.mtime = row[15]
            fileinfo.time = row[16]

            return fileinfo

    def commit(self):
        self.con.commit()


# EOF #
