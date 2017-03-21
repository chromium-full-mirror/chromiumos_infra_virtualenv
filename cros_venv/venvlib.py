# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Virtualenv management"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import collections
import functools
import hashlib
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile
import warnings

from cros_venv import constants
from cros_venv import flock

_PACKAGE_DIR = os.path.join(constants.REPO_DIR, 'pip_packages')
_VENV_PY = '/usr/bin/python2.7'

# BASE_DEPENDENCIES are pip requirements automatically included in every
# virtualenv so we have control over which versions of bootstrap
# packages are installed.
_BASE_DEPENDENCIES = ('setuptools==28.2.0', 'pip==8.1.2')


class Venv(object):
    """Wraps all operations on a virtualenv directory."""

    def __init__(self, venv_dir, reqs_file):
        warnings.warn('Venv is deprecated; use VersionedVenv instead')
        self._venv_dir = venv_dir
        self._reqs_file = reqs_file

    @property
    def _venv_python(self):
        return os.path.join(self._venv_dir, 'bin', 'python')

    @property
    def _lock_file(self):
        return os.path.join(self._venv_dir, '.create_venv.lock')

    @property
    def _installed_reqs_file(self):
        return os.path.join(self._venv_dir, '.installed.txt')

    def _lock(self):
        """Return lock context for the virtualenv."""
        return flock.FileLock(self._lock_file)

    def ensure(self):
        """Create or update virtualenv."""
        _makedirs_exist_ok(self._venv_dir)
        with self._lock():
            if not self._venv_initialized():
                self._init_venv()
            if not self._reqs_up_to_date():
                self._install_reqs()

    def _venv_initialized(self):
        """Check if virtualenv is initialized properly."""
        return os.path.exists(self._venv_python)

    def _init_venv(self):
        """Initialize virtualenv."""
        subprocess.check_call([
            'virtualenv', self._venv_dir,
            '-p', _VENV_PY,
            '--extra-search-dir', _PACKAGE_DIR,
            # TODO(ayatane): Ubuntu Precise ships with virtualenv 1.7,
            # which requires specifying --setuptools, else distribute is
            # used (distribute is deprecated).  virtualenv after 1.10
            # uses setuptools by default.  virtualenv >1.10 accepts the
            # --setuptools option but does not document it.  Once we no
            # longer have any hosts on virtualenv 1.7, the --setuptools
            # option can be removed.
            '--setuptools'])

    def _reqs_up_to_date(self):
        """Return whether the virtualenv reqs file is up to date."""
        if not os.path.exists(self._installed_reqs_file):
            return False
        with open(self._installed_reqs_file) as installed, \
             open(self._reqs_file) as specified:
            return _iter_equal(installed, specified)

    def _install_reqs(self):
        """Install indicated packages into virtualenv.

        The corresponding requirements file is also copied after
        installation.
        """
        subprocess.check_call(
            [self._venv_python, '-m', 'pip', 'install',
             '--no-index', '-f', 'file://' + _PACKAGE_DIR]
            + list(_BASE_DEPENDENCIES)
            + ['-r', self._reqs_file]
        )
        shutil.copyfile(self._reqs_file, self._installed_reqs_file)


class _VenvPaths(object):

    """Wrapper defining paths inside a versioned virtualenv."""

    def __init__(self, venvdir):
        """Initialize instance.

        venvdir is the absolute path to a virtualenv.
        """
        self.venvdir = venvdir

    def __repr__(self):
        return '{cls}({this.venvdir!r})'.format(
            cls=type(self).__name__,
            this=self,
        )

    @property
    def python(self):
        """Path to the virtualenv's Python binary."""
        return os.path.join(self.venvdir, 'bin', 'python')

    @property
    def lockfile(self):
        """Path to lock file for changing virtualenv."""
        return os.path.join(self.venvdir, 'change.lock')

    @property
    def logfile(self):
        """Path to log file for creating virtualenv."""
        return os.path.join(self.venvdir, 'create.log')

    @property
    def spec(self):
        """Path to spec file inside virtualenv directory."""
        return os.path.join(self.venvdir, 'spec.json')


class VersionedVenv(object):

    """Versioned virtualenv, specified by a _VenvSpec.

    This class provides a method for ensuring the versioned virtualenv
    is created.
    """

    def __init__(self, spec):
        """Initialize instance.

        spec is a _VenvSpec.
        """
        self._spec = spec
        self._paths = _VenvPaths(_get_venvdir(spec))

    def __repr__(self):
        return '{cls}({this._spec!r})'.format(
            cls=type(self).__name__,
            this=self,
        )

    def ensure(self):
        """Ensure that the virtualenv exists."""
        _makedirs_exist_ok(self._paths.venvdir)
        with flock.FileLock(self._paths.lockfile):
            self._check_or_create()
        return self._paths.venvdir

    def _check_or_create(self):
        """Check virtualenv, creating it if it is not created."""
        try:
            existing_spec = self._load_spec()
        except IOError:
            self._create()
        else:
            self._check(existing_spec)

    def _create(self):
        """Create virtualenv."""
        with open(self._paths.logfile, 'w') as logfile, \
             _make_reqs_file(self._spec) as reqs_file:
            _create_venv(venvdir=self._paths.venvdir,
                         logfile=logfile)
            _install_reqs_file(python_path=self._paths.python,
                               reqs_path=reqs_file.name,
                               logfile=logfile)
        self._dump_spec()

    def _check(self, spec):
        """Check if the given spec matches our spec.

        Raise SpecMismatchError if check fails.
        """
        if spec != self._spec:
            raise SpecMismatchError

    def _dump_spec(self):
        """Save the _VenvSpec to the virtualenv on disk."""
        with open(self._paths.spec, 'w') as f:
            return _dump_spec(self._spec, f)

    def _load_spec(self):
        """Return the _VenvSpec for the virtualenv on disk."""
        with open(self._paths.spec, 'r') as f:
            return _load_spec(f)


class SpecMismatchError(Exception):
    """Versioned virtualenv specs do not match."""


_VenvSpec = collections.namedtuple('_VenvSpec', 'py_version,reqs')


def make_spec(f):
    """Make _VenvSpec from a requirements file object."""
    return _VenvSpec(_get_python_version(), f.read())


def _get_reqs_hash(spec):
    """Return hash string for _VenvSpec requirements.

    Make sure to check for collisions.
    """
    hasher = hashlib.md5()
    hasher.update(spec.reqs)
    return hasher.hexdigest()


def _get_venvdir(spec):
    """Return the virtualenv directory to use for the _VenvSpec.

    Returns absolute path.
    """
    cache_dir = _get_cache_dir()
    return os.path.join(
        cache_dir, 'venv-%s-%s' % (spec.py_version, _get_reqs_hash(spec)))


def _dump_spec(spec, f):
    """Dump _VenvSpec to a file."""
    json.dump(spec, f)


def _load_spec(f):
    """Load _VenvSpec from a file."""
    return _VenvSpec._make(json.load(f))


def _make_reqs_file(spec):
    """Return a temporary reqs file for the virtualenv spec.

    The return value is a tempfile.NamedTemporaryFile, which cleans
    up on close.  The filename is accessible via the name attribute.
    """
    f = tempfile.NamedTemporaryFile('w')
    f.writelines(req + '\n' for req in _BASE_DEPENDENCIES)
    f.write(spec.reqs)
    f.flush()
    return f


def _create_venv(venvdir, logfile):
    """Create a virtualenv at the given path."""
    # TODO(ayatane): Ubuntu Precise ships with virtualenv 1.7, which
    # requires specifying --setuptools, else distribute is used
    # (distribute is deprecated).  virtualenv after 1.10 uses setuptools
    # by default.  virtualenv >1.10 accepts the --setuptools option but
    # does not document it.  Once we no longer have any hosts on
    # virtualenv 1.7, the --setuptools option can be removed.
    command = ['virtualenv', venvdir, '-p', _VENV_PY,
               '--extra-search-dir', _PACKAGE_DIR, '--setuptools']
    _log_check_call(command, logfile=logfile)


def _install_reqs_file(python_path, reqs_path, logfile):
    """Install reqs file using pip."""
    command = [python_path, '-m', 'pip', 'install',
               '--no-index', '-f', 'file://' + _PACKAGE_DIR, '-r', reqs_path]
    _log_check_call(command, logfile=logfile)


def _add_call_logging(call_func):
    """Wrap a subprocess-style call with logging."""
    @functools.wraps(call_func)
    def wrapped_command(args, logfile, **kwargs):
        """Logging-wrapped call.

        Arguments are similar to subprocess.Popen, depending on the
        underlying call.  There is an extra keyword-only parameter
        logfile, which takes a file object.
        """
        logfile.write('Running %r\n' % (args,))
        logfile.flush()
        call_func(args, stdout=logfile, **kwargs)
    return wrapped_command


_log_check_call = _add_call_logging(subprocess.check_call)


def _get_python_version():
    """Return the version string for the current Python."""
    return '.'.join(unicode(part) for part in sys.version_info[:3])


def _get_cache_dir():
    """Get cache dir to use for cros_venv.

    Returns absolute path.
    """
    return os.path.expanduser('~/.cache/cros_venv')


def _iter_equal(first, second):
    """Return whether two iterables are equal.

    If one iterable is shorter, it will be filled with None and compared
    with the other.
    """
    return all(x == y for x, y in itertools.izip_longest(first, second))


def _makedirs_exist_ok(path):
    """Make directories recursively, ignoring if directory already exists."""
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise
