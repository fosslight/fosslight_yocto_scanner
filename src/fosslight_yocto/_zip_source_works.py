#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
import shutil
import zipfile
import tarfile
import logging
import fosslight_util.constant as constant
from fosslight_util.write_txt import write_txt_file
import stat
from fosslight_binary.binary_analysis import check_binary
from tqdm import tqdm


logger = logging.getLogger(constant.LOGGER_NAME)
SOURCE_DESC_DIR_NAME = "package_zips"
source_desc_folder = SOURCE_DESC_DIR_NAME
FINAL_ZIP_FILE_NAME = "packages.tar.gz"
INTERNAL_SRC_TXT_FILE = "oss_source_path.txt"
FAILED_ZIP_LIST = "failed_to_compress_list.txt"
ZIP_FILE_EXTENSION = ".zip"
EXCLUDE_FILE_EXTENSION = ['socket']


def is_exclude_file(file_abs_path):
    excluded = False
    try:
        extension = os.path.splitext(file_abs_path)[1][1:]
        if stat.S_ISFIFO(os.stat(file_abs_path).st_mode):
            excluded = True
        elif extension in EXCLUDE_FILE_EXTENSION:
            excluded = True
    except Exception as ex:
        logger.debug(f'Failed to check: {ex}')
    return excluded


def zip_module(orig_path, desc_name):
    FAILED_MSG_PREFIX = "Failed: " + desc_name + " " + orig_path
    success = True
    failed_msg = [FAILED_MSG_PREFIX]
    desc_name = desc_name.strip()
    zip_name = desc_name + ZIP_FILE_EXTENSION

    if desc_name == "":
        logger.debug("Recipe name is missing")
    elif orig_path != "" and os.path.exists(orig_path):
        abs_src = os.path.abspath(orig_path)
        des_path = os.path.join(source_desc_folder, zip_name)
        compress_file = []
        zip_object = zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED)
        for dir_name, sub_dirs, files in os.walk(orig_path):
            for filename in files:
                try:
                    abs_name = os.path.abspath(os.path.join(dir_name, filename))
                    if is_exclude_file(abs_name):
                        continue
                    if os.path.islink(abs_name):
                        abs_name = os.readlink(abs_name)
                        if not os.path.isfile(abs_name):
                            continue
                    if (not check_binary(abs_name)) and (abs_name not in compress_file):
                        relpath = os.path.relpath(abs_name, abs_src)
                        compress_file.append(abs_name)
                        zip_object.write(abs_name, relpath)
                except Exception as ex:
                    success = False
                    failed_msg.append(f'|--- {ex}')
        try:
            zip_object.close()
            shutil.move(zip_name, des_path)
        except Exception as ex:
            success = False
            failed_msg.append(f'|--- {ex}')
    else:
        success = False
        failed_msg.append(f"|--- Can't find source path: {orig_path}")

    return success, failed_msg


def zip_compressed_source(output_dir="", total_list=[]):
    success = False
    zip_files = []
    final_zip_file = os.path.join(output_dir, FINAL_ZIP_FILE_NAME)

    for file_in_pkg in os.listdir(source_desc_folder):
        if file_in_pkg.endswith(ZIP_FILE_EXTENSION):
            f_path = os.path.join(source_desc_folder, file_in_pkg)
            zip_files.append(f_path)
            total_list.remove(file_in_pkg)
    if len(zip_files) > 0:
        logger.info(f"\n* List included in {final_zip_file}")
        try:
            with tarfile.open(final_zip_file, "w:gz") as tar:
                for zip_file in zip_files:
                    tar.add(zip_file)
                    logger.debug(f'Compress : {zip_file}')
            tar.close()
            success = True
        except Exception as ex:
            success = False
            logger.error(f'Failed to compress: {ex}')
        if len(total_list) > 0:
            logger.info("\n* Recipes not included in the package file")
            logger.info("\n".join(total_list))
    else:
        logger.warning("\n* There is no zip file to compress.")
    if success:
        logger.info(f"\n* Final compressed file: {final_zip_file}")


def collect_source(pkg_list, output_dir):
    global source_desc_folder
    if output_dir == "":
        output_dir = os.getcwd()
    source_desc_folder = os.path.join(output_dir, SOURCE_DESC_DIR_NAME)
    output_src_txt = os.path.join(output_dir, INTERNAL_SRC_TXT_FILE)
    output_failed_txt = os.path.join(output_dir, FAILED_ZIP_LIST)

    bom_recipe_data = {}

    for pkg_item in pkg_list:
        if pkg_item.oss_name not in bom_recipe_data:
            bom_recipe_data[pkg_item.oss_name] = pkg_item

    if os.path.exists(source_desc_folder):
        shutil.rmtree(source_desc_folder, ignore_errors=True)
    os.makedirs(source_desc_folder)

    output_src_str = []
    failed_list = []
    total_list = []
    success_list = []

    for recipe_name, recipe_item in tqdm(bom_recipe_data.items()):
        src_uri = recipe_item.download
        base_path = recipe_item.file_path

        # zip downloaded source codes and located to package_zip folders
        total_list.append(recipe_name + ZIP_FILE_EXTENSION)
        success, failed_msg = zip_module(recipe_item.src_path, recipe_name)
        if success:
            success_list.append(recipe_name)
        else:
            failed_list.extend(failed_msg)

        # check whether yocto recipe is from LGE repositories
        if src_uri.startswith("file://"):
            if "recipe" in base_path:
                real_path = base_path
            else:
                real_path = os.path.join(base_path, src_uri.replace("file://", ''))
            output_src_str.append(f'{recipe_name}: {real_path}')

    if success_list:
        str_success_list = "\n".join(success_list)
        logger.info(f'* Success List:\n{str_success_list}')
    if len(output_src_str) > 0:
        logger.info(f'* Internal Source path: {output_src_txt}')
        write_txt_file(output_src_txt, "\n".join(output_src_str))
    if len(failed_list) > 0:
        logger.warning(f'* Compression failed list: {output_failed_txt}')
        write_txt_file(output_failed_txt, "\n".join(failed_list))

    # zip package source codes
    zip_compressed_source(output_dir, total_list)
