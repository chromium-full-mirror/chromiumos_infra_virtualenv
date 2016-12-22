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
