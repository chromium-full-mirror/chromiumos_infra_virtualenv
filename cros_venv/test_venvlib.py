# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import unittest

from cros_venv import testcases
from cros_venv import venvlib


class VenvTmpDirTestCase(testcases.TmpdirTestCase):

    """TestCase for Venv that uses a temp directory."""

    def test__reqs_up_to_date(self):
        """Test _reqs_up_to_date()."""
        venv = venvlib.Venv('.', 'reqs.txt')
        os.makedirs('lib/python2.7/site-packages')
        with open('reqs.txt', 'w') as f:
            f.write('mir.qualia==1.2.3\n')
        with open('.installed.txt', 'w') as f:
            f.write('mir.qualia==1.2.3\n')
        self.assertTrue(venv._reqs_up_to_date())

    def test__reqs_up_to_date_missing(self):
        """Test _reqs_up_to_date() with missing installed reqs."""
        venv = venvlib.Venv('.', 'reqs.txt')
        self.assertFalse(venv._reqs_up_to_date())

    def test__reqs_up_to_date_different(self):
        """Test _reqs_up_to_date() with different installed reqs."""
        venv = venvlib.Venv('.', 'reqs.txt')
        os.makedirs('lib/python2.7/site-packages')
        with open('reqs.txt', 'w') as f:
            f.write('mir.qualia==1.2.4\n')
        with open('.installed.txt', 'w') as f:
            f.write('mir.qualia==1.2.3\n')
        self.assertFalse(venv._reqs_up_to_date())

    def test__venv_initialized(self):
        """Test _venv_initialized()."""
        venv = venvlib.Venv('.', 'reqs.txt')
        os.makedirs('bin')
        with open('bin/python', 'wb') as f:
            f.write(b'python binary')
        self.assertTrue(venv._venv_initialized())

    def test__venv_initialized_missing(self):
        """Test _venv_initialized() with missing bin/python."""
        venv = venvlib.Venv('.', 'reqs.txt')
        self.assertFalse(venv._venv_initialized())


class VenvlibTestCase(unittest.TestCase):

    """TestCase for venvlib functions."""

    def test__PACKAGE_DIR(self):
        """Test that _PACKAGE_DIR exists."""
        self.assertTrue(os.path.isdir(venvlib._PACKAGE_DIR))

    def test__iter_equal(self):
        """Test when _iter_equal() is True."""
        self.assertTrue(venvlib._iter_equal(
            iter(['foo', 'bar']),
            iter(['foo', 'bar']),
        ))

    def test__iter_equal_wrong_length(self):
        """Test when _iter_equal() is False due to length."""
        self.assertFalse(venvlib._iter_equal(
            iter(['foo', 'bar', 'baz']),
            iter(['foo', 'bar']),
        ))

    def test__iter_equal_fill_with_None(self):
        """Test that _iter_equal() is True due to filling with None."""
        self.assertTrue(venvlib._iter_equal(
            iter(['foo', 'bar', None]),
            iter(['foo', 'bar']),
        ))

    def test__iter_equal_wrong_value(self):
        """Test when _iter_equal() is False due to value."""
        self.assertFalse(venvlib._iter_equal(
            iter(['foo', 'baz']),
            iter(['foo', 'bar']),
        ))


class VenvlibTmpDirTestCase(testcases.TmpdirTestCase):

    """TestCase for venvlib functions that uses a temp directory."""

    def test__makedirs_exist_ok(self):
        """Test _makedirs_exist_ok() ignores existing dir."""
        os.mkdir('foo')
        try:
            venvlib._makedirs_exist_ok('foo')
        except OSError:
            self.fail('OSError raised')
