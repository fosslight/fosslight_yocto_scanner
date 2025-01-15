#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import yaml
import logging
import codecs
import os
import fosslight_util.constant as constant
from ._package_item import PackageItem

_logger = logging.getLogger(constant.LOGGER_NAME)
EXAMPLE_OSS_PKG_INFO_LINK = "https://github.com/fosslight/fosslight_prechecker/blob/main/tests/convert/sbom-info.yaml"


def parsing_yml(yaml_file, base_path):
    oss_list = []
    license_list = []
    idx = 1
    err_reason = ""
    OLD_YAML_ROOT_ELEMENT = ['Open Source Software Package',
                             'Open Source Package']
    try:
        path_of_yml = os.path.normpath(os.path.dirname(yaml_file))
        base_normpath = os.path.normpath(base_path)
        relative_path = ""
        if path_of_yml != base_normpath:
            relative_path = os.path.relpath(path_of_yml, base_normpath)
        else:
            relative_path = ""
        doc = yaml.safe_load(codecs.open(yaml_file, "r", "utf-8"))
        # If yaml file is empty, return immediately
        if doc is None:
            err_reason = "empty"
            _logger.debug(f"The yaml file is empty file: {yaml_file}")
            return oss_list, license_list, err_reason

        is_old_format = any(x in doc for x in OLD_YAML_ROOT_ELEMENT)

        for root_element in doc:
            oss_items = doc[root_element]
            if oss_items:
                if not isinstance(oss_items, list) or 'version' not in oss_items[0]:
                    raise AttributeError(f"- Ref. {EXAMPLE_OSS_PKG_INFO_LINK}")
                for oss in oss_items:
                    item = PackageItem()
                    item.relative_path = relative_path
                    if not is_old_format:
                        item.name = root_element
                    for key, value in oss.items():
                        if key:
                            key = key.lower().strip()
                        if not value:
                            value = ""
                        set_value_switch(item, key, value, yaml_file)
                    oss_list.append(item)
                    license_list.extend(item.license)
                    idx += 1
    except AttributeError as ex:
        _logger.debug(f"Not supported yaml file format: {yaml_file} {ex}")
        oss_list = []
        err_reason = "not_supported"
    except yaml.YAMLError:
        _logger.debug(f"Error to parse yaml - skip to parse yaml file: {yaml_file}")
        oss_list = []
        err_reason = "yaml_error"
    return oss_list, set(license_list), err_reason


def set_value_switch(oss, key, value, yaml_file=""):
    if key in ['oss name', 'name']:
        oss.name = value
    elif key in ['oss version', 'version']:
        oss.version = value
    elif key in ['download location', 'source']:
        oss.download_location = value
    elif key in ['license', 'license text']:
        oss.license = value
    elif key in ['file name or path', 'source name or path', 'source path',
                 'file', 'binary name', 'binary path']:
        oss.source_name_or_path = value
    elif key in ['copyright text', 'copyright']:
        oss.copyright = value
    elif key == 'exclude':
        oss.exclude = value
    elif key == 'comment':
        oss.comment = value
    elif key == 'homepage':
        oss.homepage = value
    elif key == 'yocto_package':
        oss.yocto_package = value
    elif key == 'yocto_recipe':
        oss.yocto_recipe = value
    elif key == 'vulnerability link':
        oss.bin_vulnerability = value
    elif key == 'tlsh':
        oss.bin_tlsh = value
    elif key == 'sha1':
        oss.bin_sha1 = value
    else:
        if yaml_file != "":
            _logger.debug(f"file:{yaml_file} - key:{key} cannot be parsed")
