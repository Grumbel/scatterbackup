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
import sqlite3
import time
from scatterbackup.fileinfo import FileInfo
from scatterbackup.blobinfo import BlobInfo
from collections import defaultdict

def fileinfo_from_row(row):
    fileinfo = FileInfo(row[2])

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

    if len(row) == 17:
        pass
    elif len(row) == 22:
        if row[18] is None:
            pass
        elif row[18] != row[0]:
            raise Exception("fileinfo_id doesn't match: {} != {}".format(row[0], row[18]))
        else:
            fileinfo.blob = BlobInfo(size=row[19],
                                     md5=row[20],
                                     sha1=row[21])
    else:
        raise Exception("unknown row length: {}: {}".format(len(row), row))

    return fileinfo


def FetchAllIter(cur):
    while True:
        results = cur.fetchmany()
        if results == []:
            break
        for result in results:
            yield result


class Database:

    def __init__(self, filename):
        self.insert_count = 0  # number of inserts since last commit
        self.insert_size = 0  # number of blob bytes processed since last commit
        self.last_commit_time = time.time()
        self.max_insert_count = 5000
        self.max_insert_size = 100 * 1000 * 1000

        self.con = sqlite3.connect(filename, timeout=300)

        # Filenames are stored as TEXT in sqlite, even so they are not
        # necessarily valid UTF-8, using os.fsencode() is required to
        # convert them into Python strings.
        self.con.text_factory = os.fsdecode

        self.init_tables()

    def init_tables(self):
        cur = self.con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS fileinfo(" +
                    "id INTEGER PRIMARY KEY, " +
                    # "storage_id INTEGER, " +
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

        cur.execute("CREATE TABLE IF NOT EXISTS storageinfo(" +
                    "id INTEGER PRIMARY KEY, " +
                    "name TEXT" +
                    ")")

        cur.execute("CREATE INDEX IF NOT EXISTS fileinfo_index ON fileinfo (path)")
        cur.execute("CREATE INDEX IF NOT EXISTS blobinfo_fileinfo_id_index ON blobinfo (fileinfo_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS blobinfo_sha1_index ON blobinfo (sha1)")
        cur.execute("CREATE INDEX IF NOT EXISTS blobinfo_md5_index ON blobinfo (md5)")

    def store(self, fileinfo):
        # print("store...", fileinfo.path)
        cur = self.con.cursor()
        cur.execute("INSERT INTO fileinfo VALUES" +
                    "(NULL, ?, cast(? as TEXT), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (fileinfo.kind,
                     os.fsencode(fileinfo.path),
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

        # auto-commit if certain thresholds are crossed
        self.insert_count += 1

        if fileinfo.blob is not None:
            self.insert_size += fileinfo.blob.size

        if self.insert_count >= self.max_insert_count or \
           self.insert_size >= self.max_insert_size:
            # if time.time() > self.last_commit_time + 5.0:
            self.commit()

    def get_by_path(self, path):
        cur = self.con.cursor()
        cur.execute("SELECT * FROM fileinfo LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id WHERE path = cast(? as TEXT)",
                    [os.fsencode(path)])
        rows = cur.fetchall()
        if len(rows) == 0:
            return None
        else:
            row = rows[-1]
            fileinfo = fileinfo_from_row(row)
            return fileinfo

    def get_all(self):
        cur = self.con.cursor()
        cur.execute("SELECT * FROM fileinfo LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id;")
        rows = FetchAllIter(cur)
        return (fileinfo_from_row(row) for row in rows)

    def get_by_glob(self, pattern):
        cur = self.con.cursor()
        cur.execute("SELECT * FROM fileinfo LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id WHERE path glob cast(? as TEXT)",
                    [os.fsencode(pattern)])
        rows = FetchAllIter(cur)
        return (fileinfo_from_row(row) for row in rows)

    def get_duplicates(self, path):
        cur = self.con.cursor()
        cur.execute((
            "SELECT "
            "  blobinfo.sha1, "
            "  fileinfo.path "
            "FROM fileinfo "
            "INNER JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
            "WHERE "
            "fileinfo.id IN ( "
            "  SELECT fileinfo_id "
            "  FROM blobinfo "
            "  INNER JOIN ( "
            "    SELECT "
            "      sha1 "
            "    FROM blobinfo "
            "    GROUP BY sha1 "
            "    HAVING count(*) > 1 "
            "    ) dup ON dup.sha1 = blobinfo.sha1 "
            "  ) AND "
            "path GLOB CAST(? AS TEXT) "
            "ORDER BY blobinfo.sha1;"),
            [os.fsencode(path) + b"/*"])

        rows = FetchAllIter(cur)
        duplicates = defaultdict(list)
        for row in rows:
            sha1, path, *rest = row
            duplicates[sha1].append((sha1, path))

        return duplicates.values()

    def commit(self):
        t = time.time()
        print("------------------- commit -------------------:",
              "count:", self.insert_count,
              "size:", self.insert_size,
              "time: {:.2f}".format(t - self.last_commit_time),
              "speed: {:.2f} MB/s".format((self.insert_size / 1000 / 1000)  / (t - self.last_commit_time)))

        self.con.commit()
        self.last_commit_time = t
        self.insert_count = 0
        self.insert_size = 0


class NullDatabase:

    def __init__(self):
        pass

    def store(self, fileinfo):
        print("store:", fileinfo.json())

    def commit(self):
        pass


# EOF #
