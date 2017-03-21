#!/bin/bash
# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# Find the virtualenv repo to use.
#
# This is meant to be sourced in scripts that need virtualenv.  The
# sourcing script should cd into the directory containing this script
# first.  This script defines functions for performing common tasks:
#
# exec_python -- Execute Python module inside of virtualenv
set -eu

realpath() {
    readlink -f -- "$1"
}

readonly virtualenv_dir=$(realpath ..)
readonly venv_dir=$(realpath ../venv/.venv)
readonly reqs_file=$(realpath ../venv/requirements.txt)

_create_venv() {
    "$virtualenv_dir/create_venv" "$venv_dir" "$reqs_file" >&2
}

exec_python_module() {
    _create_venv
    export PYTHONPATH='../venv'
    exec "$venv_dir/bin/python" -m "$@"
}
