#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Android binary analysis script
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

import subprocess
import pytest


@pytest.fixture
def run_command():
    def _run_command(command):
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        success = result.returncode == 0
        stdout = result.stdout.decode('utf-8')
        stderr = result.stderr.decode('utf-8')
        return success, stdout, stderr
    return _run_command