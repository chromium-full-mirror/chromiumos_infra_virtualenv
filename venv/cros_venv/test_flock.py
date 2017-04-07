# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import errno
import fcntl
import logging
import mock
import os
import unittest

from cros_venv import testcases
from cros_venv import flock


_nullhandler = logging.NullHandler()


def setUpModule():
    flock.logger.addHandler(_nullhandler)


def tearDownModule():
    flock.logger.removeHandler(_nullhandler)


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
    """Tests for flock."""

    def test_symlink_fail(self):
        """Test that symlink raises OSError when it already exists."""
        os.symlink('tmp', 'foo')
        with self.assertRaises(OSError):
            os.symlink('tmp', 'foo')

    def test_FileLock(self):
        """Test that FileLock acquires and releases lock."""
        self.assertFalse(os.path.lexists('lockfile'))
        with flock.FileLock('lockfile', timeout=0):
            self.assertTrue(os.path.lexists('lockfile'))
        self.assertFalse(os.path.lexists('lockfile'))

    def test_FileLock_proc_target(self):
        """Test that FileLock lock points to process /proc."""
        with flock.FileLock('lockfile', timeout=0):
            self.assertEqual(os.readlink('lockfile'),
                             '/proc/' + str(os.getpid()))

    def test_FileLock_timeout(self):
        """Test that FileLock raises exception on timeout."""
        os.symlink('tmp', 'lockfile')
        with self.assertRaises(Exception):
            with flock.FileLock('lockfile', timeout=0):
                pass

    def test__release_lock(self):
        """Test _release_lock()."""
        file_lock = flock.FileLock('lockfile')
        os.symlink(file_lock._proc_path, 'lockfile')
        file_lock._release_lock()
        self.assertFalse(os.path.lexists('lockfile'))

    def test__release_lock_other_process(self):
        """Test _release_lock() ignores other process's lock."""
        file_lock = flock.FileLock('lockfile')
        os.symlink('/proc/1', 'lockfile')
        file_lock._release_lock()
        self.assertTrue(os.path.lexists('lockfile'))

    def test__get_lock_pid(self):
        """Test _get_lock_pid."""
        file_lock = flock.FileLock('lockfile')
        os.symlink('/proc/1', 'lockfile')
        self.assertEqual(file_lock._get_lock_pid(), 1)

    def test__is_lock_orphaned_own_lock(self):
        """Test _is_lock_orphaned() with own lock."""
        file_lock = flock.FileLock('lockfile')
        os.symlink(file_lock._proc_path, 'lockfile')
        self.assertFalse(file_lock._is_lock_orphaned())

    def test__is_lock_orphaned_missing(self):
        """Test _is_lock_orphaned() with missing lock."""
        file_lock = flock.FileLock('lockfile')
        self.assertFalse(file_lock._is_lock_orphaned())

    @mock.patch.object(flock, '_is_pid_running')
    def test__is_lock_orphaned(self, is_running):
        """Test _is_lock_orphaned()."""
        is_running.return_value = False
        file_lock = flock.FileLock('lockfile')
        os.symlink(file_lock._proc_path, 'lockfile')
        self.assertTrue(file_lock._is_lock_orphaned())

    def test__is_lock_flock(self):
        """Test _is_lock_flock()."""
        file_lock = flock.FileLock('lockfile')
        with open('lockfile', 'w') as _f:
            pass
        self.assertTrue(file_lock._is_lock_flock())

    def test__is_lock_flock_symlink(self):
        """Test _is_lock_flock() with symlink lock."""
        file_lock = flock.FileLock('lockfile')
        os.symlink(file_lock._proc_path, 'lockfile')
        self.assertFalse(file_lock._is_lock_flock())

    def test__is_lock_flock_missing(self):
        """Test _is_lock_flock() with missing lock."""
        file_lock = flock.FileLock('lockfile')
        self.assertFalse(file_lock._is_lock_flock())

    @mock.patch.object(flock, '_is_pid_running')
    def test__clean_orphaned_lock(self, is_running):
        """Test _clean_orphaned_lock()."""
        is_running.return_value = False
        file_lock = flock.FileLock('lockfile')
        os.symlink('/proc/1', 'lockfile')
        file_lock._clean_orphaned_lock()
        self.assertFalse(os.path.lexists('lockfile'))

    @mock.patch.object(flock, '_is_pid_running')
    def test__clean_orphaned_lock_owned(self, is_running):
        """Test _clean_orphaned_lock() ignores owned lock."""
        is_running.return_value = True
        file_lock = flock.FileLock('lockfile')
        os.symlink('/proc/1', 'lockfile')
        file_lock._clean_orphaned_lock()
        self.assertTrue(os.path.lexists('lockfile'))

    def test__clean_flock_lock(self):
        """Test _clean_flock_lock()."""
        file_lock = flock.FileLock('lockfile')
        with open('lockfile', 'w') as _f:
            pass
        file_lock._clean_flock_lock()
        self.assertFalse(os.path.exists('lockfile'))

    def test__clean_flock_lock_symlink(self):
        """Test _clean_flock_lock() skips symlink lock."""
        file_lock = flock.FileLock('lockfile')
        os.symlink('/proc/1', 'lockfile')
        file_lock._clean_flock_lock()
        self.assertTrue(os.path.exists('lockfile'))
