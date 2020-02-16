# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Lock files.

Please read:

fcntl(2)
flock(2)
lockf(3)
http://pubs.opengroup.org/onlinepubs/9699919799/functions/lockf.html
http://pubs.opengroup.org/onlinepubs/9699919799/functions/fcntl.html
https://github.com/python/cpython/blob/2.7/Modules/fcntlmodule.c

Informal references:

http://0pointer.de/blog/projects/locking.html
https://www.samba.org/samba/news/articles/low_point/tale_two_stds_os2.html
http://chris.improbable.org/2010/12/16/everything-you-never-wanted-to-know-about-file-locking/
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import errno
import fcntl
import logging
import os
import random
import time


logger = logging.getLogger(__name__)


class FileLock(object):
    """Context manager for an exclusive file lock.

    This uses fcntl() locks for portability.  Refer to the module
    docstring and the links therein for details that informed this
    choice.

    fcntl() locks have a number of important quirks:

    This may or may not work if the lock is on a remote filesystem.

    Locks are per-process and therefore not thread-safe.

    The lock is bound to the file inode:

    >>> tmp = getfixture('tmpdir')
    >>> f1 = str(tmp.join('lock'))
    >>> f2 = str(tmp.join('lock2'))
    >>> with FileLock(f1):
    ...     os.link(f1, f2)
    ...     f = open(f2)  # Same inode
    ...     f.close()     # This will release the lock
    ...     # Stuff here will run without the lock
    """

    def __init__(self, lockfile, timeout=180):
        """Initialize instance.

        Args:
            lockfile: Path to lockfile
            timeout: Timeout for grabbing lock, in seconds
        """
        self._lockfile = lockfile
        self._timeout = timeout
        self._fd = None

    def __enter__(self):
        timeout = time.time() + self._timeout
        # Wait for possible symlink locks and open lock file.
        while True:
            if not self._symlink_lock_present():
                try:
                    self._fd = os.open(self._lockfile,
                                       os.O_RDWR | os.O_CREAT,
                                       0o666)
                    break
                except OSError as e:  # pragma: no cover
                    logger.debug('Error opening lock file: %s', e)
            if time.time() > timeout:
                raise TimeoutError(self._lockfile, self._timeout)
            time.sleep(random.random())

        # Grab lock on file.
        while True:
            try:
                fcntl.lockf(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError as e:
                logger.debug('Error acquiring lock: %s', e)
            else:
                return
            if time.time() > timeout:
                raise TimeoutError(self._lockfile, self._timeout)
            time.sleep(random.random())

    def __exit__(self, exc_type, exc_value, traceback):
        os.close(self._fd)

    def _symlink_lock_present(self):
        """Check if an old style symlink lock is in place."""
        # TODO(ayatane): 2017-08-21 Old symlink lock file handling can
        # be removed after the code has existed for Long Enough that
        # there aren't reasonably any instances of it left on developer
        # or prod machines.
        try:
            target = os.readlink(self._lockfile)
        except OSError as e:
            if e.errno == errno.EINVAL:
                # Not a symlink.
                return False
            elif e.errno == errno.ENOENT:
                # Lock is gone.
                return False
            else:  # pragma: no cover
                raise
        pid = _procdir.getpid(target)
        if _is_pid_running(pid):
            return True
        try:
            os.unlink(self._lockfile)
        except OSError as e:  # pragma: no cover
            if e.errno != errno.ENOENT:
                raise
        return False


class TimeoutError(Exception):
    """Grabbing lock timed out."""

    def __init__(self, filename, timeout):
        super(TimeoutError, self).__init__(filename, timeout)
        self.filename = filename
        self.timeout = timeout

    def __str__(self):
        return ('Grabbing lock %(filename)s'
                ' timed out after %(timeout)s seconds'
                % {
                    'filename': self.filename,
                    'timeout': self.timeout,
                })


class _ProcDir(object):
    """Class wrapping /proc related functions."""

    def __init__(self, procdir):
        self._procdir = procdir

    def getpath(self, pid):
        """Return /proc dir path for pid."""
        return os.path.join(self._procdir, str(pid))

    def getpid(self, path):
        """Return int pid for /proc path."""
        proc_prefix_len = len(self._procdir) + 1  # Handle extra ending slash
        pid_string = path[proc_prefix_len:]
        return int(pid_string)

_procdir = _ProcDir('/proc')


def _is_pid_running(pid):
    """Return True if pid is running."""
    try:
        os.kill(pid, 0)
    except OSError as e:
        return e.errno != errno.ESRCH
    else:
        return True
