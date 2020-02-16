# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import errno
import fcntl
import logging
import os
import sys
import unittest

import mock

if sys.version_info.major < 3:
    import subprocess32 as subprocess
else:
    import subprocess

from cros_venv import testcases
from cros_venv import flock

logger = logging.getLogger(__name__)
_log_handler = None


def setUpModule():
    global _log_handler
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    _log_handler = logging.StreamHandler()
    _log_handler.setFormatter(logging.Formatter(
        '%(asctime)s:%(levelname)s:%(message)s'))
    root.addHandler(_log_handler)


def tearDownModule():
    root = logging.getLogger()
    root.removeHandler(_log_handler)
    root.setLevel(logging.WARNING)


class ProcDirTestCase(unittest.TestCase):
    """Tests for _ProcDir."""

    def test_getpath(self):
        """Test getpath()."""
        got = flock._procdir.getpath(123)
        self.assertEqual(got, '/proc/123')

    def test_getpid(self):
        """Test getpid()."""
        got = flock._procdir.getpid('/proc/123')
        self.assertEqual(got, 123)


class IsPidRunningTestCase(unittest.TestCase):
    """Tests for _is_pid_running()."""

    @mock.patch('os.kill')
    def test_no_such_process(self, kill):
        """Test _is_pid_running() when no such process."""
        kill.side_effect = OSError(errno.ESRCH, '')
        self.assertFalse(flock._is_pid_running(1))

    @mock.patch('os.kill')
    def test_operation_not_permitted(self, kill):
        """Test _is_pid_running() when operation not permitted."""
        kill.side_effect = OSError(errno.EPERM, '')
        self.assertTrue(flock._is_pid_running(1))

    @mock.patch('os.kill')
    def test_okay(self, _kill):
        """Test _is_pid_running() when operation not permitted."""
        self.assertTrue(flock._is_pid_running(1))


class FileLockTestCase(testcases.TmpdirTestCase):
    """Tests for flock (provide code coverage, not full functional testing)."""

    def test_happy_path(self):
        """Test happy path."""
        with flock.FileLock('lockfile', timeout=0):
            pass

    def test_other_process_has_lock(self):
        """Test with other process holding lock."""
        logger.debug('Starting test')
        with _lock('lockfile'):
            with self.assertRaises(flock.TimeoutError):
                with flock.FileLock('lockfile', timeout=0):
                    pass  # pragma: no cover

    def test_with_stale_symlink_lock(self):
        """Test with existing symlink lock.

        TODO(ayatane): Old symlink lock file handling can be removed,
        see flock.py
        """
        os.symlink('/proc/99999', 'lockfile')
        with mock.patch.object(flock, '_is_pid_running',
                               autospec=True) as running:
            running.return_value = False
            with flock.FileLock('lockfile', timeout=0):
                pass
        self.assertFalse(os.path.islink('lockfile'))

    def test_with_active_symlink_lock(self):
        """Test with existing symlink lock.

        TODO(ayatane): Old symlink lock file handling can be removed,
        see flock.py
        """
        os.symlink('/proc/99999', 'lockfile')
        with mock.patch.object(flock, '_is_pid_running',
                               autospec=True) as running:
            running.return_value = True
            with self.assertRaises(flock.TimeoutError):
                with flock.FileLock('lockfile', timeout=0):
                    pass  # pragma: no cover


class TimeoutErrorTestCase(unittest.TestCase):
    """Tests for Timeout Error"""

    def test_str(self):
        """Test basic error string contents."""
        e = flock.TimeoutError(filename='foo', timeout=123)
        self.assertIn('foo', str(e))
        self.assertIn('123', str(e))


_LOCK_SCRIPT = """\
import fcntl
import os
import time

fd = os.open(%(filename)r, os.O_CREAT | os.O_RDWR)
fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
print('hi')
while True:
    time.sleep(10)
"""


@contextlib.contextmanager
def _lock(filename):
    """Lock a file in another process for testing."""
    logger.debug('Grabbing external lock on %s', filename)
    with subprocess.Popen(
            ['python', '-u', '-c', _LOCK_SCRIPT % {'filename': filename}],
            stdout=subprocess.PIPE) as proc:
        logger.debug('Started external lock process for %s', filename)
        proc.stdout.readline()
        logger.debug('Finished grabbing external lock on %s', filename)
        yield proc
        logger.debug('Releasing external lock on %s', filename)
        proc.terminate()
