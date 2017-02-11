# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Lock files"""

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


class FileLock(object):
    """Context manager for an exclusive file lock."""

    def __init__(self, lockfile, timeout=180):
        """Initialize instance.

        Args:
            lockfile: Path to lockfile
            timeout: Timeout for grabbing lock, in seconds.
        """
        self._lockfile = lockfile
        self._timeout = timeout

    @property
    def _proc_path(self):
        return _procdir.getpath(os.getpid())

    def __enter__(self):
        self._acquire_lock()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._release_lock()

    def _acquire_lock(self):
        """Try to acquire lock within timeout."""
        timeout = time.time() + self._timeout
        self._clean_stale_lock()
        while True:
            try:
                os.symlink(self._proc_path, self._lockfile)
            except OSError as e:
                logger.warning('Error acquiring lock: %s', e)
            else:
                return
            if time.time() > timeout:
                break
            time.sleep(random.random())
        raise Exception('Trying to acquire lock %r timed out.'
                        % (self._lockfile,))

    def _release_lock(self):
        """Release own lock."""
        if os.readlink(self._lockfile) != self._proc_path:
            logger.warning('Lockfile %s does not belong to this process',
                           self._lockfile)
        else:
            os.unlink(self._lockfile)

    def _clean_stale_lock(self):
        """Clean up stale locks."""
        # TODO(ayatane): Old flock(2) lock file handling can be removed
        # after the code has existed for Long Enough that there aren't
        # reasonably any instances of it left on developer or prod
        # machines.
        self._clean_flock_lock()
        self._clean_orphaned_lock()

    def _clean_flock_lock(self):
        """Clean up old flock(2)-based lock."""
        if self._is_lock_flock():
            logger.warning('Removing old style lock file')
            os.unlink(self._lockfile)

    def _clean_orphaned_lock(self):
        """Clean up orphaned lock."""
        if self._is_lock_orphaned():
            logger.warning('Removing orphaned lock')
            os.unlink(self._lockfile)

    def _is_lock_flock(self):
        """Return True if old flock(2) lock exists."""
        return (os.path.isfile(self._lockfile)
                and not os.path.islink(self._lockfile))

    def _is_lock_orphaned(self):
        """Return True if lock is orphaned."""
        return (os.path.islink(self._lockfile)
                and not _is_pid_running(self._get_lock_pid()))

    def _get_lock_pid(self):
        """Return pid of current lock file as int."""
        return _procdir.getpid(os.readlink(self._lockfile))
