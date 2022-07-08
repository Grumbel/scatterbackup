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


from typing import Any, Sequence

import argparse
import json
import os
import sys
import time
import subprocess
import tempfile

from scatterbackup.util import sb_init, make_default_database
from scatterbackup.database import Database
from scatterbackup.fileinfo import FileInfo

# st_dev is included when it changes
# root directory contains full path
# directory:
# [{"name":"/tmp/test","asize":58,"dev":22,"ino":2203839}, # directory
#  {"name":"1MB.dat","asize":100000,"dsize":102400,"ino":2203840}, # files
#  {"name":"pcmC0D2c","ino":679,"notreg":true}, # device file
#  ...
#  [{"name":"foo","asize":6,"ino":2203947}, # subdirectory
#   {"name":"bar","ino":2203948}],


NcduFileNode = dict[str, Any]
NcduDirNode = list[Any]
NcduRoot = list[Any]


def ncdu_directory(node: FileInfo) -> NcduDirNode:
    return [{"name": os.path.basename(node.path),
             "asize": 0,
             "dev": node.dev,
             "ino": node.ino}]


def ncdu_fake_directory(name: str) -> NcduDirNode:
    return [{"name": os.path.basename(name) or "/",
             "asize": 0,
             "dev": 0,
             "ino": 0}]


def ncdu_file(node: FileInfo) -> NcduFileNode:
    if node.kind == "file":
        assert node.blocks is not None
        return {"name": os.path.basename(node.path),
                "asize": node.size,
                "dsize": node.blocks * 512,
                "ino": node.ino}
    else:
        return {"name": os.path.basename(node.path),
                "ino": node.ino,
                "notreg": True}


def ncdu_from_fileinfos_with_header(fileinfos: Sequence[FileInfo]) -> NcduRoot:
    return [1, 0,
            {"progname": "scatterbackup",
             "progver": "1.10",
             "timestamp": int(time.time())},
            ncdu_from_fileinfos(fileinfos)]


def build_hierachy(directories: dict[str, NcduDirNode]) -> None:
    nodes_without_parent = list(directories.items())

    while nodes_without_parent != []:
        dname, node = nodes_without_parent.pop()

        parent_dname = os.path.dirname(dname)

        if parent_dname == dname:
            pass
        else:
            parent_node = directories.get(parent_dname)

            if parent_node is None:
                parent_node = ncdu_fake_directory(parent_dname)
                nodes_without_parent.append((parent_dname, parent_node))
                directories[parent_dname] = parent_node

            parent_node.append(node)


def get_node_or_fake(directories: dict[str, NcduDirNode], dname: str) -> NcduDirNode:
    node = directories.get(dname)

    if node is not None:
        return node
    else:
        node = ncdu_fake_directory(dname)
        directories[dname] = node
        return node


def collapse_empty_dirs(directories: dict[str, NcduDirNode]) -> NcduDirNode:
    dname = "/"
    node = directories[dname]

    while len(node) == 2 and isinstance(node[1], list) and node[1] != []:
        dname = os.path.join(dname, node[1][0]['name'])
        node = node[1]

    node[0]['name'] = dname
    return node


def ncdu_from_fileinfos(fileinfos: Sequence[FileInfo]) -> NcduDirNode:
    dir_fileinfos = (f for f in fileinfos if f.kind == "directory")
    file_fileinfos = (f for f in fileinfos if f.kind != "directory")
    directories: dict[str, NcduDirNode] = {d.path: ncdu_directory(d) for d in dir_fileinfos}

    # attach all the files to their directories or fake directories
    for fileinfo in file_fileinfos:
        parent = get_node_or_fake(directories, os.path.dirname(fileinfo.path))
        parent.append(ncdu_file(fileinfo))

    build_hierachy(directories)

    root = collapse_empty_dirs(directories)
    # root = directories["/"]

    return root


def main() -> None:
    sb_init()

    parser = argparse.ArgumentParser(description='Convert .sbtr to ncdu syntax')
    parser.add_argument('FILE', action='store', type=str, nargs=1,
                        help='.sbtr file to load')
    parser.add_argument('-d', '--database', type=str, default=None,
                        help="Store results in database")
    parser.add_argument('-o', '--output', metavar="FILE", type=str, default=None,
                        help="Output results to FILE instead of starting ncdu")
    parser.add_argument('--debug-sql', action='store_true', default=False,
                        help="Debug SQL queries")
    args = parser.parse_args()

    db = Database(args.database or make_default_database(), args.debug_sql)

    # fileinfos = scatterbackup.sbtr.fileinfos_from_sbtr(args.FILE[0])

    # FIXME: do some benchmarking on glob vs directory table for tree retrieval
    # fileinfos = list(db.get_directory_by_path(os.path.abspath(args.FILE[0])))

    print("gather fileinfos")
    fileinfos = list(db.get_by_glob(os.path.join(os.path.abspath(args.FILE[0]), "*")))

    print("building .js data")
    ncdu_js = ncdu_from_fileinfos_with_header(fileinfos)
    if args.output is None:
        with tempfile.NamedTemporaryFile("w") as fout:
            print("dumping .js")
            json.dump(ncdu_js, fp=fout)
            fout.flush()
            print("calling ncdu")
            subprocess.call(["ncdu", "-f", fout.name])
    elif args.output == "-":
        json.dump(ncdu_js, fp=sys.stdout)
    else:
        with open(args.output, "w") as fout:
            json.dump(ncdu_js, fp=fout)


# EOF #
