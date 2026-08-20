#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_yocto._package_item import PackageItem
from fosslight_yocto._write_result_file import SHEET_NAME_DEP
from fosslight_yocto._yocto_purl import build_yocto_purl, derive_bpn
from fosslight_util.write_excel import get_header_row


def test_derive_bpn_strips_prefix_and_suffix():
    assert derive_bpn("lib32-glibc") == "glibc"
    assert derive_bpn("libusb1-native") == "libusb1"
    assert derive_bpn("nativesdk-qemu") == "qemu"
    assert derive_bpn("binutils-cross-aarch64") == "binutils"
    assert derive_bpn("gcc-cross-canadian-aarch64") == "gcc"
    assert derive_bpn("glibc") == "glibc"


def test_build_yocto_purl_matches_definition_examples():
    assert build_yocto_purl(name="glibc", version="2.35") == "pkg:yocto/glibc@2.35"
    assert build_yocto_purl(name="u-boot-xlnx-uenv", version="1.0.0") == (
        "pkg:yocto/u-boot-xlnx-uenv@1.0.0"
    )


def test_build_yocto_purl_preserves_colon_in_name_and_version():
    assert build_yocto_purl(name="foo:bar", version="1:2.0") == "pkg:yocto/foo:bar@1:2.0"


def test_dep_print_item_uses_fosslight_util_columns():
    pkg = PackageItem()
    pkg.oss_name = "libusb1-native"
    pkg.pv = "1.0.22"
    pkg.version = "1.0.22"
    pkg.license = "LGPLv2.1+"
    pkg.download_location = "http://example.com/libusb.tar.bz2"
    pkg.recipe_file = "/oe-core/meta/recipes-support/libusb/libusb1_1.0.22.bb"

    rows = pkg.get_print_item(SHEET_NAME_DEP)
    assert len(rows) == 1
    row = rows[0]
    header = get_header_row(SHEET_NAME_DEP)
    # ID is added later by fosslight_util; data row starts at Package URL
    assert len(row) == len(header) - 1
    assert row[0] == "pkg:yocto/libusb1@1.0.22"
    assert row[1] == "libusb1-native"
    assert row[2] == "1.0.22"
    assert "lgplv2.1+" in row[3]
    assert row[-1] == ""
