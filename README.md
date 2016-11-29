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

This repository contains two scripts for working with Python virtualenvs.

`venv_command` runs a command in a virtualenv environment.  This is more
convenient than having to start a shell and source `bin/activate`.
For example, to start Python inside the virtualenv:

    $ venv_command path/to/venv python

`create_venv` creates or updates a virtualenv using a `requirements.txt` file.

    $ create_venv path/to/venv path/to/requirements.txt

Here’s a complete example:

    $ echo mock=2.0.0 > requirements.txt
    $ ./create_venv venv requirements.txt
    $ ./venv_command venv python
    Python 2.7.6 (default, Jun 22 2015, 17:58:13)
    [GCC 4.8.2] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import mock
    >>>
