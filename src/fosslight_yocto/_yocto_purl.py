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
_CROSS_ARCH_SUFFIX = re.compile(r"-cross-[A-Za-z0-9_]+$")
_REPO_URL_SCHEMES = ("https://", "http://", "ssh://", "git://")


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
            arch_stripped = _CROSS_ARCH_SUFFIX.sub("", name)
            if arch_stripped != name:
                name = arch_stripped
                changed = True
    return name


def _enc(value: str) -> str:
    return quote(str(value), safe="-._~", encoding="utf-8")


def _normalize_repository_url(repository_url: str) -> str:
    url = (repository_url or "").strip()
    if not url:
        return ""
    if url.startswith("git@"):
        host_path = url[4:]
        if ":" in host_path:
            host, path = host_path.split(":", 1)
            url = f"ssh://git@{host}/{path}"
    if not url.lower().startswith(_REPO_URL_SCHEMES):
        return ""
    return url


def build_yocto_purl(
    *,
    name: str,
    version: Optional[str] = "",
    layer: Optional[str] = "",
    repository_url: Optional[str] = "",
    layer_version: Optional[str] = "",
) -> str:
    """
    Build pkg:yocto/[layer]/[BPN]@[PV]?repository_url=...&layer_version=...

    namespace (layer), version, and qualifiers are optional per yocto-definition.json.
    """
    bpn = (name or "").strip()
    if not bpn:
        return ""

    namespace = (layer or "").strip().lower()
    path = f"{_enc(namespace)}/{_enc(bpn)}" if namespace else _enc(bpn)
    purl = f"pkg:{YOCTO_PURL_TYPE}/{path}"

    pv = (version or "").strip()
    if pv:
        purl += f"@{_enc(pv)}"

    qualifiers = []
    repo_url = _normalize_repository_url(repository_url or "")
    if repo_url:
        qualifiers.append(f"repository_url={_enc(repo_url)}")
    lv = (layer_version or "").strip()
    if lv:
        qualifiers.append(f"layer_version={_enc(lv)}")
    if qualifiers:
        purl += "?" + "&".join(qualifiers)
    return purl
