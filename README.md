infra_virtualenv README
=======================

This repository provides a common Python virtualenv interface that
infra code (such as chromite) can depend on.  At this point, it is
experimental and not yet used in production.

Virtualenv users should create a `requirements.txt` file listing the
packages that they need and use the wrapper scripts (described below)
to create the virtualenv and run commands within it.

To add packages to this repository, run:

    $ pip wheel -w path/to/pip_packages -r path/to/requirements.txt

Commit the changes and make a CL.

For example for chromite, from within `chromite/virtualenv`, run:

    $ pip wheel -w pip_packages -r requirements.txt

Wrapper scripts
---------------

`create_venv` creates or updates a virtualenv using a
`requirements.txt` file.

    $ create_venv .venv requirements.txt

To run the virtualenv python, use:

    $ .venv/bin/python

NOTE: it is not generally safe to run the other scripts in `.venv/bin`
due to the hard-coded paths in the virtualenv.  Instead of running
`.venv/bin/pip` for example, use `.venv/bin/python -m pip`.

Here’s a complete example:

    $ echo mock==2.0.0 > requirements.txt
    $ ./create_venv .venv requirements.txt
    $ .venv/bin/python
    Python 2.7.6 (default, Jun 22 2015, 17:58:13)
    [GCC 4.8.2] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import sys
    >>> sys.prefix  # This points to the virtualenv now
    '/usr/local/google/home/ayatane/src/chromiumos/infra_virtualenv/.venv'
    >>> import mock

Adding arbitrary directories to import path
-------------------------------------------

NOTE: Do not use this for third party dependencies (stuff not owned by
ChromiumOS)!  This should only be used to set up imports for stuff we
own.  For example, importing python-MySQL should NOT use this, but
importing chromite from Autotest may use this.

This should be handled by the minimum amount of code in the package's
`__init__.py` file.

Example:

    """Autotest package."""

    import sys

    # Use the minimum amount of logic to find the path to add
    _chromite_parent = 'site-packages'
    sys.path.append(_chromite_parent)

A solid understanding of the [Python import system](https://docs.python.org/3/reference/import.html)
is recommended (link is for Python 3, but is informative).

In brief, `__init__.py` is executed whenever the package is imported.
The package is imported before any submodule or subpackage is
imported.  The package is only imported once per Python process;
future imports get the "cached" "singleton" package object.  Thus,
`__init__.py` will modify `sys.path` exactly once and is guaranteed to
be run before anything in that package is used.

Background for __init__.py recommended usage
--------------------------------------------

(Updated on 2017-02-21)

Previously, we set up the import path for first party modules by
patching sys.path in very creative ways.  This tends to cause
problems.

In the original virtualenv design, first party packages would be
handled by using `pip -e` to install the packages inside the
virtualenv in editable mode.  However, the implementation of this is
wonky, buggy, and generally considered a second citizen to installing
packages "properly".  The blocking issue is that pip -e must copy the
entire source tree internally, all for writing a metadata file and
what amounts to a symlink.  This takes a considerable amount of time
for large packages such as chromite (the .git directory is copied
also).  This is not trivially fixed upstream, and the editable
installs feature is not considered a top priority.

Thus, the reason for adding our own import path patching is to work
around pip while solving our existing woes.

A test concept of the feature was implemented using .pth files, which
are simple files that contain paths to add to Python’s import path.

The problem with this implementation is that our code is run in a lot
of really weird configurations.  Having a single .pth file may not be
good enough.  While relative paths are supported (and sane), some of
the places our code is run do not use the same file system hierarchy.
Also, there is no simple way to handle recursive requirements.

Thus, going forward, the standard way to support first party imports
is a small bit of `sys.path` patching code in the respective package’s
`__init__.py` file.  This enable the use of Python's full power for
handling weird environments as needed; a little logic goes a long way.
A lot of other things also just work due to `__init__.py` file
semantics: for example, recursive requirements.
