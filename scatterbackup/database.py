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

from scatterbackup.generation import Generation
from scatterbackup.fileinfo import FileInfo
from scatterbackup.blobinfo import BlobInfo


def path_iter(path):
    yield path
    while path != "/":
        path = os.path.dirname(path)
        yield path


def generation_from_row(row):
    if len(row) != 4:
        raise Exception("generation_from_row: to many columns: {}".format(row))
    else:
        return Generation(row[0], row[1], row[2], row[3])


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
        cur.execute(
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
            ")")

        cur.execute(
            "CREATE TABLE IF NOT EXISTS blobinfo("
            "id INTEGER PRIMARY KEY, "
            "fileinfo_id INTEGER, "
            "size INTEGER, "
            "md5 TEXT, "
            "sha1 TEXT"
            ")")

        cur.execute(
            "CREATE TABLE IF NOT EXISTS directory("
            "id INTEGER PRIMARY KEY, "
            "path TEXT UNIQUE, "
            "parent_id INTEGER"
            ")")

        cur.execute(
            "CREATE TABLE IF NOT EXISTS linkinfo("
            "id INTEGER PRIMARY KEY, "
            "fileinfo_id INTEGER, "
            "target TEXT "
            ")")

        cur.execute(
            "CREATE TABLE IF NOT EXISTS storageinfo("
            "id INTEGER PRIMARY KEY, "
            "name TEXT"
            ")")

        cur.execute(
            "CREATE TABLE IF NOT EXISTS generation("
            "id INTEGER PRIMARY KEY, "
            "start INTEGER, "
            "end INTEGER, "
            "command TEXT"
            ")")

        def py_dirname(p):
            try:
                if p is None:
                    print("WHY?!")
                    return None
                else:
                    return os.fsencode(os.path.dirname(p))
            except:
                print("ERROR", sys.exc_info())
                return None

        self.con.create_function("py_dirname", 1, py_dirname)

        cur.execute("CREATE INDEX IF NOT EXISTS fileinfo_index ON fileinfo (path)")
        cur.execute("CREATE INDEX IF NOT EXISTS fileinfo_directory_id_index ON fileinfo (directory_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS fileinfo2_index ON fileinfo (death, path)")
        cur.execute("CREATE INDEX IF NOT EXISTS directory_path_index ON directory (path)")
        cur.execute("CREATE INDEX IF NOT EXISTS directory_parent_id_index ON directory (parent_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS blobinfo_fileinfo_id_index ON blobinfo (fileinfo_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS blobinfo_sha1_index ON blobinfo (sha1)")
        cur.execute("CREATE INDEX IF NOT EXISTS blobinfo_md5_index ON blobinfo (md5)")
        self.con.commit()

    def init_generation(self, cmd):
        cur = self.con.cursor()
        current_time = int(round(time.time() * 1000**3))
        cur.execute("INSERT INTO generation "
                    "(command, start) "
                    "VALUES "
                    "(?, ?)",
                    [cmd, current_time])
        self.current_generation = cur.lastrowid

        return self.current_generation

    def deinit_generation(self, rowid):
        cur = self.con.cursor()
        current_time = int(round(time.time() * 1000**3))
        cur.execute("UPDATE generation "
                    "SET "
                    "  end = ? "
                    "WHERE "
                    "  id = ?",
                    [current_time, rowid])

    def store_directory(self, path):
        cur = self.con.cursor()
        cur.execute("SELECT id "
                    "FROM directory "
                    "WHERE path = cast(? AS TEXT)",
                    [os.fsencode(path)])
        rows = cur.fetchall()
        if len(rows) == 1:
            return rows[0][0]
        else:
            # create path entries
            cur.executemany(
                "INSERT OR IGNORE INTO directory "
                "VALUES (NULL, cast(? AS TEXT), NULL)",
                [[os.fsencode(p)] for p in path_iter(path)])

            # update parent_ids
            cur.execute("UPDATE directory "
                        "SET parent_id = ("
                        "  SELECT t.id FROM directory AS t "
                        "  WHERE t.path = directory.path)"
                        "WHERE parent_id IS NULL")

            # retry to query the directory_id
            cur.execute("SELECT id "
                        "FROM directory "
                        "WHERE path = cast(? AS TEXT)",
                        [os.fsencode(path)])
            rows = cur.fetchall()
            return rows[0][0]

    def store(self, fileinfo):
        cur = self.con.cursor()

        if fileinfo.birth is not None:
            birth = fileinfo.birth
        else:
            birth = self.current_generation

        if fileinfo.directory_id is None:
            dname = os.path.dirname(fileinfo.path)
            fileinfo.directory_id = self.store_directory(dname)

        # print("store...", fileinfo.path)
        cur.execute(
            "INSERT INTO fileinfo VALUES"
            "(NULL, ?, cast(? as TEXT), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
            cur.execute("INSERT INTO blobinfo VALUES"
                        "(NULL, ?, ?, ?, ?)",
                        (fileinfo_id, fileinfo.blob.size, fileinfo.blob.md5, fileinfo.blob.sha1))

        if fileinfo.target is not None:
            cur.execute("INSERT INTO linkinfo VALUES"
                        "(NULL, ?, ?)",
                        (fileinfo_id, fileinfo.target))

        # auto-commit if certain thresholds are crossed
        self.insert_count += 1

        if fileinfo.blob is not None:
            self.insert_size += fileinfo.blob.size

        if (self.max_insert_count is not None and self.insert_count >= self.max_insert_count) or \
           (self.max_insert_size is not None and self.insert_size >= self.max_insert_size):
            # if time.time() > self.last_commit_time + 5.0:
            self.commit()

    def mark_removed_recursive(self, fileinfo):
        if fileinfo.rowid is None:
            print("mark_removed_recursive: no rowid given", fileinfo.path)
        elif fileinfo.kind != "directory":
            print("mark_removed_recursive: must be a directory", fileinfo.path)
        else:
            cur = self.con.cursor()

            # "WITH RECURSIVE" is *much* faster when we use a plain
            # value in the initial-select instead of this SELECT
            # statement
            cur.execute("SELECT id FROM directory WHERE path = cast(? AS TEXT)",
                        [os.fsencode(fileinfo.path)])
            rows = cur.fetchall()
            if len(rows) != 1:
                print("mark_removed_recursive: directory not found: {}".format(fileinfo.path))
            else:
                root_directory_id = rows[0][0]

                # remove all the children of the root node
                cur.execute(
                    "WITH RECURSIVE "

                    # create a list of directory.id that are to be removed
                    "child_dirs(x) AS ( "
                    "  VALUES(?) "
                    "  UNION ALL "
                    "  SELECT id "
                    "  FROM directory, child_dirs "
                    "  WHERE parent_id = x "
                    ") "

                    "UPDATE fileinfo "
                    "SET death = ? "
                    "WHERE directory_id IN child_dirs AND death is NULL",
                    [root_directory_id,
                     self.current_generation])

            # remove the root node itself
            cur.execute(
                "UPDATE fileinfo "
                "SET death = ? "
                "WHERE fileinfo.id = ?",
                [self.current_generation, fileinfo.rowid])

    def mark_removed(self, fileinfo):
        if fileinfo.rowid is None:
            print("mark_removed: no rowid given", fileinfo.path)
        else:
            cur = self.con.cursor()
            cur.execute(
                "UPDATE fileinfo "
                "SET death = ? "
                "WHERE fileinfo.id = ?",
                [self.current_generation, fileinfo.rowid])

    def get_directory_by_path(self, path):
        """Returns the directory given by 'path', does not recurse into the directory"""
        cur = self.con.cursor()
        cur.execute(
            "SELECT id "
            "FROM directory "
            "WHERE "
            "  path = cast(? AS TEXT)",
            [os.fsencode(path)])
        rows = cur.fetchall()

        if len(rows) != 1:
            return []
        else:
            rowid, = rows[0]

            cur.execute(
                "SELECT * "
                "FROM fileinfo "
                "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
                "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id "
                "WHERE "
                "  fileinfo.death is NULL AND "
                "  fileinfo.directory_id = ?",
                [rowid])

            return (fileinfo_from_row(row) for row in cur)

    def get_by_path_many(self, path):
        return self.get_by_path(path, all_matches=True)

    def get_by_path(self, path, all_matches=False):
        if all_matches:
            gen_limit_stmt = ""
        else:
            gen_limit_stmt = "  fileinfo.death is NULL AND "

        cur = self.con.cursor()
        cur.execute(
            "SELECT * "
            "FROM fileinfo "
            "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
            "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id "
            "WHERE "
            + gen_limit_stmt +
            "  path = cast(? as TEXT)"
            "ORDER BY birth ASC",
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
            "SELECT * "
            "FROM fileinfo "
            "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
            "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id ")
        return (fileinfo_from_row(row) for row in cur)

    def get_by_glob(self, pattern):
        cur = self.con.cursor()
        cur.execute(
            "SELECT * "
            "FROM fileinfo "
            "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
            "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id "
            "WHERE "
            "  fileinfo.death is NULL AND "
            "  path glob cast(? as TEXT)",
            [os.fsencode(pattern)])
        return (fileinfo_from_row(row) for row in cur)

    def get_by_checksum(self, checksum_type, checksum):
        cur = self.con.cursor()
        cur.execute(
            "WITH "

            "matching_fileinfos AS ( "
            "  SELECT fileinfo_id "
            "  FROM blobinfo "
            "  WHERE "
            "    {} = ?) "

            "SELECT * "
            "FROM fileinfo "
            "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
            "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id "
            "WHERE "
            "  fileinfo.death is NULL AND "
            "  fileinfo.id in matching_fileinfos".format(checksum_type),
            [checksum])
        return (fileinfo_from_row(row) for row in cur)

    def get_duplicates(self, path):
        cur = self.con.cursor()

        # doing the GLOB early speeds things up a good bit, even so it
        # has to be done twice
        stmt = (
            "WITH "

            "  matching_fileinfo_ids AS ("
            "    SELECT id "
            "    FROM fileinfo "
            "    WHERE "
            "      fileinfo.death is NULL AND"
            "      path GLOB CAST(? AS TEXT) "
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

        current_sha1 = None
        group = []
        for row in cur:
            fileinfo = fileinfo_from_row(row)

            if current_sha1 != fileinfo.blob.sha1:
                if group != []:
                    yield group

                group = []
                current_sha1 = fileinfo.blob.sha1

            group.append(fileinfo)

        if group != []:
            yield group

    def get_generations(self, start=None, end=None):
        cur = self.con.cursor()

        if start is not None and end is not None:
            condition = "WHERE ? <= id AND id < ?"
            bindings = [start, end]
        elif start is not None and end is None:
            condition = "WHERE ? < id"
            bindings = [start]
        elif start is None and end is not None:
            condition = "WHERE id >= ?"
            bindings = [end]
        else:
            condition = ""
            bindings = []

        cur.execute(
            "SELECT * "
            "FROM generation "
            + condition,
            bindings)

        return [generation_from_row(row) for row in cur]

    def fsck(self):
        # check for path that have multiple alive FileInfo associated with them
        cur = self.con.cursor()
        cur.execute(
            "SELECT * "
            "FROM ( "
            "  SELECT * "
            "  FROM fileinfo "
            "  WHERE death is NULL "
            "  ) AS birth "
            "GROUP BY path "
            "HAVING COUNT(*) > 1")
        for row in cur:
            fileinfo = fileinfo_from_row(row)
            print("error: double-alive: {}".format(fileinfo.path))

        # check for FileInfo that have never been born
        cur.execute(
            "SELECT * "
            "FROM fileinfo "
            "WHERE birth is NULL ")
        for row in cur:
            fileinfo = fileinfo_from_row(row)
            print("error: birth must not be NULL: {}".format(fileinfo.path))

        # check for orphaned BlobInfo
        cur.execute(
            "SELECT count(*) "
            "FROM blobinfo "
            "WHERE fileinfo_id NOT IN (SELECT id from fileinfo)")
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
            "SELECT COUNT(*) "
            "FROM fileinfo "
            "WHERE death is NULL")
        print("{} files in database".format(cur.fetchall()[0][0]))

        cur.execute(
            "SELECT COUNT(*) "
            "FROM fileinfo "
            "WHERE death IS NOT NULL")
        print("{} dead files in database".format(cur.fetchall()[0][0]))

        cur.execute(
            "SELECT COUNT(*) "
            "FROM directory")
        print("{} directories in database".format(cur.fetchall()[0][0]))

    def dump(self):
        """Dump the content of the database to stdout"""
        cur = self.con.cursor()
        for tbl in ['fileinfo', 'directory', 'blobinfo', 'linkinfo', 'generation']:
            print("\n{}:".format(tbl))
            cur.execute("SELECT * FROM {}".format(tbl))
            for row in cur:
                print(" ", row)


class NullDatabase:

    def __init__(self):
        pass

    def store(self, fileinfo):
        # pylint: disable=no-self-use
        print("store:", fileinfo.json())

    def commit(self):
        pass


# EOF #
