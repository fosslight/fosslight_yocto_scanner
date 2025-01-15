#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging
import fosslight_util.constant as constant
import codecs
from ruamel.yaml import YAML
from ruamel.yaml.constructor import SafeConstructor
import os
from ._package_item import PackageItem, set_value_switch, update_package_name
from .parsing_yaml import parsing_yml
from copy import deepcopy

logger = logging.getLogger(constant.LOGGER_NAME)
KEY_PKG = "yocto_package"
KEY_RECIPE = "yocto_recipe"
MSG_TO_EXCLUDE = "Excluded by oss-pkg-info.yaml"
MSG_FROM_YAML_ROW = "Info loaded from oss-pkg-info.yaml"


def construct_yaml_map(self, node):
    # test if there are duplicate node keys
    keys = set()
    for key_node, value_node in node.value:
        key = self.construct_object(key_node, deep=True)
        if key in keys:
            break
        keys.add(key)
    else:
        data = {}
        yield data
        value = self.construct_mapping(node)
        data.update(value)
        return
    data = []
    yield data
    for key_node, value_node in node.value:
        key = self.construct_object(key_node, deep=True)
        val = self.construct_object(value_node, deep=True)
        data.append({key: val})


def set_list_by_value(value):
    items = []
    if value:
        if isinstance(value, list):
            items += value
        else:
            items = [value]
    return items


def load_oss_pkg_info_yaml(oss_pkg_files, print_bin_android_mode, installed_packages_src, installed_packages_bin, nested_pkg_name):
    all_pkgs_to_exclude = []
    oss_items_to_append = []
    for oss_pkg_info_yaml_file in oss_pkg_files.split(','):
        if os.path.isfile(oss_pkg_info_yaml_file):
            try:  # LATEST YAML FORMAT
                temp_items, _, _ = parsing_yml(oss_pkg_info_yaml_file, os.path.dirname(oss_pkg_info_yaml_file))
                for parent in temp_items:
                    child = PackageItem()
                    child.__dict__.update(parent.__dict__)
                    oss_items_to_append.append(child)
            except Exception as ex:
                logger.error(f"Failed to parsing yaml({oss_pkg_info_yaml_file}): {ex}")
            if not oss_items_to_append:
                try:  # LEGACY YAML FORMAT
                    with codecs.open(oss_pkg_info_yaml_file, "r", "utf-8") as f:
                        data = f.read()
                        SafeConstructor.add_constructor(u'tag:yaml.org,2002:map', construct_yaml_map)
                        yaml = YAML(typ='safe')
                        data = yaml.load(data)

                        if not isinstance(data, list):
                            data_list = [data]
                        else:
                            data_list = data

                        for recipe_items in data_list:
                            for root_name, oss_items in recipe_items.items():
                                recipe_name = root_name.strip()
                                if oss_items:
                                    for item in oss_items:
                                        pkg_item = PackageItem()
                                        for key, value in item.items():
                                            set_value_switch(pkg_item, key, value, nested_pkg_name)
                                        if recipe_name != "Open Source Package":
                                            pkg_item.yocto_recipe = recipe_name
                                        oss_items_to_append.append(pkg_item)
                except Exception as ex:
                    logger.warning(f"Failed to read {oss_pkg_info_yaml_file}: {ex}")
        else:
            logger.warning(f"Can't find a file:{oss_pkg_info_yaml_file}")

    # Update oss item based on value(yocto_package, yocto_recipe) in item.
    pkg_item_list = []
    for oss in oss_items_to_append:
        recipe_names_to_search = oss.yocto_recipe
        pkg_names_to_search = oss.yocto_package
        # Find the item to be excluded by the recipe or package name.
        pkgs_to_exclude = [(x.package_name, x.parent_package_name, x.oss_name) for x in installed_packages_src if
                           x.oss_name in recipe_names_to_search or x.name in recipe_names_to_search
                           or x.parent_package_name in pkg_names_to_search or x.package_name in pkg_names_to_search]

        if len(pkgs_to_exclude) > 0:
            search_list = recipe_names_to_search + pkg_names_to_search
            len_search = len(search_list)
            if len_search > 0:
                update_package_name(oss, search_list[0], nested_pkg_name)
            elif len_search > 1:
                prev_comment = ""
                if "comment" in oss:
                    prev_comment = f"{oss.comment}/"
                oss.comment = f"{prev_comment}pkg, recipe:{search_list}"

            all_pkgs_to_exclude += pkgs_to_exclude

            oss.source_name_or_path = ""  # Don't print file value loaded from yaml file.
            oss.comment = MSG_FROM_YAML_ROW
            oss_name_from_yaml = oss.name

            for _, pkg_name, recipe in pkgs_to_exclude:
                oss.parent_package_name = pkg_name
                oss.oss_name = recipe
                oss.name = oss_name_from_yaml
                pkg_updated = deepcopy(oss)
                pkg_item_list.append(pkg_updated)

    # Exclude packages
    for pkg_name, _, _ in all_pkgs_to_exclude:
        pkg_items = list(filter(lambda x: x.package_name == pkg_name
                                and x.exclude is False, installed_packages_bin))
        pkg_items += [x for x in installed_packages_src if x.package_name == pkg_name and x.exclude is False]

        for item in pkg_items:
            item.exclude = True
            item.comment = MSG_TO_EXCLUDE

    # Append yaml's OSS items to SRC tab
    installed_packages_src.extend(pkg_item_list)

    return installed_packages_src, installed_packages_bin
