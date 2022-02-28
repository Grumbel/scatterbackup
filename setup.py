#!/usr/bin/env python3

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


from setuptools import setup, find_packages


setup(name='scatterbackup',
      version='0.1.0',
      scripts=[],
      entry_points={
          'console_scripts': [
              'sb-maketree = scatterbackup.cmd_maketree:main',
              'sb-diff = scatterbackup.cmd_diff:main',
              'sb-diffdb = scatterbackup.cmd_diffdb:main',
              'sb-inbackup = scatterbackup.cmd_inbackup:main',
              'sb-ncdu = scatterbackup.cmd_ncdu:main',
              'sb-dbtool = scatterbackup.cmd_dbtool:main',
              'sb-md5sum = scatterbackup.cmd_md5sum:main',
              'sb-dupfinder = scatterbackup.cmd_dupfinder:main',
              'sb-dupfinderdb = scatterbackup.cmd_dupfinderdb:main',
              'sb-query = scatterbackup.cmd_query:main',
              'sb-update = scatterbackup.cmd_update:main',
              'sb-fsck = scatterbackup.cmd_fsck:main',
              'sb-info = scatterbackup.cmd_info:main',
              'sb-log = scatterbackup.cmd_log:main',
              'sb-du = scatterbackup.cmd_du:main',
              'sb-sha1sum = scatterbackup.cmd_sha1sum:main'
          ],
          'gui_scripts': []
          },
      packages=['scatterbackup'],
      install_requires=[
          'PyYAML',
          'pyxdg',
          'pyparsing'
      ])


# EOF #
