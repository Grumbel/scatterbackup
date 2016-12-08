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
import sys
import sqlite3
import time
from scatterbackup.fileinfo import FileInfo
from scatterbackup.blobinfo import BlobInfo


def generation_from_row(row):
    if len(row) != 3:
        raise Exception("generation_from_row: to many columns: {}".format(row))
    else:
        return Generation(row[0], row[1], row[2])


def fileinfo_from_row(row):
    fileinfo = FileInfo(row[2])

    fileinfo.rowid = row[0]
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
    fileinfo.birth = row[17]
    fileinfo.death = row[18]
    fileinfo.directory_id = row[19]

    if len(row) == 20:
        pass  # no BlobInfo requested
    elif len(row) == 25:
        if row[21] is None:
            pass  # no BlobInfo available
        elif row[21] != row[0]:
            raise Exception("fileinfo_id doesn't match: {} != {}".format(row[0], row[21]))
        else:
            fileinfo.blob = BlobInfo(size=row[22],
                                     md5=row[23],
                                     sha1=row[24])
    elif len(row) == 28:
        if row[21] is None:
            pass  # no BlobInfo available
        elif row[21] != row[0]:
            raise Exception("fileinfo_id doesn't match: {} != {}".format(row[0], row[21]))
        else:
            fileinfo.blob = BlobInfo(size=row[22],
                                     md5=row[23],
                                     sha1=row[24])

        if row[25] is not None:
            if row[26] != row[0]:
                raise Exception("fileinfo_id doesn't match: {} != {}".format(row[0], row[26]))
            fileinfo.target = row[27]
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
        # convert them back into Python strings.
        self.con.text_factory = os.fsdecode

        self.current_generation = None

        self.init_tables()

    def init_tables(self):
        cur = self.con.cursor()
        cur.execute((
            "CREATE TABLE IF NOT EXISTS fileinfo("
            "id INTEGER PRIMARY KEY, "
            # "storage_id INTEGER, "
            "type TEXT, "
            "path TEXT, "

            "dev INTEGER, "
            "ino INTEGER, "

            "mode INTEGER, "
            "nlink INTEGER, "

            "uid INTEGER, "
            "gid INTEGER, "

            "rdev INTEGER, "

            "size INTEGER, "
            "blksize INTEGER, "
            "blocks INTEGER, "

            "atime INTEGER, "
            "ctime INTEGER, "
            "mtime INTEGER, "

            # time when this entry was created
            "time INTEGER, "

            "birth INTEGER, "
            "death INTEGER, "

            "directory_id INTEGER"
            ")"))

        cur.execute((
            "CREATE TABLE IF NOT EXISTS blobinfo("
            "id INTEGER PRIMARY KEY, "
            "fileinfo_id INTEGER, "
            "size INTEGER, "
            "md5 TEXT, "
            "sha1 TEXT"
            ")"))

        cur.execute((
            "CREATE TABLE IF NOT EXISTS directory("
            "id INTEGER PRIMARY KEY, "
            "path TEXT UNIQUE"
            ")"))

        cur.execute((
            "CREATE TABLE IF NOT EXISTS linkinfo("
            "id INTEGER PRIMARY KEY, "
            "fileinfo_id INTEGER, "
            "target TEXT "
            ")"))

        cur.execute((
            "CREATE TABLE IF NOT EXISTS storageinfo("
            "id INTEGER PRIMARY KEY, "
            "name TEXT"
            ")"))

        cur.execute((
            "CREATE TABLE IF NOT EXISTS generation("
            "id INTEGER PRIMARY KEY, "
            "command TEXT, "
            "time INTEGER"
            ")"))

        def py_dirname(p):
            try:
                if p is None:
                    return None
                else:
                    return os.path.dirname(p)
            except:
                print("ERROR", sys.exc_info())
                return None

        self.con.create_function("py_dirname", 1, py_dirname)

        if False:
            print("STARTING CONVERT")
            print("creating directory table")
            cur.execute(
                "INSERT OR IGNORE INTO directory "
                "SELECT NULL, py_dirname(path) FROM fileinfo")

            print("updating directory_id in fileinfo")
            cur.execute(
                "UPDATE fileinfo "
                "SET directory_id = (SELECT id FROM directory WHERE directory.path = py_dirname(fileinfo.path))")
            print("CONVERT DONE")

        cur.execute("CREATE INDEX IF NOT EXISTS fileinfo_index ON fileinfo (path)")
        cur.execute("CREATE INDEX IF NOT EXISTS fileinfo_directory_id_index ON fileinfo (directory_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS fileinfo2_index ON fileinfo (death, path)")
        cur.execute("CREATE INDEX IF NOT EXISTS directory_path_index ON fileinfo (path)")
        cur.execute("CREATE INDEX IF NOT EXISTS blobinfo_fileinfo_id_index ON blobinfo (fileinfo_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS blobinfo_sha1_index ON blobinfo (sha1)")
        cur.execute("CREATE INDEX IF NOT EXISTS blobinfo_md5_index ON blobinfo (md5)")

    def init_generation(self, cmd):
        cur = self.con.cursor()
        current_time = int(round(time.time() * 1000**3))
        cur.execute(("INSERT INTO generation VALUES"
                     "(NULL, ?, ?)"),
                    [cmd, current_time])
        self.current_generation = cur.lastrowid

    def store(self, fileinfo):
        cur = self.con.cursor()

        if fileinfo.birth is not None:
            birth = fileinfo.birth
        else:
            birth = self.current_generation

        if fileinfo.directory_id is None:
            dname = os.path.dirname(fileinfo.path)
            cur.execute(
                "INSERT OR IGNORE INTO directory "
                "VALUES (NULL, cast(? AS TEXT))",
                [os.fsencode(dname)])
            cur.execute(
                "SELECT id FROM directory WHERE path = cast(? AS TEXT)",
                [os.fsencode(dname)])
            fileinfo.directory_id = cur.fetchall()[0][0]

        # print("store...", fileinfo.path)
        cur.execute(
            ("INSERT INTO fileinfo VALUES"
             "(NULL, ?, cast(? as TEXT), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"),
            [fileinfo.kind,
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
             fileinfo.time,
             birth,
             fileinfo.death,
             fileinfo.directory_id])

        fileinfo_id = cur.lastrowid

        if fileinfo.blob is not None:
            cur.execute(("INSERT INTO blobinfo VALUES"
                         "(NULL, ?, ?, ?, ?)"),
                        (fileinfo_id, fileinfo.blob.size, fileinfo.blob.md5, fileinfo.blob.sha1))

        if fileinfo.target is not None:
            cur.execute(("INSERT INTO linkinfo VALUES"
                         "(NULL, ?, ?)"),
                        (fileinfo_id, fileinfo.target))

        # auto-commit if certain thresholds are crossed
        self.insert_count += 1

        if fileinfo.blob is not None:
            self.insert_size += fileinfo.blob.size

        if self.insert_count >= self.max_insert_count or \
           self.insert_size >= self.max_insert_size:
            # if time.time() > self.last_commit_time + 5.0:
            self.commit()

    def mark_removed_recursive(self, fileinfo):
        if fileinfo.rowid is None:
            print("mark_removed_recursive: no rowid given", fileinfo.path)
        elif fileinfo.kind != "directory":
            print("mark_removed_recursive: must be a directory", fileinfo.path)
        else:
            cur = self.con.cursor()

            # root
            cur.execute(
                ("UPDATE fileinfo "
                 "SET death = ? "
                 "WHERE fileinfo.id = ?"),
                [self.current_generation, fileinfo.rowid])

            # children
            cur.execute(
                ("UPDATE fileinfo "
                 "SET death = ? "
                 "WHERE fileinfo.path GLOB cast(? AS TEXT)"),
                [self.current_generation,
                 os.fsencode(os.path.join(fileinfo.path, "*"))])

    def mark_removed(self, fileinfo):
        if fileinfo.rowid is None:
            print("mark_removed: no rowid given", fileinfo.path)
        else:
            cur = self.con.cursor()
            cur.execute(
                ("UPDATE fileinfo "
                 "SET death = ? "
                 "WHERE fileinfo.id = ?"),
                [self.current_generation, fileinfo.rowid])

    def get_directory_by_path2(self, path):
        path_glob = os.path.join(path, "*")
        path_not_glob = os.path.join(path, "*", "*")

        cur = self.con.cursor()
        cur.execute(
            ("SELECT * "
             "FROM fileinfo "
             "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
             "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id "
             "WHERE "
             "  path GLOB cast(? AS TEXT) AND "
             "  path NOT GLOB cast(? AS TEXT) AND"
             "  fileinfo.death is NULL "),
            [os.fsencode(path_glob), os.fsencode(path_not_glob)])
        rows = FetchAllIter(cur)
        return (fileinfo_from_row(row) for row in rows)

    def get_directory_by_path(self, path):
        cur = self.con.cursor()
        cur.execute(
            ("SELECT id "
             "FROM directory "
             "WHERE "
             "  path = cast(? AS TEXT)"),
            [os.fsencode(path)])
        rows = cur.fetchall()

        if len(rows) != 1:
            return []
        else:
            rowid, = rows[0]

            cur.execute(
                ("SELECT * "
                 "FROM fileinfo "
                 "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
                 "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id "
                 "WHERE "
                 "  fileinfo.death is NULL AND "
                 "  fileinfo.directory_id = ?"),
                [rowid])
            rows = FetchAllIter(cur)

            return (fileinfo_from_row(row) for row in rows)

    def get_by_path_many(self, path):
        return self.get_by_path(path, all_matches=True)

    def get_by_path(self, path, all_matches=False):
        if all_matches:
            gen_limit_stmt = ""
        else:
            gen_limit_stmt = "  fileinfo.death is NULL AND "

        cur = self.con.cursor()
        cur.execute(
            ("SELECT * "
             "FROM fileinfo "
             "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
             "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id "
             "WHERE "
             +  gen_limit_stmt +
             "  path = cast(? as TEXT)"
             "ORDER BY birth ASC"),
            [os.fsencode(path)])
        rows = cur.fetchall()
        if len(rows) == 0:
            return None
        else:
            if all_matches:
                return [fileinfo_from_row(row) for row in rows]
            else:
                row = rows[-1]
                fileinfo = fileinfo_from_row(row)
                return fileinfo

    def get_all(self):
        cur = self.con.cursor()
        cur.execute(
            ("SELECT * "
             "FROM fileinfo "
             "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
             "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id "))
        rows = FetchAllIter(cur)
        return (fileinfo_from_row(row) for row in rows)

    def get_by_glob(self, pattern):
        cur = self.con.cursor()
        cur.execute(
            ("SELECT * "
             "FROM fileinfo "
             "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
             "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id "
             "WHERE "
             "  fileinfo.death is NULL AND "
             "  path glob cast(? as TEXT)"),
            [os.fsencode(pattern)])
        rows = FetchAllIter(cur)
        return (fileinfo_from_row(row) for row in rows)

    def get_duplicates(self, path):
        cur = self.con.cursor()

        # doing the GLOB early speeds things up a good bit, even so it
        # has to be done twice
        stmt = (
            "WITH "

            "  matching_fileinfo_ids AS ("
            "    SELECT id "
            "    FROM fileinfo "
            "    WHERE path GLOB CAST(? AS TEXT) "
            "  ), "

            "  duplicate_sha1s AS ("
            "    SELECT sha1 "
            "    FROM blobinfo "
            "    WHERE fileinfo_id IN matching_fileinfo_ids "
            "    GROUP BY sha1 "
            "    HAVING COUNT(*) > 1"
            "  ),"

            "  duplicate_fileinfo_ids AS ("
            "    SELECT fileinfo_id "
            "    FROM blobinfo "
            "    INNER JOIN duplicate_sha1s ON duplicate_sha1s.sha1 = blobinfo.sha1 "
            "  )"

            "SELECT * "
            "FROM fileinfo "
            "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
            "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id "
            "WHERE "
            "  fileinfo.death is NULL AND "
            "  fileinfo.id IN duplicate_fileinfo_ids AND "
            "  path GLOB CAST(? AS TEXT)"
            "ORDER BY blobinfo.sha1 ASC"
        )

        arg = os.path.join(os.fsencode(path), b"*")
        cur.execute(stmt, [arg, arg])

        rows = FetchAllIter(cur)

        current_sha1 = None
        group = []
        for row in rows:
            fileinfo = fileinfo_from_row(row)

            if current_sha1 != fileinfo.blob.sha1:
                if group != []:
                    yield group

                group = []
                current_sha1 = fileinfo.blob.sha1

            group.append(fileinfo)

        if group != []:
            yield group

    def get_generations(self, start, end):
        cur = self.con.cursor()
        cur.execute(
            ("SELECT * "
             "FROM generation "
             "WHERE start <= ? AND ? < end"),
            [start, end])
        rows = FetchAllIter(cur)
        return [generation_from_row(row) for row in rows]

    def fsck(self):
        # check for path that have multiple alive FileInfo associated with them
        cur = self.con.cursor()
        cur.execute(
            ("SELECT * "
             "FROM ( "
             "  SELECT * "
             "  FROM fileinfo "
             "  WHERE death is NULL "
             "  ) AS birth "
             "GROUP BY path "
             "HAVING COUNT(*) > 1"))
        rows = FetchAllIter(cur)
        for row in rows:
            fileinfo = fileinfo_from_row(row)
            print("error: double-alive: {}".format(fileinfo.path))

        # check for FileInfo that have never been born
        cur.execute(
            ("SELECT * "
             "FROM fileinfo "
             "WHERE birth is NULL "))
        rows = FetchAllIter(cur)
        for row in rows:
            fileinfo = fileinfo_from_row(row)
            print("error: birth must not be NULL: {}".format(fileinfo.path))

        # check for orphaned BlobInfo
        cur.execute(
            ("SELECT count(*) "
             "FROM blobinfo "
             "WHERE fileinfo_id NOT IN (SELECT id from fileinfo)"))
        rows = cur.fetchall()
        if rows[0][0] > 0:
            print("error: {} orphaned BlobInfo".format(rows[0][0]))

    def commit(self):
        t = time.time()
        print("------------------- commit -------------------:",
              "count:", self.insert_count,
              "size:", self.insert_size,
              "time: {:.2f}".format(t - self.last_commit_time),
              "speed: {:.2f} MB/s".format((self.insert_size / 1000 / 1000) / (t - self.last_commit_time)))

        self.con.commit()
        self.last_commit_time = t
        self.insert_count = 0
        self.insert_size = 0

    def print_info(self):
        cur = self.con.cursor()

        cur.execute(
            ("SELECT COUNT(*) "
             "FROM fileinfo "
             "WHERE death is NULL"))
        print("{} files in database".format(cur.fetchall()[0][0]))

        cur.execute(
            ("SELECT COUNT(*) "
             "FROM fileinfo "
             "WHERE death IS NOT NULL"))
        print("{} dead files in database".format(cur.fetchall()[0][0]))


class NullDatabase:

    def __init__(self):
        pass

    def store(self, fileinfo):
        # pylint: disable=locally-disabled, no-self-use
        print("store:", fileinfo.json())

    def commit(self):
        pass


# EOF #
