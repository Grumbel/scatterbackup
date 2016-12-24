# ScatterBackup - A chaotic backup solution
# Copyright (C) 2016 Ingo Ruhnke <grumbel@gmail.com>
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


def sql_pretty_print(text):
    keywords = ["FROM",
                "LEFT JOIN",
                "INNER JOIN",
                "WHERE",
                "GROUP BY",
                "ORDER BY"]
    text = "sql> " + text
    for keyword in keywords:
        text = text.replace(keyword, "\nsql> " + keyword)
    print(text)


def WHERE(stmt):
    if stmt:
        return "WHERE " + stmt
    else:
        return ""


def OR(*stmts):
    if len(stmts) == 1:
        return stmts[0]
    else:
        stmts = [stmt for stmt in stmts if stmt]
        return " OR ".join("(" + stmt + ")" for stmt in stmts)


def AND(*stmts):
    if len(stmts) == 1:
        return stmts[0]
    else:
        stmts = [stmt for stmt in stmts if stmt]
        return " AND ".join("(" + stmt + ")" for stmt in stmts)


# EOF #
