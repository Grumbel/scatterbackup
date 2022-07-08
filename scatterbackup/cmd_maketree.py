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


from typing import Callable, IO, Optional

import argparse
import sys

import scatterbackup
from scatterbackup.database import Database
from scatterbackup.generator import generate_fileinfos
from scatterbackup.fileinfo import FileInfo


def on_report(fileinfo: FileInfo, fout: IO[str] = sys.stdout) -> None:
    fout.write(fileinfo.json())
    fout.write("\n")


def on_error(err: OSError) -> None:
    sys.stderr.write("{}: cannot process path: {}: {}\n".format(
        sys.argv[0], err.filename, err.strerror))


def process_directory(directory: str, checksums: bool, relative: bool, prefix: str,
                      on_report_cb: Callable[[FileInfo], None]) -> None:
    if prefix is not None:
        relative = True

    for fileinfo in generate_fileinfos(directory,
                                       relative=relative,
                                       prefix=prefix,
                                       checksums=checksums,
                                       onerror=on_error):
        on_report_cb(fileinfo)


def main() -> None:
    parser = argparse.ArgumentParser(description='Collect FileInfo')
    parser.add_argument('DIRECTORY', action='store', type=str, nargs='+',
                        help='directory containing the mod')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="be more verbose")
    parser.add_argument('-q', '--quiet', action='store_true', default=False,
                        help="be less verbose")
    parser.add_argument('-n', '--no-checksum', action='store_true', default=False,
                        help="don't calculate checksums")
    parser.add_argument('-R', '--relative', action='store_true', default=False,
                        help="Path names are stored relative")
    parser.add_argument('-p', '--prefix', type=str, default=None,
                        help="Use a fake prefix to make a relative path absolute")
    parser.add_argument('--host', type=str, default=None,
                        help="Set the host name")
    parser.add_argument('-H', '--no-host', action='store_true', default=False,
                        help="Set the host name to None")
    parser.add_argument('-d', '--database', type=str, default=None,
                        help="Store results in database")
    parser.add_argument('-o', '--output', type=str, default=None,
                        help="Set the output filename")
    args = parser.parse_args()

    on_report_cb: Callable[[FileInfo], None] = on_report
    if args.output:
        fout = open(args.output, "w")

        def on_report_with_file(fileinfo: FileInfo, fout: IO[str] = fout) -> None:
            on_report(fileinfo, fout)

        on_report_cb = on_report_with_file

    db: Optional[Database] = None
    if args.database is not None:
        db = scatterbackup.Database(args.database)

        def on_report_with_database(fileinfo: FileInfo) -> None:
            assert db is not None
            db.store(fileinfo)

        on_report_cb = on_report_with_database

    for d in args.DIRECTORY:
        process_directory(d, not args.no_checksum, args.relative, args.prefix, on_report_cb)

    if db is not None:
        db.commit()


# EOF #
