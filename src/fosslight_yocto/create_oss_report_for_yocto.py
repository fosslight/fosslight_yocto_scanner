#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import hashlib
import os
import sys
import json
import tlsh
from binaryornot.check import is_binary
import magic
import copy
import logging
import re
import stat
from fosslight_util.set_log import init_log
from fosslight_util.cover import dump_result_log
from fosslight_util.time import current_timestamp_utc, timestamp_for_filename
import fosslight_util.constant as constant
from ._zip_source_works import collect_source
from ._package_item import (
    PackageItem,
    set_value_switch,
    update_package_name,
    BinItem)
from ._write_result_file import write_result_from_bom
from tqdm import tqdm
from ._overwrite_yaml import load_oss_pkg_info_yaml
from fosslight_util.output_format import check_output_format
import argparse
from typing import List
from fosslight_util.oss_item import ScannerItem
from ._help import print_help_msg_bom, print_version

logger = logging.getLogger(constant.LOGGER_NAME)
PKG_NAME = "fosslight_yocto"

# Global variables
bom_pkg_data = {}  # Parsed from bom
installed_packages_src = []  # DEP Sheet | BIN (Yocto) Sheet
installed_packages_bin: List[PackageItem] = []  # BIN Sheet
binary_list: List[BinItem] = []  # -a option result
nested_pkg_name = {}  # Package list created at build time
additional_columns = []
printall = False  # Print all values in bom.json
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
                    "src_path": "", "file_path": "", "pv": "", "recipe_file": ""}
        additional_column = {}
        recipe_name = item.get('recipe', '')
        oss_item['oss_name'] = recipe_name
        oss_item['version'] = item.get('pv', '')
        oss_item['pv'] = item.get('pv', '')
        oss_item['recipe_file'] = item.get('file', '')
        oss_item['src_path'] = item.get('src_path', '')

        if printall:
            for key, value in item.items():
                if key not in ['src_path', 'pv', 'recipe', 'packages', 'license_flags', 'license', 'pkg_lic',
                               'src_uri', 'file_path', 'recipe_file']:
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
        error_msg += "-b bom.json\n"
    if not os.path.isfile(installed_pkgs):
        error_msg += "-i installed-package-names.txt\n"
    if not os.path.isdir(buildhistory_path) or buildhistory_path == "":
        error_msg += "-p path/to/buildhistory\n"
    if not os.path.isfile(installed_pkgs_version):
        error_msg += "-ip installed-packages.txt\n"

    if error_msg != "":
        exit_with_error_msg("Check Arguments\n" + error_msg, EX_NOINPUT)


def exit_with_error_msg(error_msg, exit_code=EX_DATAERR):
    logger.error(error_msg)
    sys.exit(exit_code)


def main():
    global installed_packages_src, installed_packages_bin, printall

    bom_file = "bom.json"
    installed_pkgs = "installed-package-names.txt"
    installed_pkgs_with_version = "installed-packages.txt"
    oss_pkg_yaml_file = ""
    buildhistory_path = ""
    bin_analysis_path = ""
    _print_bin_android = False
    _compress_source_all = ""
    output_path = os.getcwd()
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
    if args.compress:
        _compress_source_all = args.compress
    if args.printall:
        printall = True

    # Output file names
    start_time = current_timestamp_utc()
    file_time = timestamp_for_filename(start_time)
    success, msg, output_path, output_file, output_extension = check_output_format(output_path, file_format)
    output_path = os.path.abspath(output_path)
    if output_file == "":
        if output_extension == '.json':
            output_file = f"fosslight_opossum_yocto_{file_time}"
        else:
            output_file = f"fosslight_report_yocto_{file_time}"
    output_file = os.path.join(output_path, output_file)
    logger, log_item = init_log(os.path.join(output_path, f"fosslight_log_yocto_{file_time}.txt"),
                                True, logging.INFO, logging.DEBUG, PKG_NAME)
    logger.info(f"Tool Info : {log_item['Tool Info']}")
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

    # Dependency Analysis - DEP Sheet or BIN(Yocto) Sheet
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

    # Write the result to excel file
    finish_time = current_timestamp_utc()
    scan_item.set_cover_finish_time(finish_time)
    write_result_from_bom(output_file, installed_packages_src, installed_packages_bin,
                          _print_bin_android, output_extension,
                          additional_columns, binary_list, scan_item)

    if _compress_source_all:
        try:
            logger.info("* Enable zip option")
            collect_source(installed_packages_src, output_path, _compress_source_all)
        except Exception as ex:
            logger.error(f"Collecting source code: {ex}")

    log_item["Running time"] = scan_item.cover.running_time
    try:
        logger.info(dump_result_log(log_item))
    except Exception as ex:
        logger.warning(f"Failed to print result log. {ex}")


if __name__ == "__main__":
    main()
