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
import argparse
import scatterbackup
import sys


def process_directory(dir, checksums, relative, host, quiet):
    filecount = 0
    for root, dirs, files in os.walk(dir):
        filecount += len(files)

    fileidx = 1
    for root, dirs, files in os.walk(dir):
        for f in files:
            p = os.path.join(root, f)
            fileinfo = scatterbackup.FileInfo.from_file(p, checksums=checksums, relative=relative, host=host)
            print(fileinfo.json())

            if not quiet:
                sys.stderr.write("[{}% {}/{}] {}\n".format(int(fileidx/filecount * 100),
                                                           fileidx, filecount,
                                                           p))
                sys.stderr.flush()

            fileidx += 1


def main():
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
    parser.add_argument('--host', type=str, default=None,
                        help="Set the host name")
    parser.add_argument('-H', '--no-host', action='store_true', default=False,
                        help="Set the host name to None")
    args = parser.parse_args()

    if args.no_host:
        host = ""
    else:
        host = args.host

    for d in args.DIRECTORY:
        process_directory(d, not args.no_checksum, args.relative, host, args.quiet)


# EOF #
