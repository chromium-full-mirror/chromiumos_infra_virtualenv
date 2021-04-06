# infra_virtualenv README

[TOC]

This repository provides a common Python virtualenv interface that
Chromium OS infrastructure code can depend on.

## Using virtualenv in another repository

A repository adding virtualenv should mimic this repository, which
itself uses virtualenv for running unit tests.

Key files:

* `bin/python_venv` starts an instance of Python that uses the
  virtualenv.
* `bin/turtle` is an example script for running a Python module using
  `bin/python_venv`.
* `venv/requirements.txt` lists the packages to install inside the
  virtualenv.
* `venv` is added to `PYTHONPATH`. For example, `venv/cros_venv` can
  be imported inside the virtualenv using `import cros_venv`.

To make sure all your requirements are pinned, run:

    bin/python_venv -m pip freeze

Copy the output into `requirements.txt`

Refer to Pip's [documentation](https://pip.pypa.io/en/stable/) for the
`requirements.txt` format.

## Adding packages to be available for use

Packages to be installed inside a virtualenv must first be added to
`pip_packages`.

To add packages, run:

    bin/python_venv -m pip wheel -w pip_packages foo==1.2.3

Refer to Pip's documentation for details on the arguments for `pip`.

If the resultant wheel contains `linux` and not `manylinux`, then it
is NOT portable.  You will need to build a portable wheel; see next
section.

Commit the wheel and make a CL.

## Building portable wheel with C extensions

You need to use the standard manylinux Docker image to build the
portable wheel.

Install Docker:

    http://go/installdocker

Add the manylinux Docker image:

    docker pull quay.io/pypa/manylinux2014_x86_64@sha256:cffd074a33992fb7493f727fda59aebd81e54b8a0e016574ceab054691acdfd0

Get the image ID:

    docker image ls quay.io/pypa/manylinux2014_x86_64

Run the Docker image:

    docker run -i -t -v "$(pwd)/pip_packages:/pip_packages" --rm $IMAGE /bin/bash

Build a portable wheel:

    cd /opt/python/cp27-cp27mu
    bin/pip wheel -w /pip_packages foo==1.2.3
    auditwheel repair --plat manylinux2014_x86_64 -w /pip_packages /pip_packages/foo-1.2.3-cp27-cp27mu-linux_x86_64.whl

Keep the `manylinux` wheel and remove the `linux` wheel.

Since these wheels are built as root inside the container, you may
need to chown the files on the host to prevent permission issues
later:

    sudo chown $(id -un):$(id -gn) pip_packages/*

## Adding third party packages to a virtualenv

Add the packages to `requirements.txt`.  If the packages are not in
`pip_packages` yet, add the packages to `pip_packages`.

## Adding first party modules to a virtualenv's import path

"First party modules" refers to Chromium OS code (anything checked out
by `repo`).

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
may check out repositories in completely different locations.  This
method is not powerful enough to account for these environments.

Modifying `sys.path` is a lot more powerful.  The way to do this is to
add a small bit of code to the `__init__.py` of the package that needs
the import.

Example (do not copy and paste blindly):

    import os
    import sys

    # The path of the package
    PKGDIR = __path__[0]
    # Paths to check
    _PATH1 = os.path.join(PKGDIR, '../foo')
    _PATH2 = '/opt/foo'

    if os.path.exists(_PATH1):
        sys.path.append(_PATH1)
    elif os.path.exists(_PATH2):
        sys.path.append(_PATH2)
    else:
        raise ImportError('foo not found')

You must also add the contents of the other project's
`requirements.txt` to your project.  We do not attempt to resolve
dependencies recursively as that is very difficult.

## Low level API

The `bin/create_venv` script prepares a virtualenv using a
`requirements.txt` file.

    bin/create_venv requirements.txt

The script will print the path to the virtualenv to stdout.  Note that
the output ends with a newline; Bash handles this, but Python does
not.

To run the virtualenv Python, call `bin/python` under the virtualenv
directory.

Together, this might look up:

    venv=$(bin/create_venv requirements.txt)
    ${venv}/bin/python

NOTE: It is not generally safe to run the other scripts in the
virtualenv's `bin` directory due to hard-coded paths.  Instead of
running `bin/pip` for example, use `bin/python -m pip`.
