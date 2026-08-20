#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_yocto._package_item import PackageItem
from fosslight_yocto._write_result_file import SHEET_NAME_DEP
from fosslight_yocto._yocto_purl import build_yocto_purl, derive_bpn, derive_layer
from fosslight_util.write_excel import get_header_row


def test_derive_bpn_strips_prefix_and_suffix():
    assert derive_bpn("lib32-glibc") == "glibc"
    assert derive_bpn("libusb1-native") == "libusb1"
    assert derive_bpn("nativesdk-qemu") == "qemu"
    assert derive_bpn("binutils-cross-aarch64") == "binutils"
    assert derive_bpn("glibc") == "glibc"


def test_derive_layer_from_recipe_file():
    assert derive_layer("/oe-core/meta/recipes-devtools/m4/m4_1.4.18.bb") == "core"
    assert derive_layer("/meta-oe/meta-oe/recipes-connectivity/libmtp/libmtp_1.1.16.bb") == "meta-oe"
    assert derive_layer("/meta-qt5/recipes-qt/qt5/qtgraphicaleffects_git.bb") == "meta-qt5"
    assert derive_layer("/meta-webosose/meta-webos/recipes-webos/videooutputd/api.bb") == "meta-webos"
    assert derive_layer("") == ""


def test_build_yocto_purl_matches_definition_examples():
    assert build_yocto_purl(name="glibc", version="2.35", layer="core") == "pkg:yocto/core/glibc@2.35"
    assert build_yocto_purl(
        name="glibc",
        version="2.35",
        layer="core",
        repository_url="https://git.openembedded.org/openembedded-core",
        layer_version="kirkstone",
    ) == (
        "pkg:yocto/core/glibc@2.35"
        "?repository_url=https%3A%2F%2Fgit.openembedded.org%2Fopenembedded-core"
        "&layer_version=kirkstone"
    )
    assert build_yocto_purl(name="u-boot-xlnx-uenv", version="1.0.0", layer="xilinx") == (
        "pkg:yocto/xilinx/u-boot-xlnx-uenv@1.0.0"
    )


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
    assert row[0] == "pkg:yocto/core/libusb1@1.0.22"
    assert row[1] == "libusb1-native"
    assert row[2] == "1.0.22"
    assert "lgplv2.1+" in row[3]
    assert row[-1] == ""
