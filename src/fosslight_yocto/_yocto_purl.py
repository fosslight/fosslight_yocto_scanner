#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
"""Build Yocto Package URLs according to purl-spec types/yocto-definition.json."""
import re
from typing import Optional
from urllib.parse import quote

YOCTO_PURL_TYPE = "yocto"
_SPECIAL_PKGSUFFIXES = (
    "-cross-canadian",
    "-crosssdk",
    "-initial",
    "-intermediate",
    "-native",
    "-cross",
)
_MLPREFIXES = ("nativesdk-", "lib32-", "lib64-", "libx32-")
_CROSS_CANADIAN_ARCH_SUFFIX = re.compile(r"-cross-canadian-[A-Za-z0-9_]+$")
_CROSS_ARCH_SUFFIX = re.compile(r"-cross-[A-Za-z0-9_]+$")


def derive_bpn(pn: str) -> str:
    """Derive BPN from PN by removing common MLPREFIX and SPECIAL_PKGSUFFIX values."""
    name = (pn or "").strip()
    for prefix in _MLPREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    changed = True
    while name and changed:
        changed = False
        for suffix in _SPECIAL_PKGSUFFIXES:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                changed = True
                break
        if not changed:
            for pattern in (_CROSS_CANADIAN_ARCH_SUFFIX, _CROSS_ARCH_SUFFIX):
                arch_stripped = pattern.sub("", name)
                if arch_stripped != name:
                    name = arch_stripped
                    changed = True
                    break
    return name


def _enc(value: str) -> str:
    return quote(str(value), safe="-._~", encoding="utf-8")


def build_yocto_purl(
    *,
    name: str,
    version: Optional[str] = "",
) -> str:
    """Build pkg:yocto/[BPN]@[PV]. Version is optional per yocto-definition.json."""
    bpn = (name or "").strip()
    if not bpn:
        return ""

    purl = f"pkg:{YOCTO_PURL_TYPE}/{_enc(bpn)}"

    pv = (version or "").strip()
    if pv:
        purl += f"@{_enc(pv)}"
    return purl
