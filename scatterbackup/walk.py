# pylint: skip-file

# See https://docs.python.org/3/license.html for license information

from typing import Any, Callable, Generator, Optional, Sequence, Tuple, Union

import sys

import stat
import os
from os import scandir, path, name, listdir, PathLike, DirEntry


def walk(top: Union[str, PathLike[str]], topdown: bool = True,
         onerror: Optional[Callable[[OSError], None]] = None,
         followlinks: bool = False,
         maxdepth: Optional[int] = None) -> Generator[Tuple[Union[str, PathLike[str]],
                                                            list[Union[str, PathLike[str]]],
                                                            list[Union[str, PathLike[str]]]],
                                                      None, None]:
    if maxdepth is None:
        maxdepth = sys.maxsize
    return _walk(top, topdown, onerror, followlinks, maxdepth, depth=1)


# This is the os.walk() function from Python-3.5.2, modified such that
# it returns symlinks to directories in the 'nodirs' portion of the
# result tuple instead of the 'dirs' one.
def _walk(top: Union[str, PathLike[str]], topdown: bool,
          onerror: Optional[Callable[[OSError], None]],
          followlinks: bool,
          maxdepth: int,
          depth: int) -> Generator[Tuple[Union[str, PathLike[str]],
                                         list[Union[str, PathLike[str]]],
                                         list[Union[str, PathLike[str]]]],
                                   None, None]:
    """Directory tree generator.

    For each directory in the directory tree rooted at top (including top
    itself, but excluding '.' and '..'), yields a 3-tuple

        dirpath, dirnames, filenames

    dirpath is a string, the path to the directory.  dirnames is a list of
    the names of the subdirectories in dirpath (excluding '.' and '..').
    filenames is a list of the names of the non-directory files in dirpath.
    Note that the names in the lists are just names, with no path components.
    To get a full path (which begins with top) to a file or directory in
    dirpath, do os.path.join(dirpath, name).

    If optional arg 'topdown' is true or not specified, the triple for a
    directory is generated before the triples for any of its subdirectories
    (directories are generated top down).  If topdown is false, the triple
    for a directory is generated after the triples for all of its
    subdirectories (directories are generated bottom up).

    When topdown is true, the caller can modify the dirnames list in-place
    (e.g., via del or slice assignment), and walk will only recurse into the
    subdirectories whose names remain in dirnames; this can be used to prune the
    search, or to impose a specific order of visiting.  Modifying dirnames when
    topdown is false is ineffective, since the directories in dirnames have
    already been generated by the time dirnames itself is generated. No matter
    the value of topdown, the list of subdirectories is retrieved before the
    tuples for the directory and its subdirectories are generated.

    By default errors from the os.scandir() call are ignored.  If
    optional arg 'onerror' is specified, it should be a function; it
    will be called with one argument, an OSError instance.  It can
    report the error to continue with the walk, or raise the exception
    to abort the walk.  Note that the filename is available as the
    filename attribute of the exception object.

    By default, os.walk does not follow symbolic links to subdirectories on
    systems that support them.  In order to get this functionality, set the
    optional argument 'followlinks' to true.

    Caution:  if you pass a relative pathname for top, don't change the
    current working directory between resumptions of walk.  walk never
    changes the current directory, and assumes that the client doesn't
    either.

    Example:

    import os
    from os.path import join, getsize
    for root, dirs, files in os.walk('python/Lib/email'):
        print(root, "consumes", end="")
        print(sum([getsize(join(root, name)) for name in files]), end="")
        print("bytes in", len(files), "non-directory files")
        if 'CVS' in dirs:
            dirs.remove('CVS')  # don't visit CVS directories

    """

    dirs = []
    nondirs = []

    # We may not have read permission for top, in which case we can't
    # get a list of the files the directory contains.  os.walk
    # always suppressed the exception then, rather than blow up for a
    # minor reason when (say) a thousand readable directories are still
    # left to visit.  That logic is copied here.
    try:
        if name == 'nt' and isinstance(top, bytes):  # type: ignore
            scandir_it = _dummy_scandir(top)
        else:
            # Note that scandir is global in this module due
            # to earlier import-*.
            scandir_it = scandir(top)
        entries: Sequence[DirEntry[str]] = list(scandir_it)
    except OSError as error:
        if onerror is not None:
            onerror(error)
        return

    for entry in entries:
        try:
            is_dir = entry.is_dir()
        except OSError:
            # If is_dir() raises an OSError, consider that the entry is not
            # a directory, same behaviour than os.path.isdir().
            is_dir = False

        try:
            is_symlink = entry.is_symlink()
        except OSError:
            # If is_symlink() raises an OSError, consider that the
            # entry is not a symbolic link, same behaviour than
            # os.path.islink().
            is_symlink = False

        if is_dir and not is_symlink:
            dirs.append(entry.name)
        else:
            nondirs.append(entry.name)

        if not topdown and is_dir:
            # Bottom-up: recurse into sub-directory, but exclude symlinks to
            # directories if followlinks is False
            if followlinks:
                walk_into = True
            else:
                walk_into = not is_symlink

            if walk_into:
                if depth < maxdepth:
                    yield from _walk(entry.path, topdown, onerror, followlinks, maxdepth, depth + 1)

    # Yield before recursion if going top down
    if topdown:
        yield top, dirs, nondirs  # type: ignore

        # Recurse into sub-directories
        islink, join = path.islink, path.join
        for dirname in dirs:
            new_path = join(top, dirname)
            # Issue #23605: os.path.islink() is used instead of caching
            # entry.is_symlink() result during the loop on os.scandir() because
            # the caller can replace the directory entry during the "yield"
            # above.
            if followlinks or not islink(new_path):
                if depth < maxdepth:
                    yield from _walk(new_path, topdown, onerror, followlinks, maxdepth, depth + 1)
    else:
        # Yield after recursion if going bottom up
        yield top, dirs, nondirs  # type: ignore


class _DummyDirEntry:
    """Dummy implementation of DirEntry

    Only used internally by os.walk(bytes). Since os.walk() doesn't need the
    follow_symlinks parameter: don't implement it, always follow symbolic
    links.
    """

    def __init__(self, dir: Union[str, PathLike[str]], name: Union[str, PathLike[str]]) -> None:
        self.name = name
        self.path = path.join(dir, name)
        # Mimick FindFirstFile/FindNextFile: we should get file attributes
        # while iterating on a directory
        self._stat: Optional[os.stat_result] = None
        self._lstat: Optional[os.stat_result] = None
        try:
            self.stat(follow_symlinks=False)
        except OSError:
            pass

    def stat(self, *, follow_symlinks: bool = True) -> os.stat_result:
        if follow_symlinks:
            if self._stat is None:
                self._stat = os.stat(self.path)
            return self._stat
        else:
            if self._lstat is None:
                self._lstat = os.stat(self.path, follow_symlinks=False)
            return self._lstat

    def is_dir(self) -> bool:
        if self._lstat is not None and not self.is_symlink():
            # use the cache lstat
            result = self.stat(follow_symlinks=False)
            return bool(stat.S_ISDIR(result.st_mode))

        result = self.stat()
        return bool(stat.S_ISDIR(result.st_mode))

    def is_symlink(self) -> bool:
        result = self.stat(follow_symlinks=False)
        return bool(stat.S_ISLNK(result.st_mode))


def _dummy_scandir(dir: Union[str, PathLike[str]]) -> Any:
    # listdir-based implementation for bytes patches on Windows
    for n in listdir(dir):
        yield _DummyDirEntry(dir, n)


# EOF #
