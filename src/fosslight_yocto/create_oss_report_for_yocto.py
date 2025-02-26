#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import hashlib
import os
import sys
import json
import tlsh
from datetime import datetime
from binaryornot.check import is_binary
import magic
import copy
import logging
import pandas as pd
import pymysql
from ._help import print_help_msg_bom, print_version
# For source code analysis
import multiprocessing
import parmap
import numpy as np
import re
import stat
from scancode import cli
from fosslight_util.set_log import init_log
import fosslight_util.constant as constant
from ._zip_source_works import collect_source
from ._package_item import (
    const_other_proprietary_license,
    EXCLUDE_TRUE_VALUE,
    PackageItem,
    set_value_switch,
    update_package_name,
    BinItem)
from ._write_result_file import write_result_from_bom, print_src_analysis_result
from tqdm import tqdm
from ._overwrite_yaml import load_oss_pkg_info_yaml
from fosslight_util.output_format import check_output_format
import argparse
from typing import List
from fosslight_util.oss_item import ScannerItem

logger = logging.getLogger(constant.LOGGER_NAME)
PKG_NAME = "fosslight_yocto"

# Global variables
bom_pkg_data = {}  # Parsed from bom
installed_packages_src = []  # SRC Sheet | BIN (Yocto) Sheet
installed_packages_bin: List[PackageItem] = []  # BIN Sheet
binary_list: List[BinItem] = []  # -a option result
nested_pkg_name = {}  # Package list created at build time
like_licenses = ['mit-like license', 'bsd-like license']
_map_license_from_yocto_to_scancode = {'proprietary-license': [const_other_proprietary_license],
                                       'gpl-3.0-plus': ['gplv3', 'gpl-3.0'],
                                       'gpl-3.0': ['gplv3', 'gpl-3.0'],
                                       'gpl-2.0-plus': ['gplv2', 'gpl-2.0'],
                                       'gpl-2.0': ['gplv2', 'gpl-2.0'],
                                       'gpl-1.0-plus': ['gplv2', 'gpl-2.0', 'gplv1', 'gpl-1.0'],
                                       'lgpl-2.1-plus': ['lgplv2', 'lgpl-2.0', 'lgplv2.1'],
                                       'lgpl-2.1': ['lgplv2', 'lgpl-2.0', 'lgplv2.1'],
                                       'lgpl-3.0': ['lgplv3'], 'python-2.0': ['psfv2', 'psf'],
                                       'agpl-3.0-plus': ['agplv3', 'agplv3.0'],
                                       'agpl-3.0': ['agplv3', 'agplv3.0'],
                                       'apache-2.0': ['apachev2'], 'afl-2.0': ['aflv2'], 'afl-1.2': ['aflv1'],
                                       'bsd-new': ['bsd-3-clause'], 'bsd-simplified': ['bsd-3-clause'],
                                       'cddl-1.0': ['cddlv1'], 'epl-1.0': ['eplv1.0'],
                                       'mpl-1.1': ['mplv1.1', 'mplv1'], 'mpl-2.0': ['mpl2.0', 'mplv2'],
                                       'x11': ['mit-x']}
_skip_to_check_scancode_licenses = ['proprietary-license']
additional_columns = []
printall = False  # Print all values in bom.json
OSC_DB_USER = 'user_oss_license'
OSC_DB_PASSWORD = 'oss_lic123'
EX_DATAERR = 65
EX_NOINPUT = 66
PKG_GROUP_PREFIX = "packagegroup-"


def read_installed_pkg_file(installed_pkg_names_file):
    global installed_packages_src
    installed_packages_src = []
    success = True
    pkg_info_not_found = True
    try:
        success, lines = read_file(installed_pkg_names_file)
        for line in lines:
            if line != "":
                pkg_name = line.strip()
                pkg_item = PackageItem()
                if pkg_name:
                    pkg_item = update_package_name(pkg_item, pkg_name, nested_pkg_name)
                    if pkg_name in bom_pkg_data:
                        for key, value in bom_pkg_data[pkg_name].items():
                            set_value_switch(pkg_item, key, value, nested_pkg_name)
                    if pkg_name.startswith(PKG_GROUP_PREFIX):
                        pkg_item.exclude = True
                    installed_packages_src.append(pkg_item)
                    if pkg_info_not_found and pkg_item.oss_name:
                        pkg_info_not_found = False
    except Exception as ex:
        logger.error(f"Read {installed_pkg_names_file}: {ex}")
        success = False
    if not installed_packages_src:
        logger.error(f"Empty File : {installed_pkg_names_file}")
        success = False
    if pkg_info_not_found:
        logger.error("Check whether you entered installed-package-names.txt with -i.")
        logger.info(f"---- Value entered with -i:{installed_pkg_names_file}")
        success = False

    return success


def get_json_object(str_data):
    json_object = ""
    try:
        json_object = json.loads(str_data)
    except ValueError:
        json_object = ""
    return json_object


def check_json_validate(bom_file):
    json_obj = ""
    file_content = ""
    try:
        result, file_content = read_file(bom_file, True)
        if file_content is not None:
            file_content = file_content.strip()
    except Exception:
        exit_with_error_msg("Can't read a bom.json", EX_NOINPUT)

    # Dafault bom.json file isn't loadable.
    json_obj = get_json_object(file_content)
    if json_obj == "":
        if file_content.startswith("{"):
            file_content = "[" + file_content
        if file_content.endswith(","):
            file_content = file_content[:-1]
            file_content += "]"
        json_obj = get_json_object(file_content)

    return json_obj


def read_bom_file(bom_file, buildhistory_latest_pkg_list):
    global bom_pkg_data, additional_columns

    json_array = check_json_validate(bom_file)
    bom_pkg_data = {}

    for item in json_array:
        oss_item = {"package": "", "license": "", "version": "", "source": "", "oss_name": "", "license_flags": "",
                    "src_path": "", "file_path": ""}
        additional_column = {}
        recipe_name = item.get('recipe', '')
        oss_item['oss_name'] = recipe_name
        oss_item['version'] = item.get('pv', '')
        oss_item['src_path'] = item.get('src_path', '')

        if printall:
            for key, value in item.items():
                if key not in ['src_path', 'pv', 'recipe', 'packages', 'license_flags', 'license', 'pkg_lic', 'src_uri', 'file_path']:
                    additional_column[key] = value if value else ''
                    additional_columns.append(key)

        bom_packages = item.get('packages', '')
        if recipe_name in buildhistory_latest_pkg_list:
            bom_packages += " " + buildhistory_latest_pkg_list[recipe_name]
            bom_packages = bom_packages.strip()

        oss_item['license_flags'] = item['license_flags']
        recipe_license = item['license']
        oss_item['license'] = recipe_license
        bom_pkg_licenses = item['pkg_lic']

        bom_src_uri = item['src_uri']
        oss_item['source'] = bom_src_uri
        if bom_src_uri != "":
            src_uri = bom_src_uri.split()
            if len(src_uri) > 0:
                oss_item['source'] = src_uri[0]

        if 'file_path' in item:
            files_path = item['file_path']
            if files_path != "":
                path_list = files_path.split(":")
                if len(path_list) > 0:
                    oss_item['file_path'] = path_list[0]

        # for 'e' option to compress fetched files.
        oss_item['source_done'] = item.get('complete', "")
        oss_item['full_src_uri'] = bom_src_uri

        oss_item['package_format'] = item.get('pf', "")

        if bom_packages != "":
            packages = bom_packages.split()
            packages = list(set(packages))
            for package in packages:
                oss_item['package'] = package
                oss_item['license'] = recipe_license
                if bom_pkg_licenses != "":
                    oss_item['license'] = bom_pkg_licenses.get(package, recipe_license)
                oss_item['additional_data'] = additional_column
                bom_pkg_data[package] = copy.deepcopy(oss_item)
        # else: # Do not save data for the recipe without packages. (ex- *-native)
        #    bom_pkg_data[recipe_name] = oss_item
    if len(bom_pkg_data) == 0:
        logger.critical("The bom.json file is not json validated.")
    additional_columns = list(set(additional_columns))


def read_file(file_name_with_path, read_as_one_line=False):
    encodings = ["utf-8", "latin-1", "utf-16"]
    read_line = "" if read_as_one_line else []
    read_success = False
    for encoding_option in encodings:
        try:
            file = open(file_name_with_path, encoding=encoding_option)
            read_line = file.read() if read_as_one_line else file.readlines()
            file.close()
            if read_line is not None and len(read_line) > 0:
                read_success = True
                break
        except Exception:
            pass

    return read_success, read_line


def find_latest_pkg_from_buildhistory(path_buildhistory, installed_pkg_version):
    global nested_pkg_name
    buildhistory_latest_pkg = {}  # Key :Recipe, Value: Recipe -- Parsed from buildhistory
    tmp_package_per_recipe_info = {}
    nested_pkg_name = {}
    not_installed_pkg = {}

    success, installed_pkg_version_lines = read_file(installed_pkg_version)
    if not installed_pkg_version_lines:
        logger.error(f"Empty File:{installed_pkg_version}")
        return buildhistory_latest_pkg

    for root, dirs, files in os.walk(path_buildhistory):
        for file in files:
            if file == "latest":
                dir_name, recipe_name = os.path.split(root)
                read_sucess, lines = read_file(os.path.join(root, file))
                file_contents = '\n'.join(lines)
                pv = ""
                pr = ""
                packages = ""
                pkg = ""
                try:
                    match = re.search(r'PV(\s)*=(\s)*((\S)+)', file_contents)
                    if match:
                        pv = match.group(3)
                    match = re.search(r'PR(\s)*=(\s)*((\S)+)', file_contents)
                    if match:
                        pr = match.group(3)
                    match = re.search(r'PACKAGES(\s)*=(\s)*([^\n]+)', file_contents)
                    if match:
                        packages = match.group(3).strip()
                        for pkg_name in packages.split():
                            tmp_package_per_recipe_info[pkg_name] = recipe_name
                            if recipe_name in buildhistory_latest_pkg:
                                buildhistory_latest_pkg[recipe_name] += f" {pkg_name}"
                            else:
                                buildhistory_latest_pkg[recipe_name] = pkg_name
                    match = re.search(r'PKG(\s)*=(\s)*([^\n]+)', file_contents)
                    if match:
                        pkg = match.group(3).strip()
                        for pkg_name in pkg.split():
                            re_pkg_name = re.escape(pkg_name)
                            r = re.compile(f"^{re_pkg_name}(-|_){pv}(-|_){pr}")
                            installed_pkg_verified = list(filter(r.match, installed_pkg_version_lines))
                            if installed_pkg_verified:
                                nested_pkg_name[pkg_name] = recipe_name
                            else:
                                not_installed_pkg[pkg_name] = recipe_name
                except Exception as ex:
                    logger.debug(f"Failed to parsing latest_{root}:{ex}")
    for pkg in not_installed_pkg.keys():
        if pkg not in nested_pkg_name:
            nested_pkg_name[pkg] = not_installed_pkg[pkg]

    for pkg in nested_pkg_name.keys():
        pkg_to_find = nested_pkg_name[pkg]
        if pkg_to_find in tmp_package_per_recipe_info:
            recipe_found = tmp_package_per_recipe_info[pkg_to_find]
            buildhistory_latest_pkg[recipe_found] += f" {pkg}"

    return buildhistory_latest_pkg


def find_package_files(path_buildhistory):
    logger.debug(f"Find_package_files: {path_buildhistory}")

    buildhistory_package_files = {}  # Key: file, Value : list of packages
    for root, dirs, files in os.walk(path_buildhistory):
        for file in files:
            dir_name, pkg_name = os.path.split(root)
            if file == "files-in-package.txt":
                read_success, lines = read_file(os.path.join(root, file))
                for line in lines:
                    words = line.split()
                    if len(words) > 4:
                        for file_name in words[4:]:
                            if file_name != "->":
                                if file_name in buildhistory_package_files:
                                    buildhistory_package_files[file_name].append(pkg_name)
                                else:
                                    buildhistory_package_files[file_name] = [pkg_name]
            if file == "latest":
                read_success, lines = read_file(os.path.join(root, file))
                for line in lines:
                    if line.startswith("FILELIST ="):
                        m = re.findall("\'[^\']+\'", line)
                        if m:
                            for file_name in m:
                                file = "." + file_name.replace("\'", "")
                                if file in buildhistory_package_files:
                                    buildhistory_package_files[file].append(pkg_name)
                                else:
                                    buildhistory_package_files[file] = [pkg_name]

                        prev_file_name = ""
                        for file_name in line.split():
                            files_to_add = []
                            if file_name.startswith("/"):
                                file = "." + file_name
                                prev_file_name = file
                                files_to_add.append(file)
                            elif file_name.startswith("'"):
                                prev_file_name = file_name
                                continue
                            else:  # When space is entered in the file name or path
                                prev_file_name += " " + file_name
                                files_to_add.append(file_name)
                                files_to_add.append(prev_file_name)

                            for file in files_to_add:
                                if file in buildhistory_package_files:
                                    buildhistory_package_files[file].append(pkg_name)
                                else:
                                    buildhistory_package_files[file] = [pkg_name]

    return buildhistory_package_files


def get_checksum_and_tlsh(bin_file_full_path):
    checksum_value = "0"
    tlsh_value = "0"
    try:
        f = open(bin_file_full_path, "rb")
        byte = f.read()
        sha1_hash = hashlib.sha1(byte)
        checksum_value = str(sha1_hash.hexdigest())
        try:
            tlsh_value = str(tlsh.hash(byte))
        except Exception:
            tlsh_value = "0"
        f.close()
    except Exception as error:
        logger.debug(f"get_checksum_and_tlsh: {error}")
    return checksum_value, tlsh_value


def get_binary_list(buildhistory_package_files, path_to_find):
    global installed_packages_bin, binary_list
    EXCLUDE_FILE_EXTENSION = ['qm', 'pyc']
    EXCLUDE_FILE_COMMAND_RESULT = ['data', 'timezone data']
    file_list = []
    success = False
    PREFIX_BIN_FAILED = "[Binary Analysis Error] "
    cnt_bin = 0

    if not os.path.isdir(path_to_find):
        logger.error(f"{PREFIX_BIN_FAILED}Directory not found: {path_to_find}\nPlease check the Path again.")
        return success, cnt_bin

    for root, dirs, files in os.walk(path_to_find):
        for file in files:
            file_abs_path = os.path.join(root, file)
            file_list.append(file_abs_path)

    if not file_list:
        logger.error(f"{PREFIX_BIN_FAILED}Cannot find files in directory: {path_to_find}\nPlease check the Path again.")
    else:
        for file_abs_path in tqdm(file_list):
            try:
                file = os.path.basename(file_abs_path)
                extension = os.path.splitext(file)[1][1:]

                if not os.path.islink(file_abs_path) and extension not in EXCLUDE_FILE_EXTENSION:
                    file_abs_path = os.path.realpath(file_abs_path)
                    file_rel_path = "./" + os.path.relpath(file_abs_path, path_to_find)

                    if stat.S_ISFIFO(os.stat(file_abs_path).st_mode):
                        continue
                    if is_binary(file_abs_path):
                        file_command_result = magic.from_file(file_abs_path)
                        if file_command_result != "":
                            excluded_keyword = [x for x in EXCLUDE_FILE_COMMAND_RESULT if
                                                file_command_result.startswith(x)]
                            if len(excluded_keyword) > 0:
                                continue
                        file_to_find = ' '.join(
                            file_rel_path.split())  # If there are two or more spaces, it is changed to one space.
                        if file_to_find in buildhistory_package_files:
                            pkg_names = buildhistory_package_files[file_to_find]
                            pkg_name = ""
                            for name in pkg_names:
                                if name in bom_pkg_data:
                                    pkg_name = name
                                    break
                        else:  # Can't find package name
                            pkg_name = ""

                        checksum, tlsh = get_checksum_and_tlsh(file_abs_path)
                        file_item = BinItem(file_rel_path, tlsh, checksum)
                        binary_list.append(file_item)
                        cnt_bin += 1

                        pkg_items = list(filter(lambda x: x.package_name is pkg_name, installed_packages_bin))

                        if pkg_items is not None and len(pkg_items) > 0:
                            # Package already inserted. Just add file to it.
                            pkg_items[0].files = file_rel_path
                        else:  # New Package
                            pkg_item = PackageItem()
                            pkg_item = update_package_name(pkg_item, pkg_name, nested_pkg_name)
                            pkg_item.files = file_rel_path
                            if pkg_name:
                                if pkg_name in bom_pkg_data:
                                    for key, value in bom_pkg_data[pkg_name].items():
                                        set_value_switch(pkg_item, key, value, nested_pkg_name)
                                else:
                                    pkg_item.oss_name = pkg_name
                                    pkg_item.comment = "Can't find package info from bom."
                            installed_packages_bin.append(pkg_item)
            except Exception as ex:
                logger.error(f"Get_binary_list: {ex}")
        if installed_packages_bin:
            success = True
        else:
            logger.error(f"{PREFIX_BIN_FAILED}Binary cannot be found (File Count: {len(file_list)}): {path_to_find}\nPlease check the Path again.")
    return success, cnt_bin


def check_required_files(bom, installed_pkgs, buildhistory_path, installed_pkgs_version):
    error_msg = ""
    if not os.path.isfile(bom):
        error_msg = "-b bom.json\n"
    if not os.path.isfile(installed_pkgs):
        error_msg = "-i installed-package-names.txt\n"
    if not os.path.isdir(buildhistory_path) or buildhistory_path == "":
        error_msg = "-p path/to/buildhistory\n"
    if not os.path.isfile(installed_pkgs_version):
        error_msg = "-ip installed-packages.txt\n"

    if error_msg != "":
        exit_with_error_msg("Check Arguments\n" + error_msg, EX_NOINPUT)


def exit_with_error_msg(error_msg, exit_code=EX_DATAERR):
    logger.error(error_msg)
    sys.exit(exit_code)


def change_like_license(recipe_license, db_licenses):
    cnt_like_licenses_in_db = 0
    matched_like_license = ""
    matched_like_style = ""
    changed_license_list = []
    try:
        for lic_group in db_licenses:
            for lic in lic_group:
                for like_license in like_licenses:
                    lic = lic.lower()
                    if lic.startswith(like_license) and matched_like_license != lic:
                        cnt_like_licenses_in_db += 1
                        matched_like_license = lic
                        matched_like_style = like_license

        if cnt_like_licenses_in_db == 1:
            if len([x for x in recipe_license if x.startswith(matched_like_style)]) > 0:
                changed_license_list = [matched_like_license if x.startswith(matched_like_style) else x for x in
                                        recipe_license]
    except Exception:
        pass
    return changed_license_list


def declare_license_by_osc_db():
    global installed_packages_src
    global installed_packages_bin

    oss_info_from_db = {}  # Key : name +|+version, Value :name, version, lic_group
    license_info_from_db = {}  # Key : name , Value : nick, score
    seperator = ","

    # Get all OSS Name, OSS version list
    for item in installed_packages_src:
        if item.license is not None and (len(item.license) > 1 or len(
                set(item.license) & set(like_licenses)) == 1) and item.exclude != EXCLUDE_TRUE_VALUE:
            key = item.name + seperator + item.version

            if key not in oss_info_from_db:
                oss_info_from_db[key] = {}
                oss_info_from_db[key]['version'] = item.version
                oss_info_from_db[key]['name'] = item.name
                oss_info_from_db[key]['lic_group'] = []

    # Get DB Connection
    db_conn, db_cur = connect_to_osc_db()
    if db_conn == "" or db_cur == "":
        return
    # Get OSS's Licenses from DB
    for key, oss_item in oss_info_from_db.items():
        where_condition = " WHERE (OM.OSS_NAME = '{oss_name}' OR NICK.OSS_NICKNAME = '{oss_name}') AND OM.OSS_VERSION = '{oss_version}'".format(
            oss_name=pymysql.escape_string(oss_item['name']), oss_version=pymysql.escape_string(oss_item['version']))
        oss_item['lic_group'], license_info_from_db = select_query_to_db(db_cur, license_info_from_db, where_condition)
    disconnect_lge_bin_db(db_conn, db_cur)

    # Get declared License
    installed_packages = []
    installed_packages.append(installed_packages_src)
    installed_packages.append(installed_packages_bin)
    need_check_list = []
    check_list = []

    for installed_pkg in installed_packages:
        for item in installed_pkg:
            try:
                recipe_license = item.license
                declared_lic = []
                if recipe_license is not None:
                    key = item.name + seperator + item.version
                    if key in oss_info_from_db and len(oss_info_from_db[key]['lic_group']) > 0:
                        if len(set(item.license) & set(like_licenses)) == 1:
                            declared_lic = change_like_license(recipe_license, oss_info_from_db[key]['lic_group'])
                            if len(declared_lic) > 0:
                                item.license = declared_lic

                        if len(item.license) > 1:
                            if seperator.join(recipe_license) in oss_info_from_db[key]:
                                declared_lic = oss_info_from_db[key][seperator.join(recipe_license)]
                            else:
                                declared_lic, need_check = get_declared_license(license_info_from_db, recipe_license,
                                                                                oss_info_from_db[key]['lic_group'])
                                oss_info_from_db[key][seperator.join(recipe_license)] = declared_lic
                                if need_check:
                                    need_check_list.append(
                                        [key, ":", seperator.join(recipe_license), "->", seperator.join(declared_lic)])
                                elif len(declared_lic) > 0:
                                    check_list.append(
                                        [key, ":", seperator.join(recipe_license), "->", seperator.join(declared_lic)])

                    item.declared_licenses = declared_lic
            except Exception:
                pass
    if len(need_check_list) > 0 or len(check_list) > 0:
        logger.warning("[License changed to the license registered in OSC System DB.]")
        print_declared_license_result(need_check_list, "* Make sure that the removed license is not included.")
        print_declared_license_result(check_list, "* Check that the removed license is not included.")


def print_declared_license_result(check_list_to_print, prefix):
    if check_list_to_print is not None and len(check_list_to_print) > 0:
        logger.warning(prefix)
        for items in check_list_to_print:
            logger.warning(" ".join(items))


def get_declared_license(license_info_from_db, recipe_licenses, db_licenses):

    declared_lic = []
    declared_lic_has_not_permissive = False
    group_score = {}

    # Check recipe license included or not
    recipe_included = False
    recipe_lic_cnt = len(recipe_licenses)
    max_matched_lic_cnt = 0
    max_permissive_cnt = 0
    not_matched_exist = False

    for db_lic_group in db_licenses:
        declare_license_has_not_permissive = False
        idx = 0
        group_score[idx] = {}
        matched_lic_cnt = 0
        permissive_lic_cnt = 0
        not_matched_cnt = 0
        matched_lic = []
        for db_lic in db_lic_group:
            for recipe_lic in recipe_licenses:
                if (recipe_lic in license_info_from_db[db_lic]['nick']) or (
                        recipe_lic in like_licenses and db_lic.startswith(recipe_lic)):
                    recipe_included = True
                    permissive_lic_or_not = license_info_from_db[db_lic]['score']
                    permissive_lic_cnt += permissive_lic_or_not
                    matched_lic_cnt += 1
                    matched_lic.append(recipe_lic)
                    if permissive_lic_or_not != 1:
                        declare_license_has_not_permissive = True

        not_matched_cnt = len(db_lic_group) - matched_lic_cnt
        if not_matched_cnt == 0:
            not_matched_exist = True
            if recipe_lic_cnt == matched_lic_cnt:
                declared_lic = []
            else:
                declared_lic = matched_lic
                declared_lic_has_not_permissive = declare_license_has_not_permissive
            break
        group_score[idx]['matched'] = matched_lic_cnt
        group_score[idx]['permissive'] = permissive_lic_cnt
        group_score[idx]['list'] = matched_lic
        group_score[idx]['has_not_permissive'] = declare_license_has_not_permissive

        if max_matched_lic_cnt < matched_lic_cnt:
            max_matched_lic_cnt = matched_lic_cnt
        if max_permissive_cnt < permissive_lic_cnt:
            max_permissive_cnt = permissive_lic_cnt
        idx += 1

    if recipe_included and not not_matched_exist:
        idx_list = [key for key, value in group_score.items() if value['matched'] == max_matched_lic_cnt]
        if len(idx_list) > 0:
            if len(idx_list) == 1:
                declared_lic = group_score[idx_list[0]]['list']
                declared_lic_has_not_permissive = group_score[idx_list[0]]['has_not_permissive']
            else:
                max_permissive_cnt = 0
                for idx in idx_list:
                    count = group_score[idx]['permissive']
                    if max_permissive_cnt == count:
                        declared_lic = group_score[idx]['list']
                        declared_lic_has_not_permissive = group_score[idx]['has_not_permissive']
                        break

        if recipe_lic_cnt == max_matched_lic_cnt:
            declared_lic = []
    need_check = False
    if len(declared_lic) > 0 and not declared_lic_has_not_permissive:
        for re_license in recipe_licenses:
            if re_license not in declared_lic and re_license not in like_licenses:
                lic_score_list = [license_info_from_db[lic_name]['score'] for lic_name in license_info_from_db.keys() if
                                  re_license in license_info_from_db[lic_name]['nick']]
                if len(lic_score_list) > 0:
                    lic_score = lic_score_list[0]
                else:
                    lic_score = get_license_query_to_db(re_license)

                if lic_score != 1:
                    need_check = True
                    break

    return declared_lic, need_check


def set_license_score(license_type):
    score = {
        'PMS': 1,  # Permissive
        'CP': 0,  # Copyleft
        'WCP': 0,  # Weak Copyleft
        'NA': 0,  # Proprietary
        'PF': 0,  # Proprietary Free
        'NC': 0  # Legacy Type - Non Commercial
    }
    if license_type in score:
        return score[license_type]
    else:
        return 0


def get_license_query_to_db(license_name):
    license_type = 0

    db_conn, db_cur = connect_to_osc_db()
    if db_conn == "" or db_cur == "":
        return
    try:
        # Get License from DB
        sql_query = """SELECT LM.LICENSE_NAME, LICENSE_TYPE FROM LICENSE_MASTER AS LM
        LEFT OUTER JOIN LICENSE_NICKNAME AS LN ON LM.LICENSE_NAME = LN.LICENSE_NAME
        WHERE LM.LICENSE_NAME='{license_name}' OR LM.SHORT_IDENTIFIER = '{license_name}' OR LN.LICENSE_NICKNAME = '{license_name}' """.format(
            license_name=pymysql.escape_string(license_name))
        df_result = get_list_by_using_query(db_cur, sql_query, ["LICENSE_NAME", "LICENSE_TYPE"])
        if df_result is not None and len(df_result) > 0:
            for idx, row in df_result.iterrows():
                license_type = set_license_score(row['LICENSE_TYPE'])
                break
    except:
        pass

    disconnect_lge_bin_db(db_conn, db_cur)
    return license_type


def select_query_to_db(cur, license_info_from_db, where_condition):
    try:
        columns = ['LICENSE_ID', 'OSS_LICENSE_IDX', 'OSS_LICENSE_COMB', 'LICENSE_NAME', 'SHORT_IDENTIFIER',
                   'LICENSE_TYPE',
                   'LICENSE_NICKNAME']
        sql_query = """SELECT OL.LICENSE_ID
     , OL.OSS_LICENSE_IDX
     , OL.OSS_LICENSE_COMB
     , LM.LICENSE_NAME
     , LM.SHORT_IDENTIFIER
     , LM.LICENSE_TYPE
     , (SELECT GROUP_CONCAT(LICENSE_NICKNAME SEPARATOR ', ') FROM LICENSE_NICKNAME WHERE LICENSE_NAME = LM.LICENSE_NAME) AS LICENSE_NICKNAME
     FROM OSS_MASTER OM
     LEFT OUTER JOIN OSS_NICKNAME NICK ON OM.OSS_NAME = NICK.OSS_NAME
     INNER JOIN OSS_LICENSE OL ON OM.OSS_ID = OL.OSS_ID
     INNER JOIN LICENSE_MASTER LM ON OL.LICENSE_ID = LM.LICENSE_ID """
        order_condition = " ORDER BY OL.OSS_LICENSE_IDX ASC;"
        lic_group = []
        df_result = get_list_by_using_query(cur, sql_query + where_condition + order_condition, columns)

        if df_result is not None and len(df_result) > 0:
            licenses = []
            for idx, row in df_result.iterrows():
                license_name = row['LICENSE_NAME']

                if row['OSS_LICENSE_COMB'] == 'OR':
                    lic_group.append(list(set(licenses)))
                    licenses = []
                licenses.append(license_name)

                if license_name not in license_info_from_db:
                    license_info_from_db[license_name] = {}
                    license_info_from_db[license_name]['nick'] = [license_name.lower()]
                    if row['SHORT_IDENTIFIER'] is not None:
                        license_info_from_db[license_name]['nick'].append(row['SHORT_IDENTIFIER'].lower())
                    if row['LICENSE_NICKNAME'] is not None:
                        nicknames = [x.lower().strip() for x in row['LICENSE_NICKNAME'].split(',')]
                        license_info_from_db[license_name]['nick'].extend(nicknames)

                    license_info_from_db[license_name]['score'] = set_license_score(row['LICENSE_TYPE'])
            lic_group.append(list(set(licenses)))
    except Exception:
        lic_group = []
    return lic_group, license_info_from_db


def run_source_code_analysis_multiprocessing(analyze_all_mode, out_dir, output_file_without_extension):
    num_cores = multiprocessing.cpu_count() - 1
    if num_cores < 1:
        num_cores = 1
    src_anlysis_start_time = datetime.now().strftime('%y%m%d_%H%M')
    scancode_result_dir = create_dir(os.path.join(out_dir, "scancode_result"))
    recipes_to_analyze = get_recipe_for_src_analysis(analyze_all_mode)
    logger.info(
        f"Source code analysis starts for {len(recipes_to_analyze)} recipes. multiprocessing={num_cores})")
    if len(recipes_to_analyze) > 0:
        for item in recipes_to_analyze:
            scancode_output_file = os.path.join(scancode_result_dir, item['name'] + ".json")
            src_path_to_analyze = item['src']
            run_scancode_per_dir(src_path_to_analyze, scancode_output_file, num_cores, item['name'])

        manager = multiprocessing.Manager()
        return_list = manager.dict()

        splited_data = np.array_split(recipes_to_analyze, num_cores)
        splited_data = [x.tolist() for x in splited_data]

        parmap.map(get_src_analysis_result, splited_data, scancode_result_dir, return_list,
                   pm_pbar=True, pm_processes=num_cores)
        source_scan_item = ScannerItem(PKG_NAME, src_anlysis_start_time)
        print_src_analysis_result(return_list, output_file_without_extension, source_scan_item)


def run_scancode_per_dir(path_to_scan, json_file_name, num_cores, recipe_name):
    if os.path.isdir(path_to_scan):
        logger.warning("|- Analyzing: " + recipe_name + ",path:" + path_to_scan + ",json:" + json_file_name)
        try:
            rc, results = cli.run_scan(path_to_scan, max_depth=100, strip_root=True, license=True, copyright=True,
                                       return_results=True, processes=num_cores, output_json_pp=json_file_name)
        except Exception as ex:
            logger.info(str(ex))


def get_src_analysis_result(input_list, scancode_result_dir, return_list):
    for item in input_list:
        try:
            key = item['name']
            scancode_output_file = os.path.join(scancode_result_dir, item['name'] + ".json")

            if os.path.isfile(scancode_output_file):
                detected_license = get_detected_licenses_from_scancode(scancode_output_file)
                sorted_license = sorted(detected_license.values(), key=(lambda x: x['cnt']), reverse=True)
                item['license_detected'] = [license_item['key'] + "(" + str(license_item['cnt']) + ")" for license_item
                                            in
                                            sorted_license]
                item['comment'] = set_src_analysis_result(item['license'], sorted_license)
            else:
                item['comment'] = f"Source code analysis failed. SRC: {item['src']}"
        except:
            item['comment'] = "Failed to parse the source code analysis result."

        return_list[key] = item


def set_src_analysis_result(item_licenses, scancode_licenses):
    need_check = False
    comment = ""
    need_find_license = []
    item_licenses_lower = [x.lower() for x in item_licenses]
    try:
        for scancode_license in scancode_licenses:
            key = scancode_license['key']
            matched = False
            if key in _skip_to_check_scancode_licenses:
                continue
            for scancode_nick in scancode_license['nick']:
                if scancode_nick in item_licenses_lower:
                    matched = True
                    break
            if not matched:
                need_check = True
                need_find_license.append(key)
        if need_check:
            comment = f"Check detected licenses: {need_find_license}"
    except:
        comment = "Failed to parse the source code analysis result."
    return comment


def get_detected_licenses_from_scancode(scancode_json_file):
    scan_licenses = {}
    try:
        with open(scancode_json_file, "r") as st_json:
            st_python = json.load(st_json)
            for file in st_python["files"]:
                licenses = file["licenses"]
                license_detected = []
                for lic_item in licenses:
                    key_list = ["key", "name", "short_name", "spdx_license_key"]
                    replace_word = ["-only", "-old-style", "-or-later"]
                    key_value = lic_item["key"].lower()
                    if key_value not in scan_licenses:
                        scan_licenses[key_value] = {}
                        scan_licenses[key_value]['nick'] = []
                        scan_licenses[key_value]['cnt'] = 1
                        scan_licenses[key_value]['key'] = key_value
                        for key in key_list:
                            value = lic_item[key]
                            if value is not None and value != "":
                                value = value.lower()
                                license_detected.append(value)
                                for word in replace_word:
                                    if word in value:
                                        value = value.replace(word, "")
                                        license_detected.append(value)
                        if key_value in _map_license_from_yocto_to_scancode:
                            license_detected = _map_license_from_yocto_to_scancode[key_value] + license_detected

                        if len(license_detected) > 0:
                            scan_licenses[key_value]['nick'] = list(set(license_detected))
                    else:
                        scan_licenses[key_value]['cnt'] += 1

    except:
        pass
    return scan_licenses


def get_recipe_for_src_analysis(analyze_all):
    logger.warning(f"Get recipe to analyze source from {len(installed_packages_src)} packages.")
    recipes_to_analyze = []
    oss_list = {}  # Key : oss_name

    try:
        # Get all OSS Name list
        for item in installed_packages_src:
            key = item.name
            if item.src_path != "":
                if key not in oss_list:
                    oss_list[key] = {}
                    oss_list[key]['version'] = item.version
                    oss_list[key]['name'] = item.name
                    oss_list[key]['license'] = item.license
                    oss_list[key]['license_detected'] = []
                    oss_list[key]['link'] = item.download
                    oss_list[key]['src'] = item.src_path
                    oss_list[key]['db'] = False
                    oss_list[key]['comment'] = ""
                else:
                    lic_list = oss_list[key]['license']
                    if isinstance(lic_list, list):
                        lic_list.extend(item.license)
                    oss_list[key]['license'] = list(set(lic_list))

        # Check exist or not
        if not analyze_all:
            db_conn, db_cur = connect_to_osc_db()
            if db_conn != "" and db_cur != "":
                for key, oss_item in oss_list.items():
                    result = check_oss_exists_in_db(db_cur, oss_item['name'], oss_item['link'])
                    oss_item['db'] = result
                disconnect_lge_bin_db(db_conn, db_cur)

        recipes_to_analyze = [oss_item for key, oss_item in oss_list.items() if not oss_item['db']]
    except Exception as error:
        logger.debug(f"ERROR - get recipe to analyze: {error}")

    return recipes_to_analyze


def create_dir(dir_name):
    try:
        if not os.path.isdir(dir_name):
            os.mkdir(dir_name)
    except OSError:
        return ""
    return dir_name


def check_oss_exists_in_db(db_cur, name, link):
    oss_exists = False
    try:
        sql_query = """SELECT OM.OSS_NAME FROM OSS_MASTER OM
        LEFT OUTER JOIN OSS_NICKNAME NICK ON OM.OSS_NAME = NICK.OSS_NAME
        LEFT OUTER JOIN OSS_DOWNLOADLOCATION DOWNLOAD ON DOWNLOAD.OSS_ID = OM.OSS_ID
        WHERE OM.OSS_NAME = '{oss_name}' OR NICK.OSS_NICKNAME = '{oss_name}' """.format(
            oss_name=pymysql.escape_string(name))
        if link != "":
            sql_query = f"{sql_query} OR DOWNLOAD.DOWNLOAD_LOCATION='{pymysql.escape_string(link)}'"

        df_result = get_list_by_using_query(db_cur, sql_query, ["OSS_NAME"])
        if df_result is not None and len(df_result) > 0:  # Exists
            oss_exists = True
        else:
            oss_exists = False
    except Exception:
        oss_exists = False

    return oss_exists


def get_list_by_using_query(cur, sql_query, columns):
    result_rows = ""  # DataFrame
    cur.execute(sql_query)
    rows = cur.fetchall()

    if rows is not None and len(rows) > 0:
        result_rows = pd.DataFrame(data=rows, columns=columns)
    return result_rows


def connect_to_osc_db():
    user = OSC_DB_USER
    password = OSC_DB_PASSWORD
    host_product = 'osc-db.lge.com'
    dbname = 'osc'
    port = 3306
    conn = ""
    cursor = ""
    try:
        conn = pymysql.connect(host=host_product, port=port, user=user, password=password, database=dbname)
        cursor = conn.cursor()
    except Exception:
        logger.warning("Can not access to FOSSLight Hub DB.")

    return conn, cursor


def disconnect_lge_bin_db(conn, cur):
    # Close db connection
    try:
        cur.close()
        conn.close()
    except Exception:
        pass


def main():
    global installed_packages_src, installed_packages_bin, printall

    bom_file = "bom.json"
    installed_pkgs = "installed-package-names.txt"
    installed_pkgs_with_version = "installed-packages.txt"
    oss_pkg_yaml_file = ""
    buildhistory_path = ""
    bin_analysis_path = ""
    _print_bin_android = False
    _analyze_source = False
    _analyze_source_all = False
    _compress_source_all = ""
    output_path = os.getcwd()
    output_src_analysis_file = "source_analysis_report"
    file_format = ""

    parser = argparse.ArgumentParser(description='FOSSLight Yocto', prog='fosslight_yocto', add_help=False)
    parser.add_argument('-h', '--help', action='store_true', required=False)
    parser.add_argument('-v', '--version', action='store_true', required=False)
    parser.add_argument('-i', '--istalled', type=str, required=False)
    parser.add_argument('-ip', '--package', type=str, required=False)
    parser.add_argument('-y', '--yaml', type=str, required=False)
    parser.add_argument('-b', '--bom', type=str, required=False)
    parser.add_argument('-p', '--buildhistory', type=str, required=False)
    parser.add_argument('-a', '--analysis', type=str, required=False)
    parser.add_argument('-o', '--output', type=str, required=False)
    parser.add_argument('-f', '--format', type=str, required=False)
    parser.add_argument('-n', '--another', action='store_true', required=False)
    parser.add_argument('-s', '--source', action='store_true', required=False)
    parser.add_argument('-c', '--complete', action='store_true', required=False)
    parser.add_argument('-e', '--compress', type=str, required=False)
    parser.add_argument('-pr', '--printall', action='store_true', required=False)

    args = parser.parse_args()
    if args.help:
        print_help_msg_bom()
    if args.version:
        print_version(PKG_NAME)
    if args.istalled:
        installed_pkgs = args.istalled
    if args.package:
        installed_pkgs_with_version = args.package
    if args.bom:
        bom_file = args.bom
    if args.yaml:
        oss_pkg_yaml_file = args.yaml
    if args.buildhistory:
        buildhistory_path = args.buildhistory
    if args.analysis:
        bin_analysis_path = args.analysis
    if args.format:
        file_format = args.format
    if args.output:
        output_path = args.output
    if args.another:
        # Print SRC result on BIN(Android) Sheet
        _print_bin_android = True
    if args.source:
        _analyze_source = True
    if args.complete:
        _analyze_source = True
        _analyze_source_all = True
    if args.compress:
        _compress_source_all = args.compress
    if args.printall:
        printall = True

    # Output file names
    start_time = datetime.now().strftime('%y%m%d_%H%M')
    success, msg, output_path, output_file, output_extension = check_output_format(output_path, file_format)
    output_path = os.path.abspath(output_path)
    if output_file == "":
        if output_extension == '.json':
            output_file = f"fosslight_opossum_yocto_{start_time}"
        else:
            output_file = f"fosslight_report_yocto_{start_time}"
    output_file = os.path.join(output_path, output_file)
    log_file = os.path.join(output_path, f"fosslight_log_yocto_{start_time}.txt")
    logger, log_item = init_log(log_file)
    scan_item = ScannerItem(PKG_NAME, start_time)
    scan_item.set_cover_pathinfo(os.getcwd(), "")

    if not success:
        logger.error(f"(-f & -o option) Format error. {msg}")
        sys.exit(1)

    check_required_files(bom_file, installed_pkgs, buildhistory_path, installed_pkgs_with_version)

    # Parsing bom file for packages' data
    pkg_from_buildhistory = find_latest_pkg_from_buildhistory(buildhistory_path, installed_pkgs_with_version)
    if not pkg_from_buildhistory:
        sys.exit(1)
    read_bom_file(bom_file, pkg_from_buildhistory)

    # Dependency Analysis - SRC Sheet or BIN(Android) Sheet
    success = read_installed_pkg_file(installed_pkgs)
    if not success:
        sys.exit(1)

    # Binary Analysis - BIN Sheet
    if bin_analysis_path:
        success, bin_cnt = get_binary_list(find_package_files(buildhistory_path), bin_analysis_path)
        scan_item.set_cover_comment(f"Total number of binaries: {len(installed_packages_bin)}")

    # Load oss-pkg-info.yaml
    if oss_pkg_yaml_file:
        installed_packages_src, installed_packages_bin = load_oss_pkg_info_yaml(oss_pkg_yaml_file, _print_bin_android,
                                                                                installed_packages_src, installed_packages_bin, nested_pkg_name)
        scan_item.set_cover_comment(f"Load sbom-info.yaml: {oss_pkg_yaml_file}")

    # Source Code Analysis
    if _analyze_source:
        run_source_code_analysis_multiprocessing(_analyze_source_all, output_path, os.path.join(output_path, output_src_analysis_file))

    # Write the result to excel file
    write_result_from_bom(output_file, installed_packages_src, installed_packages_bin,
                          _print_bin_android, output_extension,
                          additional_columns, binary_list, scan_item)

    if _compress_source_all:
        try:
            logger.info("* Enable zip option")
            collect_source(installed_packages_src, output_path, _compress_source_all)
        except Exception as ex:
            logger.error(f"Collecting source code: {ex}")


if __name__ == "__main__":
    main()
