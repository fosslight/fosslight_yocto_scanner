#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Android binary analysis script
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import pytest


@pytest.fixture(scope="module")
def test_environment(run_command):

    # given
    run_command("rm -rf test_result")
    os.makedirs("test_result", exist_ok=True)
    
    env_commands = [
        (
            "fosslight_yocto -ip test_files/installed-packages.txt "
            "-i test_files/installed-package-names.txt "
            "-b test_files/bom.json -p test_files/packages "
            "-y test_files/oss-pkg-info2.yaml -o test_result/yocto2.xlsx -n"
        ),
        (
            "fosslight_yocto -ip test_files/installed-packages.txt "
            "-i test_files/installed-package-names.txt "
            "-b test_files/bom.json -p test_files/packages "
            "-y test_files/oss-pkg-info.yaml -o test_result/yocto.xlsx"
        ),
        (
            "fosslight_yocto -ip test_files/installed-packages.txt "
            "-i test_files/installed-package-names.txt "
            "-b test_files/bom.json -p test_files/packages -o test_result"
        )
    ]
    
    for command in env_commands:

        # when
        success, stdout, stderr = run_command(command)

        # then 
        assert success, f"Command failed:\n{command}\nStdout: {stdout}\nStderr: {stderr}"


@pytest.mark.release
def test_release_environment(run_command, test_environment):

    # when
    help_result, _, _ = run_command("fosslight_yocto -h")
    double_help_result, _, _ = run_command("fosslight_doubleopen -h")
    installed_result, _, _ = run_command("fosslight_yocto -ip test_files/installed-packages.txt -i test_files/installed-package-names.txt -b test_files/bom.json -p test_files/packages -y test_files/oss-pkg-info.yaml -o test_result/yocto.xlsx")

    # then
    assert help_result is True, "Help command failed"
    assert double_help_result is True, "Doubled help command failed"
    assert installed_result is True, "installed command failed"
