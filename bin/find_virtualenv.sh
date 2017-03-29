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
# exec_python_module -- Execute Python module inside of virtualenv
#
# This script is a canonical template that can be copied to other
# repositories.  The venv_repo variable should be changed to point to
# this repository.
set -eu

realpath() {
    readlink -f -- "$1"
}

# venv_repo should be changed if this script is copied to other repos.
readonly venv_repo=$(realpath ..)
readonly create_script=$(realpath "${venv_repo}/bin/create_venv")
readonly venv_home=$(realpath ../venv)
readonly reqs_file=$(realpath "${venv_home}/requirements.txt")

exec_python_module() {
    venvdir=$("${create_script}" "$reqs_file")
    export PYTHONPATH=${venv_home}
    exec "${venvdir}/bin/python" -m "$@"
}
