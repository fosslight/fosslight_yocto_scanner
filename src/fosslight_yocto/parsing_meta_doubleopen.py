#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
import json
from datetime import datetime
import logging
import fosslight_util.constant as constant
from fosslight_util.set_log import init_log
from ._help import print_help_msg_doubleopen, print_version
from fosslight_util.output_format import write_output_file
from ._package_item import PackageItem
import argparse

logger = logging.getLogger(constant.LOGGER_NAME)
_PKG_NAME = "fosslight_yocto"


def copy_info_from_recipe(pkg, recipe):
    if recipe != "" and recipe is not None:
        pkg.comment = recipe.comment
        pkg.download_location = recipe.download_location
        pkg.license = recipe.license
        pkg.copyright = recipe.copyright
        pkg.homepage = recipe.homepage
        pkg.oss_name = recipe.oss_name


def matching_data_from_recipe(pkg_list, recipe_list, generated_list, is_distributed=False):
    rc = True
    msg = ""

    try:
        for pkg in pkg_list:
            pkg_spdx = pkg.spdx_id
            logger.debug("FIND : " + pkg_spdx)
            if pkg_spdx in generated_list:
                recipe = generated_list[pkg_spdx]
                logger.debug("|-- RECIPE : " + recipe)
                try:
                    found_idx = recipe_list.index(recipe)
                    recipe_item = recipe_list[found_idx]
                    if is_distributed:
                        recipe_item.exclude = False
                    pkg = copy_info_from_recipe(pkg, recipe_item)
                except ValueError as ex:
                    logger.debug(f"|--- Can't find recipe_ {recipe}:{ex}")
                    continue

    except Exception as ex:
        msg = f"Error Parsing item:{ex}"
        rc = False
        logger.error(msg)

    return rc, msg, pkg_list


def parsing_pkg_item(pkg_list, pkg_distributed):

    rc = True
    pkg_items = []
    recipe_items = []
    pkg_notDistributed = []
    logger.debug("TOTAL FILE COUNT: " + str(len(pkg_list)) + "\n")

    for pkg in pkg_list:
        try:
            pkg_item = PackageItem()
            for key, value in pkg.items():
                if key == 'versionInfo':
                    pkg_item.version = value
                elif key == 'downloadLocation':
                    pkg_item.download_location = value
                elif key == 'licenseDeclared':
                    pkg_item.license = value
                elif key == 'file':
                    pkg_item.source_name_or_path = value
                elif key == 'copyrightText':
                    pkg_item.copyright = value
                elif key == 'comment':
                    pkg_item.comment = value
                elif key == 'name':
                    pkg_item.package_name = value
                    pkg_item.oss_name = value
                    pkg_item.parent_package_name = value
                elif key == 'homepage':
                    pkg_item.homepage = value
                elif key == 'SPDXID':
                    pkg_item.spdx_id = value

            if pkg_item.spdx_id.startswith("SPDXRef-Recipe-"):
                pkg_item.exclude = True
                recipe_items.append(pkg_item)
            else:
                if pkg_item.spdx_id in pkg_distributed:
                    pkg_items.append(pkg_item)
                else:
                    pkg_item.exclude = True
                    pkg_notDistributed.append(pkg_item)

        except Exception as ex:
            rc = False
            logger.error(f"Error Parsing item:{ex}")

    logger.info(f"- TOTAL Distributed: {len(pkg_items)}")
    logger.info(f"- TOTAL Recipe: {len(recipe_items)}")
    logger.info(f"- TOTAL Not Distributed: {len(pkg_notDistributed)}")

    return rc, pkg_items, recipe_items, pkg_notDistributed


def parsing_relationships_item(relationships_items):
    rc = True
    spdx_distributed = []
    generated_list = {}

    for rel_item in relationships_items:
        try:
            rel_type = ""
            spdx_id = ""
            relatedSpdxElement = ""
            if "spdxElementId" in rel_item:
                spdx_id = rel_item["spdxElementId"]
            if "relationshipType" in rel_item:
                rel_type = rel_item["relationshipType"]
            if "relatedSpdxElement" in rel_item:
                relatedSpdxElement = rel_item["relatedSpdxElement"]
            if spdx_id:
                if rel_type == "PACKAGE_OF":
                    spdx_distributed.append(spdx_id)
                if rel_type == "GENERATES":  # CONTAINS GENERATED_FROM
                    generated_list[relatedSpdxElement] = spdx_id

        except Exception as ex:
            rc = False
            logger.error(f"Parsing relation:{ex}")

    return rc, spdx_distributed, generated_list


def parsing_spdx_json(json_file):
    recipes = []
    pkg_distributed = []
    pkg_notDistributed = []
    try:
        logger.info("Start parsing " + json_file)
        with open(json_file, "r") as st_json:
            st_python = json.load(st_json)
            rc, spdx_distributed, generated_list = parsing_relationships_item(st_python["relationships"])
            rc, pkg_distributed, recipes, pkg_notDistributed = parsing_pkg_item(st_python["packages"], spdx_distributed)
            rc, msg, pkg_distributed = matching_data_from_recipe(pkg_distributed, recipes, generated_list, True)
            rc, msg, pkg_notDistributed = matching_data_from_recipe(pkg_notDistributed, recipes, generated_list)

    except Exception as error:
        logger.error(f"Parsing {json_file}:{error}")
    return recipes, pkg_distributed, pkg_notDistributed


def get_sheet_content_to_print(pkg_list):
    list_to_print = []
    for item in pkg_list:
        list_to_print.extend(item.get_print_item())
    return list_to_print


def read_spdx_json(json_file_to_parse, output_file_name):
    recipes = []
    pkg_distributed = []
    pkg_notDistributed = []

    msg = ""
    success = True

    try:
        sheet_list = {}
        if os.path.isfile(json_file_to_parse):
            recipes, pkg_distributed, pkg_notDistributed = parsing_spdx_json(
                json_file_to_parse)

            sheet_list["SRC_distributed"] = get_sheet_content_to_print(pkg_distributed)
            sheet_list["SRC_recipe"] = get_sheet_content_to_print(recipes)
            sheet_list["SRC_not_distributed"] = get_sheet_content_to_print(pkg_notDistributed)
        else:
            msg = "Can't find a spdx json file:" + json_file_to_parse
            success = False

        success_to_write, writing_msg, result_file = write_output_file(output_file_name, ".xlsx", sheet_list)
        if success_to_write:
            logger.info(f"FOSSLight Report:{result_file}")
        else:
            logger.warning(f"Writing excel :{success_to_write}, {writing_msg}")

    except Exception as ex:
        success = False
        msg = str(ex)
        logger.error(msg)

    return msg, success


def main():
    global logger

    start_time = datetime.now().strftime('%y%m%d_%H%M')
    output_file_name = ""

    parser = argparse.ArgumentParser(description='FOSSLight Yocto', prog='fosslight_yocto', add_help=False)
    parser.add_argument('-h', '--help', action='store_true', required=False)
    parser.add_argument('-v', '--version', action='store_true', required=False)
    parser.add_argument('-o', '--output', type=str, required=False)
    parser.add_argument('-f', '--file', type=str, required=False)

    args = parser.parse_args()
    if args.help:
        print_help_msg_doubleopen()
    if args.version:
        print_version(_PKG_NAME)
    if args.file:
        spdx_file = args.file
    if args.output:
        output_file_name = os.path.abspath(args.output)

    if output_file_name == "":
        output_dir = os.getcwd()
        oss_report_name = f"fosslight_report_yocto_{start_time}"
    else:
        oss_report_name = output_file_name
        output_dir = os.path.dirname(output_file_name)

    logger, log_item = init_log(os.path.join(output_dir, f"fosslight_log_yocto_{start_time}.txt"))
    read_spdx_json(spdx_file, oss_report_name)


if __name__ == '__main__':
    main()
