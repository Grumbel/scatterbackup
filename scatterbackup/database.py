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
import logging

from scatterbackup.generation import Generation, GenerationRange
from scatterbackup.fileinfo import FileInfo
from scatterbackup.blobinfo import BlobInfo
from scatterbackup.sql import WHERE, AND, OR, sql_pretty_print


def path_iter(path):
    yield path
    while path != "/":
        path = os.path.dirname(path)
        yield path


def grange_to_sql(grange, args):
    if grange is None:
        grange_stmt = "fileinfo.death is NULL"
    elif grange.include_rule == GenerationRange.INCLUDE_ALIVE:
        grange_stmt = []
        if grange.start is not None:
            grange_stmt.append("fileinfo.death >= ?")
            args.append(grange.start)

        if grange.end is not None:
            grange_stmt.append("fileinfo.birth < ?")
            args.append(grange.end)

        grange_stmt = AND(*grange_stmt)
    elif grange.include_rule == GenerationRange.INCLUDE_CHANGED:
        grange_stmt = []
        if grange.start is not None:
            grange_stmt.append("? <= fileinfo.birth AND fileinfo.birth < ?")
            args += [grange.start, grange.end]

        if grange.end is not None:
            grange_stmt.append("? <= fileinfo.death AND fileinfo.death < ?")
            args += [grange.start, grange.end]

        grange_stmt = OR(*grange_stmt)
    else:
        raise Exception("invalid include_rule in GenerationRange")

    return grange_stmt


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

    def __init__(self, filename, sql_debug=False):
        self.sql_debug = sql_debug

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

        cur = self.con.cursor()
        self.execute(cur, "PRAGMA journal_mode = WAL")
        self.init_tables()

    def init_tables(self):
        cur = self.con.cursor()
        self.execute(cur,
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

        self.execute(cur,
            "CREATE TABLE IF NOT EXISTS blobinfo("
            "id INTEGER PRIMARY KEY, "
            "fileinfo_id INTEGER, "
            "size INTEGER, "
            "md5 TEXT, "
            "sha1 TEXT"
            ")")

        self.create_directory_table()

        self.execute(cur,
            "CREATE TABLE IF NOT EXISTS linkinfo("
            "id INTEGER PRIMARY KEY, "
            "fileinfo_id INTEGER, "
            "target TEXT "
            ")")

        self.execute(cur,
            "CREATE TABLE IF NOT EXISTS storageinfo("
            "id INTEGER PRIMARY KEY, "
            "name TEXT"
            ")")

        self.execute(cur,
            "CREATE TABLE IF NOT EXISTS generation("
            "id INTEGER PRIMARY KEY, "
            "start INTEGER, "
            "end INTEGER, "
            "command TEXT"
            ")")

        def py_dirname(p):
            """SQL text with invalid UTF-8 can't be passed directly to a custom
            functions, only 'None' will be received. The UTF-8 needs
            to be converted to a blob first and then back to text once
            the custom function returned. this can be done with:

            cast(py_dirname(cast(column_name AS BLOB)) AS TEXT)

            """

            if type(p) is not bytes:
                logging.error("error: py_dirname() parameter is not bytes")

            if p is None:
                print("WHY?!")
                return None
            else:
                return os.path.dirname(p)

        self.con.create_function("py_dirname", 1, py_dirname)

        self.execute(cur, "CREATE INDEX IF NOT EXISTS fileinfo_index ON fileinfo (path)")
        self.execute(cur, "CREATE INDEX IF NOT EXISTS fileinfo_directory_id_index ON fileinfo (directory_id)")
        self.execute(cur, "CREATE INDEX IF NOT EXISTS fileinfo2_index ON fileinfo (death, path)")
        self.execute(cur, "CREATE INDEX IF NOT EXISTS fileinfo_death_index ON fileinfo (death)")
        self.execute(cur, "CREATE INDEX IF NOT EXISTS fileinfo_birth_index ON fileinfo (birth)")

        self.execute(cur, "CREATE UNIQUE INDEX IF NOT EXISTS directory_path_index ON directory (path)")
        self.execute(cur, "CREATE INDEX IF NOT EXISTS directory_parent_id_index ON directory (parent_id)")

        self.execute(cur, "CREATE INDEX IF NOT EXISTS blobinfo_fileinfo_id_index ON blobinfo (fileinfo_id)")
        self.execute(cur, "CREATE INDEX IF NOT EXISTS blobinfo_sha1_index ON blobinfo (sha1)")
        self.execute(cur, "CREATE INDEX IF NOT EXISTS blobinfo_md5_index ON blobinfo (md5)")

        self.execute(cur, "CREATE INDEX IF NOT EXISTS linkinfo_fileinfo_id_index ON linkinfo (fileinfo_id)")

        self.con.commit()

    def init_generation(self, cmd):
        current_time = int(round(time.time() * 1000**3))
        cur = self.con.cursor()
        self.execute(cur,
            "INSERT INTO generation "
            "(command, start) "
            "VALUES "
            "(?, ?)",
            [cmd, current_time])
        self.current_generation = cur.lastrowid

        return self.current_generation

    def deinit_generation(self, rowid):
        current_time = int(round(time.time() * 1000**3))
        cur = self.con.cursor()
        self.execute(cur,
            "UPDATE generation "
            "SET "
            "  end = ? "
            "WHERE "
            "  id = ?",
            [current_time, rowid])

    def store_directory(self, path):
        cur = self.con.cursor()
        self.execute(cur,
            "SELECT id "
            "FROM directory "
            "WHERE path = cast(? AS TEXT)",
            [os.fsencode(path)])
        rows = cur.fetchall()
        if len(rows) == 1:
            return rows[0][0]
        else:
            # self.execute(cur, "SAVEPOINT store_directory")

            # create path entries
            self.executemany(cur,
                "INSERT OR IGNORE INTO directory "
                "VALUES (NULL, cast(? AS TEXT), NULL)",
                [[os.fsencode(p)] for p in path_iter(path)])

            # update parent_ids
            if False:  # this is slow
                self.execute(cur,
                    "UPDATE directory "
                    "SET parent_id = ("
                    "  SELECT t.id FROM directory AS t "
                    "  WHERE t.path = cast(py_dirname(cast(directory.path AS BLOB)) AS TEXT))"
                    "WHERE parent_id IS NULL")
            else:
                self.execute(cur,
                    "SELECT id, path "
                    "FROM directory "
                    "WHERE parent_id IS NULL")
                parent_is_null = [(row[0], os.path.dirname(row[1])) for row in cur]

                for d_id, parent_path in parent_is_null:
                    self.execute(cur,
                        "SELECT id "
                        "FROM directory "
                        "WHERE path = cast(? AS TEXT)",
                        [os.fsencode(parent_path)])
                    rows = cur.fetchall()
                    if rows == []:
                        # FIXME: this happens when the above INSERT is
                        # interrupted before the parent_id are set
                        # properly
                        pass
                    else:
                        parent_id = rows[0][0]

                        self.execute(cur,
                            "UPDATE directory "
                            "SET parent_id = ?"
                            "WHERE id = ?",
                            [parent_id, d_id])

            # self.execute(cur, "RELEASE store_directory")

            # retry to query the directory_id
            self.execute(cur,
                "SELECT id "
                "FROM directory "
                "WHERE path = cast(? AS TEXT)",
                [os.fsencode(path)])
            rows = cur.fetchall()
            return rows[0][0]

    def store(self, fileinfo):
        if fileinfo.birth is not None:
            birth = fileinfo.birth
        else:
            birth = self.current_generation

        if fileinfo.directory_id is None:
            dname = os.path.dirname(fileinfo.path)
            fileinfo.directory_id = self.store_directory(dname)

        cur = self.con.cursor()

        # print("store...", fileinfo.path)
        self.execute(cur,
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
            self.execute(cur,
                "INSERT INTO blobinfo VALUES"
                "(NULL, ?, ?, ?, ?)",
                (fileinfo_id, fileinfo.blob.size, fileinfo.blob.md5, fileinfo.blob.sha1))

        if fileinfo.target is not None:
            self.execute(cur,
                "INSERT INTO linkinfo VALUES"
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
            self.execute(cur,
                "SELECT id FROM directory WHERE path = cast(? AS TEXT)",
                [os.fsencode(fileinfo.path)])
            rows = cur.fetchall()
            if len(rows) != 1:
                print("mark_removed_recursive: directory not found: {}".format(fileinfo.path))
            else:
                root_directory_id = rows[0][0]

                # remove all the children of the root node
                self.execute(cur,
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
            self.execute(cur,
                "UPDATE fileinfo "
                "SET death = ? "
                "WHERE fileinfo.id = ?",
                [self.current_generation, fileinfo.rowid])

    def mark_removed(self, fileinfo):
        if fileinfo.rowid is None:
            print("mark_removed: no rowid given", fileinfo.path)
        else:
            cur = self.con.cursor()
            self.execute(cur,
                "UPDATE fileinfo "
                "SET death = ? "
                "WHERE fileinfo.id = ?",
                [self.current_generation, fileinfo.rowid])

    def get_directory_by_path(self, path):
        """Returns the directory given by 'path', does not recurse into the directory"""
        cur = self.con.cursor()
        self.execute(cur,
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

            self.execute(cur,
                "SELECT * "
                "FROM fileinfo "
                "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
                "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id "
                "WHERE "
                "  fileinfo.death is NULL AND "
                "  fileinfo.directory_id = ?",
                [rowid])

            return (fileinfo_from_row(row) for row in cur)

    def get_one_by_path(self, path, grange=None):
        gen = self.get_by_path(path, grange)
        lst = list(gen)
        if lst == []:
            return None
        elif len(lst) > 1:
            logging.warning("multiple rows in database, expected one: %s", lst)

        return lst[-1]

    def get_by_path(self, path, grange=None):
        """When grange is None, return only the active file, otherwise return
        files as specified by grange"""
        args = []
        grange_stmt = grange_to_sql(grange, args)

        cur = self.con.cursor()
        self.execute(cur,
            "SELECT * "
            "FROM fileinfo "
            "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
            "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id " +
            WHERE(
                AND(grange_stmt,
                    "path = cast(? as TEXT)")) +
            "ORDER BY birth ASC",
            args + [os.fsencode(path)])
        return (fileinfo_from_row(row) for row in cur)

    def get_all(self):
        cur = self.con.cursor()
        self.execute(cur,
            "SELECT * "
            "FROM fileinfo "
            "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
            "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id ")
        return (fileinfo_from_row(row) for row in cur)

    def sql_print_debug(self, cur, sql, args_lst):
        sql_pretty_print(sql)
        print()
        for args in args_lst:
            print("ARGS: {}".format(args))
        print()

        self.execute(cur, "EXPLAIN QUERY PLAN " + sql, args_lst[0])
        for row in cur:
            print("explain>", row)

    def execute(self, cur, sql, args=[]):
        if self.sql_debug:
            print(",-----[SQL-debug: execute()]")
            print()
            self.sql_print_debug(cur, sql, [args])
            start_time = time.time()

        result = cur.execute(sql, args)

        if self.sql_debug:
            print("Time to execute: {:.16f} secs".format(time.time() - start_time))
            print("`-----\n")

        return result

    def executemany(self, cur, sql, args):
        if self.sql_debug:
            print(",-----[SQL-debug: executemany()]")
            print()
            self.sql_print_debug(cur, sql, args)
            start_time = time.time()

        result = cur.executemany(sql, args)

        if self.sql_debug:
            print("Time to execute: {:.16f} secs".format(time.time() - start_time))
            print("`-----\n")

        return result

    def get_by_glob(self, patterns, grange=None):
        patterns = patterns if type(patterns) is list else [patterns]

        grange_args = []
        grange_stmt = grange_to_sql(grange, grange_args)

        glob_args = []
        glob_stmt = []

        for pattern in patterns:
            glob_args.append(os.fsencode(pattern))
            glob_stmt.append("path glob cast(? as TEXT)")

        glob_stmt = OR(*glob_stmt)

        cur = self.con.cursor()
        self.execute(cur,
            "SELECT * "
            "FROM fileinfo "
            "LEFT JOIN blobinfo ON blobinfo.fileinfo_id = fileinfo.id "
            "LEFT JOIN linkinfo ON linkinfo.fileinfo_id = fileinfo.id " +
            WHERE(
                AND(grange_stmt, glob_stmt)),
            grange_args + glob_args)

        return (fileinfo_from_row(row) for row in cur)

    def get_by_checksum(self, checksum_type, checksum, grange=None):
        grange_args = []
        grange_stmt = grange_to_sql(grange, grange_args)

        cur = self.con.cursor()
        self.execute(cur,
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
            .format(checksum_type) +
            WHERE(
                AND(grange_stmt,
                    "  fileinfo.id in matching_fileinfos")),
            grange_args + [checksum])
        return (fileinfo_from_row(row) for row in cur)

    def get_duplicates(self, path):
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

        cur = self.con.cursor()
        arg = os.path.join(os.fsencode(path), b"*")
        self.execute(cur, stmt, [arg, arg])

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

    def get_generations_range(self):
        cur = self.con.cursor()
        self.execute(cur,
            "SELECT MIN(id), MAX(id) + 1 "
            "FROM generation")

        rows = cur.fetchall()
        return GenerationRange(rows[0][0], rows[0][1])

    def get_generations(self, grange):
        if grange.start is not None and grange.end is not None:
            condition = "? <= id AND id < ?"
            bindings = [grange.start, grange.end]
        elif grange.start is not None and grange.end is None:
            condition = "? < id"
            bindings = [grange.start]
        elif grange.start is None and grange.end is not None:
            condition = "id >= ?"
            bindings = [grange.end]
        else:
            condition = ""
            bindings = []

        cur = self.con.cursor()
        self.execute(cur,
            "SELECT * "
            "FROM generation " +
            WHERE(condition),
            bindings)

        return [generation_from_row(row) for row in cur]

    def get_affected_generations(self, fileinfo_query):
        """Return a list of all generations in which files matching
        'fileinfo_query' where changed

        """
        cur = self.con.cursor()
        self.execute(cur,
            "SELECT DISTINCT birth AS gen "
            "FROM fileinfo "
            "WHERE path GLOB ? "
            "UNION "
            "SELECT DISTINCT death AS gen "
            "FROM fileinfo "
            "WHERE path GLOB ? AND "
            "      death IS NOT NULL "
            "ORDER BY gen",
            [fileinfo_query,
             fileinfo_query])

        return list(cur)

    def fsck(self):
        cur = self.con.cursor()
        # check for path that have multiple alive FileInfo associated with them
        self.execute(cur,
            "SELECT * "
            "FROM fileinfo "
            "WHERE death is NULL "
            "GROUP BY path "
            "HAVING COUNT(*) > 1")
        for row in cur:
            fileinfo = fileinfo_from_row(row)
            print("error: double-alive: {}".format(fileinfo.path))

        # check for FileInfo that have never been born
        self.execute(cur,
            "SELECT * "
            "FROM fileinfo "
            "WHERE birth is NULL ")
        for row in cur:
            fileinfo = fileinfo_from_row(row)
            print("error: birth must not be NULL: {}".format(fileinfo.path))

        # check for orphaned BlobInfo
        self.execute(cur,
            "SELECT count(*) "
            "FROM blobinfo "
            "WHERE fileinfo_id NOT IN (SELECT id from fileinfo)")
        rows = cur.fetchall()
        if rows[0][0] > 0:
            print("error: {} orphaned BlobInfo".format(rows[0][0]))

        # check for self referencing parent_ids in directory table
        self.execute(cur,
            "SELECT id, parent_id, path  "
            "FROM directory "
            "WHERE id = parent_id")
        for row in cur:
            print("error: self-reference in directory table: id={} parent_id={} path='{}'"
                  .format(row[0], row[1], row[2]))

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
        self.execute(cur,
            "SELECT COUNT(*) "
            "FROM fileinfo "
            "WHERE death is NULL")
        print("{} files in database".format(cur.fetchall()[0][0]))

        self.execute(cur,
            "SELECT COUNT(*) "
            "FROM fileinfo "
            "WHERE death IS NOT NULL")
        print("{} dead files in database".format(cur.fetchall()[0][0]))

        self.execute(cur,
            "SELECT COUNT(*) "
            "FROM directory")
        print("{} directories in database".format(cur.fetchall()[0][0]))

    def create_directory_table(self):
        cur = self.con.cursor()
        self.execute(cur,
            "CREATE TABLE IF NOT EXISTS directory("
            "id INTEGER PRIMARY KEY, "
            "path TEXT UNIQUE, "
            "parent_id INTEGER"
            ")")

    def rebuild_directory_table(self):
        cur = self.con.cursor()
        print("Deleting old directory table")
        self.execute(cur,
            "DROP TABLE directory")

        print("Creating empty directory table")
        self.create_directory_table()

        print("Filling directory table with content")
        self.execute(cur,
            "INSERT OR IGNORE INTO directory "
            "  SELECT NULL, cast(py_dirname(cast(path AS BLOB)) AS TEXT), id "
            "  FROM fileinfo")

        print("Setting parent_ids in directory table")
        self.execute(cur,
            "UPDATE directory "
            "SET parent_id = ("
            "  SELECT t.id FROM directory AS t "
            "  WHERE t.path = cast(py_dirname(cast(directory.path AS BLOB)) AS TEXT))")

        print("Setting directory_ids in fileinfo table")
        self.execute(cur,
            "UPDATE fileinfo "
            "SET directory_id = ("
            "  SELECT id FROM directory "
            "  WHERE directory.path = cast(py_dirname(cast(fileinfo.path AS BLOB)) AS TEXT))")

    def cleanup_double_alive(self):
        cur = self.con.cursor()
        self.execute(cur,
            "WITH "

            "duplicate_path AS ("
            "  SELECT path "
            "  FROM fileinfo "
            "  WHERE death is NULL "
            "  GROUP BY path "
            "  HAVING COUNT(*) > 1), "

            "keep_id AS ("
            "  SELECT MAX(fileinfo.id) "
            "  FROM duplicate_path "
            "  LEFT JOIN fileinfo ON fileinfo.path = duplicate_path.path "
            "  GROUP BY fileinfo.path) "

            "DELETE FROM fileinfo "
            "WHERE "
            "  path IN duplicate_path AND "
            "  id NOT IN keep_id")

    def rebuild_indices(self):
        cur = self.con.cursor()
        self.execute(cur,
            "SELECT name "
            "FROM sqlite_master "
            "WHERE "
            "  type = 'index' AND "
            "  sql IS NOT NULL")

        rows = list(cur)
        for row in rows:
            name = row[0]
            print("dropping {}".format(name))
            self.execute(cur, "DROP INDEX {}".format(name))

    def dump(self):
        """Dump the content of the database to stdout"""
        cur = self.con.cursor()
        for tbl in ['fileinfo', 'directory', 'blobinfo', 'linkinfo', 'generation']:
            print("\n{}:".format(tbl))
            self.execute(cur, "SELECT * FROM {}".format(tbl))
            for row in cur:
                print(" ", row)

    def vacuum(self):
        cur = self.con.cursor()
        self.execute(cur,
            "VACUUM")


class NullDatabase:

    def __init__(self):
        pass

    def store(self, fileinfo):
        # pylint: disable=no-self-use
        print("store:", fileinfo.json())

    def commit(self):
        pass


# EOF #
