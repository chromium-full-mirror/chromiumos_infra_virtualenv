# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from cStringIO import StringIO
import os
import unittest
import warnings

import mock

from cros_venv import flock
from cros_venv import testcases
from cros_venv import venvlib


class VenvTmpDirTestCase(testcases.TmpdirTestCase):

    """TestCase for Venv that uses a temp directory."""

    def run(self, result=None):
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            super(VenvTmpDirTestCase, self).run(result)

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

    def test__get_cache_dir(self):
        got = venvlib._get_cache_dir()
        self.assertTrue(got.endswith('/.cache/cros_venv'))

    def test__get_cache_dir_should_be_absolute(self):
        got = venvlib._get_cache_dir()
        self.assertTrue(got.startswith('/'))

    @mock.patch.object(venvlib, 'sys')
    def test__get_python_version(self, sys):
        sys.version_info = (2, 7, 12, 'final', 0)
        self.assertEqual(venvlib._get_python_version(), '2.7.12')


class VenvlibTmpDirTestCase(testcases.TmpdirTestCase):

    """TestCase for venvlib functions that uses a temp directory."""

    def test__makedirs_exist_ok(self):
        """Test _makedirs_exist_ok() ignores existing dir."""
        os.mkdir('foo')
        try:
            venvlib._makedirs_exist_ok('foo')
        except OSError:
            self.fail('OSError raised')

    def test__log_check_call(self):
        with open('tmp', 'w') as f:
            venvlib._log_check_call(['echo', 'hi'], logfile=f)
        with open('tmp', 'r') as f:
            self.assertEqual(f.read(), "Running [u'echo', u'hi']\nhi\n")


class VenvPathsTestCase(unittest.TestCase):

    """Tests for _VenvPaths."""

    def test_repr(self):
        paths = venvlib._VenvPaths('/tmp')
        self.assertEqual(repr(paths),
                         "_VenvPaths(u'/tmp')")

    def test_venvdir(self):
        """Test for venvdir attribute."""
        paths = venvlib._VenvPaths('/tmp')
        self.assertEqual(paths.venvdir, '/tmp')

    def test_python(self):
        """Test for python attribute."""
        paths = venvlib._VenvPaths('/tmp')
        self.assertEqual(paths.python, '/tmp/bin/python')

    def test_lockfile(self):
        """Test for lockfile attribute."""
        paths = venvlib._VenvPaths('/tmp')
        self.assertEqual(paths.lockfile, '/tmp/change.lock')

    def test_logfile(self):
        """Test for logfile attribute."""
        paths = venvlib._VenvPaths('/tmp')
        self.assertEqual(paths.logfile, '/tmp/create.log')

    def test_spec(self):
        """Test for spec attribute."""
        paths = venvlib._VenvPaths('/tmp')
        self.assertEqual(paths.spec, '/tmp/spec.json')


class VersionedVenvTestCase(unittest.TestCase):

    """Tests for VersionedVenv."""

    def test_repr(self):
        spec = venvlib._VenvSpec('1.7.6', 'foo==1.0.0\n')
        venv = venvlib.VersionedVenv(spec)
        with mock.patch.object(venvlib._VenvSpec, '__repr__') as venv_repr:
            venv_repr.return_value = 'foo'
            self.assertEqual(repr(venv),
                             "VersionedVenv(foo)")


class VersionedVenvTmpDirTestCase(testcases.TmpdirTestCase):

    """Tests for VersionedVenv that use a temp directory."""

    def setUp(self):
        super(VersionedVenvTmpDirTestCase, self).setUp()
        patcher = mock.patch.object(venvlib, '_get_cache_dir')
        get_cache_dir = patcher.start()
        self.addCleanup(patcher.stop)
        get_cache_dir.return_value = os.getcwd()

    @mock.patch.object(venvlib.VersionedVenv, '_create')
    @mock.patch.object(venvlib.VersionedVenv, '_check')
    def test__check_or_create_should_create_missing_dir(self, check, create):
        """Test that _check_or_create() creates when directory is missing."""
        spec = venvlib._VenvSpec('1.7.6', 'foo==1.0.0\n')
        venv = venvlib.VersionedVenv(spec)
        venv._check_or_create()
        check.assert_not_called()
        create.assert_called_once_with()

    @mock.patch.object(venvlib.VersionedVenv, '_create')
    @mock.patch.object(venvlib.VersionedVenv, '_check')
    def test__check_or_create_should_create_missing_spec(self, check, create):
        """Test that _check_or_create() creates when spec file is missing."""
        spec = venvlib._VenvSpec('1.7.6', 'foo==1.0.0\n')
        venv = venvlib.VersionedVenv(spec)
        venvdir = 'venv-1.7.6-5442279a613e6a2c4a93c9bda10e63f4'
        os.mkdir(venvdir)
        venv._check_or_create()
        check.assert_not_called()
        create.assert_called_once_with()

    @mock.patch.object(venvlib.VersionedVenv, '_create')
    @mock.patch.object(venvlib.VersionedVenv, '_check')
    def test__check_or_create_should_check_with_spec(self, check, create):
        """Test that _check_or_create() creates when spec file is missing."""
        spec = venvlib._VenvSpec('1.7.6', 'foo==1.0.0\n')
        venv = venvlib.VersionedVenv(spec)
        venvdir = 'venv-1.7.6-5442279a613e6a2c4a93c9bda10e63f4'
        os.mkdir(venvdir)
        with open(venvdir + '/spec.json', 'w') as f:
            f.write('["1.7.6", "foo==1.0.0\\n"]')
        venv._check_or_create()
        check.assert_called_once_with(spec)
        create.assert_not_called()

    def test__check_should_pass_with_same_spec(self):
        """Test that _check() passes when spec matches."""
        spec = venvlib._VenvSpec('1.7.6', 'foo==1.0.0\n')
        venv = venvlib.VersionedVenv(spec)
        try:
            venv._check(spec)
        except venvlib.SpecMismatchError:
            self.fail('Check did not pass')

    def test__check_should_fail_with_different_spec(self):
        """Test that _check() fails when spec does not match."""
        spec = venvlib._VenvSpec('1.7.6', 'foo==1.0.0\n')
        venv = venvlib.VersionedVenv(spec)
        with self.assertRaises(venvlib.SpecMismatchError):
            venv._check(venvlib._VenvSpec('1.7.6', 'foo=2.0.0\n'))

    def test_dump_spec_and_load_spec(self):
        spec = venvlib._VenvSpec('1.7.6', 'foo==1.0.0\n')
        venv = venvlib.VersionedVenv(spec)
        os.mkdir(venv._paths.venvdir)
        venv._dump_spec()
        got = venv._load_spec()
        self.assertEqual(spec, got)


class VenvSpecTestCase(unittest.TestCase):

    """Tests for _VenvSpec."""

    def test_eq(self):
        self.assertEqual(
            venvlib._VenvSpec('2.7.3', 'foo==1.0.0\n'),
            venvlib._VenvSpec('2.7.3', 'foo==1.0.0\n'),
        )

    def test_not_eq(self):
        self.assertNotEqual(
            venvlib._VenvSpec('2.7.3', 'foo==1.0.0\n'),
            venvlib._VenvSpec('2.7.4', 'foo==1.0.0\n'),
        )

    @mock.patch.object(venvlib, '_get_python_version')
    def test_make_spec(self, get_ver):
        f = StringIO('foo==1.0.0\n')
        get_ver.return_value = '1.7.6'
        self.assertEqual(
            venvlib.make_spec(f),
            venvlib._VenvSpec('1.7.6', 'foo==1.0.0\n')
        )

    def test__get_reqs_hash(self):
        spec = venvlib._VenvSpec('1.7.6', 'foo==1.0.0\n')
        self.assertEqual(venvlib._get_reqs_hash(spec),
                         '5442279a613e6a2c4a93c9bda10e63f4')

    @mock.patch.object(venvlib, '_get_cache_dir')
    def test__get_venvdir(self, get_cache_dir):
        get_cache_dir.return_value = '/home/arland/.cache/cros_venv'
        spec = venvlib._VenvSpec('1.7.6', 'foo==1.0.0\n')
        got = venvlib._get_venvdir(spec)
        self.assertEqual(
            got,
            '/home/arland/.cache/cros_venv'
            '/venv-1.7.6-5442279a613e6a2c4a93c9bda10e63f4')

    def test__get_venvdir_should_be_absolute(self):
        spec = venvlib._VenvSpec('1.7.6', 'foo==1.0.0\n')
        got = venvlib._get_venvdir(spec)
        self.assertTrue(got.startswith('/'))

    def test_dump_spec_and_load_spec(self):
        spec = venvlib._VenvSpec('1.7.6', 'foo==1.0.0\n')
        f = StringIO()
        venvlib._dump_spec(spec, f)
        f.seek(0)
        got = venvlib._load_spec(f)
        self.assertEqual(spec, got)

    def test__make_reqs_file_should_cleanup(self):
        spec = venvlib._VenvSpec('1.7.6', 'foo==1.0.0\n')
        with venvlib._make_reqs_file(spec) as f:
            self.assertTrue(os.path.exists(f.name))
        self.assertFalse(os.path.exists(f.name))

    def test__make_reqs_file_content(self):
        spec = venvlib._VenvSpec('1.7.6', 'foo==1.0.0\n')
        with venvlib._make_reqs_file(spec) as f, \
             open(f.name, 'r') as rfile:
            self.assertEqual(rfile.read(),
                             'setuptools==28.2.0\npip==8.1.2\nfoo==1.0.0\n')
