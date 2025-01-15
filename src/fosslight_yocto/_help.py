#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.help import PrintHelpMsg, print_package_version

_HELP_MESSAGE_BOM = """
    Usage: fosslight_yocto [option1] <arg1> [option2] <arg2>...

    FOSSLight Yocto for parsing BOM.json

    Options:
        Mandatory
            -p <path>\t\t   Path of buildhistory/package
            -b <file_with_path>\t\t   bom.json
            -i <file_with_path>\t\t   installed-package-names.txt
            -ip <file_with_path>\t   installed-packages.txt

        Optional
            -h\t\t\t\t   Print help message
            -v\t\t\t\t   Print FOSSLight yocto version
            -y <file_with_path>\t\t   sbom-info.yaml or oss-pkg-info.yaml
            -a <path>\t\t\t   Path to analyze the binaries
            -n\t\t\t\t   Print result in BIN(Yocto) format
            -s\t\t\t\t   Analyze source code for unconfirmed Open Source
            -c\t\t\t\t   Analyze all the source code
            -e <path>\t\t\t   Top build output path with bom.json to compress all the source code
            -o <path>\t\t\t   Output Path
            -f <format>\t\t\t   Output file format (excel, csv, opossum)
            -pr\t\t\t\t   Print all data of bom.json"""

_HELP_MESSAGE_META_DOUBLE = """
    Usage: fosslight_doubleopen [option1] <arg1> [option2] <arg2>...

    FOSSLight Yocto for parsing meta-doubleopen's result file

    Options:
        Mandatory
            -f <file_name>\t\t  meta-doubleopen result spdx file

        Optional
            -h\t\t\t\t   Print help message
            -v\t\t\t\t   Print FOSSLight yocto version
            -o <file_name>\t\t   Output file name"""


def print_help_msg_bom():
    helpMsg = PrintHelpMsg(_HELP_MESSAGE_BOM)
    helpMsg.print_help_msg(True)


def print_help_msg_doubleopen():
    helpMsg = PrintHelpMsg(_HELP_MESSAGE_META_DOUBLE)
    helpMsg.print_help_msg(True)


def print_version(pkg_name):
    print_package_version(pkg_name, "FOSSLight Yocto Version:")
