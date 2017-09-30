# infra_virtualenv README

This repository provides a common Python virtualenv interface that
Chromium OS infrastructure code can depend on.

## Using virtualenv in another repository

A repository adding virtualenv should mimic this repository, which
itself uses virtualenv for running unit tests.

Key files:

* `bin/python_venv` starts an instance of Python that uses the
  virtualenv.
* `bin/turtle` is an example script for running a Python module using
  `bin/python_venv`
* `venv/requirements.txt` lists the packages to install inside the
  virtualenv. Refer to Pip's
  [documentation](https://pip.pypa.io/en/stable/) for the
  `requirements.txt` format.
* `venv` is added to `PYTHONPATH`. For example, `venv/cros_venv` can
  be imported inside the virtualenv using `import cros_venv`.

## Adding packages to be available for use

Packages to be installed inside a virtualenv must first be added to
`pip_packages`.

To add packages, run:

    $ bin/python_venv -m pip wheel -w pip_packages <packages to install>
    
Refer to Pip's documentation for details on the arguments for `pip`.

Commit the added package and make a CL.

## Adding third party packages to a virtualenv

Add the packages to `requirements.txt`.  If the packages are not in
`pip_packages` yet, add the packages to `pip_packages`.

## Adding first party modules to a virtualenv

First party modules refers to Chromium OS code (checked out by `repo`
as a big honking source tree).

NOTE: Do not use this for third party dependencies (stuff not owned by
Chromium OS)!  This should only be used to set up imports for stuff we
own.  For example, importing `python-MySQL` SHOULD NOT use this, but
importing `chromite` MAY use this.

There are two ways to do this:

1. Adding a relative symlink to `venv`.
2. Modifying `sys.path` in `__init__.py`.

Adding a symlink to `venv` is simple and should be self-explanatory.
However, keep in mind that `repo` checkouts may not always have the
same structure, and certain environments such as production servers
may store core in complete different locations.  This method is not
powerful enough to account for these environments.

Modifying `sys.path` is a lot more powerful.  The way to do this is to
add a small bit of code to the `__init__.py` of the package that needs
the import.

Example (do not copy and paste blindly):

    import os
    import sys

    PKGDIR = __path__[0]
    _PATH1 = os.path.join(PKGDIR, '../foo')
    _PATH2 = os.path.join(PKGDIR, '/opt/foo')
    # Use the minimum amount of logic to find the path to add
    if os.path.exists(_PATH1):
        sys.path.append(_PATH1)
    elif os.path.exists(_PATH2):
        sys.path.append(_PATH2)
    else:
        raise ImportError('foo not found')

You must also add the contents of the other project's
`requirements.txt` to your project, as there is no easy way to resolve
recursive dependencies automatically.

## Low level API

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

NOTE: It is not generally safe to run the other scripts in the
virtualenv's `bin` directory due to hard-coded paths.  Instead of
running `bin/pip` for example, use `bin/python -m pip`.
