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


from typing import Optional

import os
import logging
import yaml

import scatterbackup.util


class Config:

    def __init__(self) -> None:
        self.excludes: list[str] = []
        self.defaults: list[str] = []

    def load(self, filename: Optional[str] = None) -> None:
        if filename is None:
            config_dir = scatterbackup.util.make_config_directory()
            filename = os.path.join(config_dir, "config.yaml")

        if not os.path.exists(filename):
            logging.info("no config file found at %s", filename)
        else:
            logging.info("loading config file from %s", filename)
            with open(filename) as fin:
                cfg = yaml.safe_load(fin)

            self.excludes = cfg.get("excludes", [])
            self.defaults = cfg.get("defaults", [])


# EOF #
