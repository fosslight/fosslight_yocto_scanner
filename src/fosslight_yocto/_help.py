#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_util.help import PrintHelpMsg, print_package_version

_HELP_MESSAGE_BOM = """
    📖 Usage
    ────────────────────────────────────────────────────────────────────
    fosslight_yocto [options] <arguments>

    📝 Description
    ────────────────────────────────────────────────────────────────────
    FOSSLight Yocto Scanner parses bom.json to extract open source
    information for packages installed on a Yocto-based model.

    📚 Guide: https://fosslight.org/fosslight-guide-en/scanner/7_yocto.html

    ⚙️  General Options
    ────────────────────────────────────────────────────────────────────
    -h                     Show this help message
    -v                     Show version information
    -o <path>              Output directory path (default: current directory)
    -f <format>            Output file format (excel, csv, opossum)

    🔍 Scanner-Specific Options
    ────────────────────────────────────────────────────────────────────
    -p <path>              Path of buildhistory/package directory
    -b <file>              bom.json file path
    -i <file>              installed-package-names.txt file path
    -ip <file>             installed-packages.txt file path
    -y <file>              sbom-info.yaml or oss-pkg-info.yaml file path
    -a <path>              Path to analyze the binaries
    -n                     Print result in BIN(Yocto) format
    -s                     Analyze source code for New Open Source
    -c                     Analyze all the source code
    -e <path>              Top build output path with bom.json to compress
                           all the source code
    -pr                    Print all data of bom.json

    💡 Examples
    ────────────────────────────────────────────────────────────────────
    # Basic scan with required inputs
    fosslight_yocto -p buildhistory/packages -b bom.json \\
                    -i installed-package-names.txt -ip installed-packages.txt

    # Scan with sbom-info.yaml and output path
    fosslight_yocto -p buildhistory/packages -b bom.json \\
                    -i installed-package-names.txt -ip installed-packages.txt \\
                    -y sbom-info.yaml -o results/

    # Scan with binary analysis and source code analysis
    fosslight_yocto -p buildhistory/packages -b bom.json \\
                    -i installed-package-names.txt -ip installed-packages.txt \\
                    -a /path/to/binaries -s
"""

_HELP_MESSAGE_META_DOUBLE = """
    📖 Usage
    ────────────────────────────────────────────────────────────────────
    fosslight_doubleopen [options] <arguments>

    📝 Description
    ────────────────────────────────────────────────────────────────────
    FOSSLight Yocto Scanner for parsing meta-doubleopen's result file
    (SPDX JSON format) and generating an OSS report.

    📚 Guide: https://fosslight.org/fosslight-guide-en/yocto

    ⚙️  General Options
    ────────────────────────────────────────────────────────────────────
    -h                     Show this help message
    -v                     Show version information

    🔍 Scanner-Specific Options
    ────────────────────────────────────────────────────────────────────
    -f <file>              meta-doubleopen result SPDX file path
    -o <file>              Output file name (with path)

    💡 Examples
    ────────────────────────────────────────────────────────────────────
    # Parse meta-doubleopen result file
    fosslight_doubleopen -f meta_doubleopen_result.spdx.json

    # Parse with custom output file name
    fosslight_doubleopen -f meta_doubleopen_result.spdx.json -o results/oss_report
"""


def print_help_msg_bom():
    helpMsg = PrintHelpMsg(_HELP_MESSAGE_BOM)
    helpMsg.print_help_msg(True)


def print_help_msg_doubleopen():
    helpMsg = PrintHelpMsg(_HELP_MESSAGE_META_DOUBLE)
    helpMsg.print_help_msg(True)


def print_version(pkg_name):
    print_package_version(pkg_name, "FOSSLight Yocto Version:")
