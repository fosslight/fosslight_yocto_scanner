#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import logging
import fosslight_util.constant as constant
from fosslight_util.output_format import write_output_file


logger = logging.getLogger(constant.LOGGER_NAME)
OUTPUT_FILE_EXTENSION = ".xlsx"


def write_result_from_bom(out_file_name, installed_packages_src, installed_packages_bin,
                          bin_android_mode=False, output_extension="", additional_column=[]):
    SHEET_HEADER = {'BIN (Yocto)': ['ID', 'Binary Name', 'Source Code Path',
                                    'NOTICE.html', 'OSS Name', 'OSS Version',
                                    'License', 'Download Location', 'Homepage',
                                    'Copyright Text', 'Exclude', 'Comment'],
                    'SRC': ['ID', 'Source Name or Path', 'OSS Name', 'OSS Version',
                            'License', 'Download Location', 'Homepage', 'Copyright Text',
                            'Exclude', 'Comment'],
                    'BIN': ['ID', 'Binary Name', 'OSS Name', 'OSS Version',
                            'License', 'Download Location', 'Homepage',
                            'Copyright Text', 'Exclude', 'Comment']}
    sheet_list = {}
    list_src_to_print = []
    list_bin_to_print = []
    logger.debug(f"write_result_from_bom - BIN(Yocto):{bin_android_mode}, {out_file_name}")
    if additional_column:
        for sheet_header_item in SHEET_HEADER.keys():
            SHEET_HEADER[sheet_header_item].extend(additional_column)

    src_sheet_name = "BIN (Yocto)" if bin_android_mode else "SRC"
    for scan_item in installed_packages_src:
        list_src_to_print.extend(scan_item.get_print_item(bin_android_mode, additional_column))
    sheet_list[src_sheet_name] = list_src_to_print

    for scan_item in installed_packages_bin:
        list_bin_to_print.extend(scan_item.get_print_item(bin_android_mode, additional_column))

    if len(list_bin_to_print) > 0:
        sheet_list["BIN"] = list_bin_to_print

    logger.debug(f"FILE:{out_file_name}{output_extension}")
    success_to_write, writing_msg, result_file = write_output_file(out_file_name, output_extension, sheet_list, SHEET_HEADER)

    if success_to_write:
        logger.info(f"Output file :{result_file}")
    else:
        logger.error(f"Fail to generate result file.: {writing_msg}")


def print_src_analysis_result(recipe_list, output_file):
    SHEET_NAME = "Source_Analysis"
    SRC_HEADER = {SHEET_NAME: ["No", "OSS Name", "OSS Version", "Check Point", "License_OSS_Report",
                               "Detected license from ScanCode", "Download location"]}

    try:
        if len(recipe_list.keys()) > 0:
            sheet_list = {}
            list_to_print = []

            for key, item in recipe_list.items():
                list_to_print.append([item['name'], item['version'], item['comment'], ','.join(item['license']),
                                      ','.join(item['license_detected']), item['link']])

            sheet_list[SHEET_NAME] = list_to_print

            success_to_write, writing_msg, result_file = write_output_file(output_file, OUTPUT_FILE_EXTENSION, sheet_list, SRC_HEADER)

            if success_to_write:
                logger.info(f"Source Analysis - Writing Output file ({result_file}), Success: {success_to_write}")
            else:
                logger.error(f"Fail to generate result file. msg:({writing_msg})")
    except Exception as ex:
        logger.error(f'write_result_from_source_analysis:{ex}')
