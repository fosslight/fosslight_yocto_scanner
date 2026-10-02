#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
from fosslight_yocto._package_item import PackageItem, update_package_name


def test_or_license_appends_to_installed_package_comment():
    pkg = PackageItem()
    update_package_name(pkg, "libelf", {"libelf": "libelf"})
    pkg.license = "GPL-2.0-only | LGPL-3.0-only"

    assert pkg.comment == "Installed Package Name: libelf / GPL-2.0-only | LGPL-3.0-only"
    assert set(pkg.license) == {"gpl-2.0-only", "lgpl-3.0-only"}


def test_or_license_sets_comment_when_comment_is_empty():
    pkg = PackageItem()
    pkg.license = "GPL-2.0-only | LGPL-3.0-only"

    assert pkg.comment == "GPL-2.0-only | LGPL-3.0-only"


def test_and_license_keeps_existing_comment():
    pkg = PackageItem()
    update_package_name(pkg, "libelf", {"libelf": "libelf"})
    pkg.license = "GPL-2.0-only & LGPL-3.0-only"

    assert pkg.comment == "Installed Package Name: libelf"
    assert set(pkg.license) == {"gpl-2.0-only", "lgpl-3.0-only"}
