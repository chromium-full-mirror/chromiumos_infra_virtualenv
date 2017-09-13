infra_virtualenv README
=======================

This repository provides a common Python virtualenv interface that
infra code (such as chromite) can depend on.

Usage
-----

Virtualenv users should mimic this repository, which itself uses
virtualenv for running unit tests.

1. Create a `venv` directory.  All packages and modules in this
   directory will be importable inside the virtualenv.
2. Create a `requirements.txt` file inside `venv` to list external
   packages to install.
3. Copy `bin/python_venv` and `bin/turtle` which serve as templates.

Adding pre-built packages
-------------------------

To add packages to this repository, run:

    $ bin/python_venv -m pip wheel -w path/to/pip_packages -r path/to/requirements.txt

Commit the changes and make a CL.

Low level API
-------------

The `bin/create_venv` script prepares a virtualenv using a
`requirements.txt` file.

    $ bin/create_venv requirements.txt

The script will print the path to the virtualenv to stdout.  Note that
the output ends with a newline; Bash handles this, but Python does
not.

To run the virtualenv Python, call `bin/python` under the virtualenv
directory.

Together, this might look up:

    $ venv=$(bin/create_venv requirements.txt)
    $ ${venv}/bin/python

NOTE: it is not generally safe to run the other scripts in the
virtualenv's `bin` directory due to hard-coded paths.  Instead of
running `bin/pip` for example, use `bin/python -m pip`.

Adding arbitrary directories to import path
-------------------------------------------

NOTE: Do not use this for third party dependencies (stuff not owned by
ChromiumOS)!  This should only be used to set up imports for stuff we
own.  For example, importing python-MySQL SHOULD NOT use this, but
importing chromite from Autotest MAY use this.

This should be handled by the minimum amount of code in the package's
`__init__.py` file.

Example:

    """Autotest package."""

    import sys

    # Use the minimum amount of logic to find the path to add
    _chromite_parent = 'site-packages'
    sys.path.append(_chromite_parent)

A solid understanding of the Python [import system][1] is recommended
(the link is for Python 3, but it is informative).

[1]: https://docs.python.org/3/reference/import.html

In brief, `__init__.py` is executed whenever a package is imported.  A
package is imported before any submodule or subpackage is imported.  A
package is only imported once per Python process; future imports are
looked up in `sys.modules`.  Thus, `__init__.py` will modify
`sys.path` exactly once and is guaranteed to be run before anything in
that package is imported.
