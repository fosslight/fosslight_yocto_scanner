#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import re
from fosslight_util.oss_item import FileItem
from ._write_result_file import SHEET_NAME_SRC, SHEET_NAME_BIN, SHEET_NAME_BIN_YOCTO

const_other_proprietary_license = 'other proprietary license'
EXCLUDE_TRUE_VALUE = "Exclude"
IGNORE_COPYRIGHT = "NOASSERTION"
TLSH_CHECKSUM_NULL = "0"


class BinItem():
    def __init__(self, file_with_path, tlsh=TLSH_CHECKSUM_NULL, checksum=TLSH_CHECKSUM_NULL):
        self.source_name_or_path = file_with_path
        self.tlsh = tlsh
        self.checksum = checksum


class PackageItem(FileItem):
    def __init__(self):
        super().__init__("")
        self.oss_name = ""  # Default Value : Recipe Name
        self._name = ""  # oss name to print
        self._version = ""  # Default Value : PV
        self.license = []  # Default value : license, it will be overwritten with a pkg_license.
        self._declared_licenses = []  # Declared License in case of multi or dual licenses
        self._files = []  # Files in installed package - Value of "Binary Name"
        self.download_location = ""  # SRC_URI
        self.copyright = ""
        self.homepage = ""
        self.parent_package_name = ""  # Packages created at build time have different installed and parent package names.
        self._package_name = ""  # Installed Package name
        self.src_path = ""
        self.file_path = ""
        self.spdx_id = ""
        self._yocto_recipe = []
        self._yocto_package = []
        self.relative_path = ""
        self.additional_data = {}
        self.pv = ""
        self.pr = ""
        self._yocto_recipe = []
        self._yocto_package = []
        self.source_done = ""   # Save timestamp after source code fetch : Only for -e option
        self.full_src_uri = ""   # List all src uri links : Only for -e option
        self.pf = ""   # Package name + version value : Only for -e option

    def __eq__(self, value):
        return self.spdx_id == value

    def __del__(self):
        pass

    @property
    def files(self):
        return self._files

    @files.setter
    def files(self, value):
        if not value:
            self._files = []
        else:
            if not isinstance(value, list):
                value = value.split(",")
            self._files.extend(value)
            self._files = [item.strip() for item in self._files]
            self._files = list(set(self._files))

    @property
    def yocto_recipe(self):
        return self._yocto_recipe

    @yocto_recipe.setter
    def yocto_recipe(self, value):
        if not isinstance(value, list):
            value = value.split(",")
        value = remove_null_values(value)
        self._yocto_recipe.extend(value)
        self._yocto_recipe = [item.strip() for item in self._yocto_recipe]
        self._yocto_recipe = list(set(self._yocto_recipe))

    @property
    def yocto_package(self):
        return self._yocto_package

    @yocto_package.setter
    def yocto_package(self, value):
        if not isinstance(value, list):
            value = value.split(",")
        value = remove_null_values(value)
        self._yocto_package.extend(value)
        self._yocto_package = [item.strip() for item in self._yocto_package]
        self._yocto_package = list(set(self._yocto_package))

    @property
    def package_name(self):
        return self._package_name

    @package_name.setter
    def package_name(self, value):
        self._package_name = value

    @property
    def copyright(self):
        return self._copyright

    @copyright.setter
    def copyright(self, value):
        if value != "":
            if isinstance(value, list):
                value = "\n".join(value)
            value = value.strip()
            if value == IGNORE_COPYRIGHT:
                value = ""
        self._copyright = value

    @property
    def oss_name(self):
        return self._oss_name

    @oss_name.setter
    def oss_name(self, value):
        if value != "":
            self._name = value.replace("lib32-", "", 1)
        self._oss_name = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        str_value = str(value)
        if self._version != str_value:
            self._version = str_value
            _COMMIT_HASH = ["+gitAUTOINC+", "gitr+AUTOINC+", "+gitrAUTOINC+"]
            _TRUNCATE_WORD = ["-", "~", "+"]

            for word in _COMMIT_HASH:
                if word in str_value:
                    versions = str_value.split(word)
                    if len(versions) > 1:
                        self._version = versions[0]
                        if self.homepage == "":
                            self.homepage = self.download_location
                        if not self.download_location.endswith(";"):
                            self.download_location += ";"
                        self.download_location += f"commit:{versions[1]}"
                    break

            for word in _TRUNCATE_WORD:
                self._version = str_value.split(sep=word, maxsplit=1)[0]

    def set_license_flags(self, value):
        if value:
            self.comment = f"[NEED CHECK]LICENSE_FLAGS = {value}"

    @property
    def license(self):
        return self._license

    @license.setter
    def license(self, value, append_mode=False):

        if not append_mode:
            self._license = []
        if isinstance(value, list):
            for lic in value:
                self._license.append(update_license(lic))
        else:
            origin_lic = value

            matched_groups = re.findall(r'[^\)]+\)', value)
            license_list = ""
            for matched_group in matched_groups:
                matched_group = matched_group.strip()
                if re.search(r'^(?!like license)*(\s)*(\((.)*\))', matched_group):
                    matched_group = matched_group.replace('(', '')
                    matched_group = matched_group.replace(')', '')
                license_list += matched_group + "&"
            if license_list != "":
                value = license_list

            if '&' in value or '|' in value:
                self.comment = origin_lic
                value = value.replace('|', '&')
                license_list = value.split('&')
                for lic in license_list:
                    lic = lic.strip()
                    if lic != "":
                        self._license.append(update_license(lic))
            else:
                self._license.append(update_license(value))
        self._license = list(set(self._license))

        if len(self._license) > 1 and const_other_proprietary_license in self._license:
            self._license.remove(const_other_proprietary_license)

    @property
    def declared_licenses(self):
        return self._declared_licenses

    @declared_licenses.setter
    def declared_licenses(self, value):
        if value != "" and isinstance(value, list):
            if len(value) > 0:
                self.comment = "License changed to the license registered in OSC System DB."
                self._declared_licenses = value

    def get_print_item(self, sheet_name=SHEET_NAME_SRC, additional_column=[], binary_list=[]):
        print_items = []
        license_to_print = self.license
        exclude = EXCLUDE_TRUE_VALUE if self.exclude else ""
        if len(self.declared_licenses) > 0:
            license_to_print = self.declared_licenses
        if sheet_name == SHEET_NAME_BIN_YOCTO:
            row = [self.parent_package_name, self.oss_name, "", self.name, self.version,
                   ','.join(license_to_print), self.download_location, self.homepage,
                   self.copyright, exclude, self.comment]
            for column_name in additional_column:
                row.append(self.additional_data.get(column_name, ''))
            print_items.append(row)
        else:
            if sheet_name == SHEET_NAME_BIN:
                for pkg_file in self.files:
                    bin = next((n for n in binary_list if n.source_name_or_path == pkg_file),
                               BinItem(pkg_file, TLSH_CHECKSUM_NULL, TLSH_CHECKSUM_NULL))
                    row = [pkg_file, self.name, self.version, ','.join(license_to_print), self.download_location,
                           self.homepage, self.copyright, exclude, self.comment, bin.tlsh, bin.checksum]
                    for column_name in additional_column:
                        row.append(self.additional_data.get(column_name, ''))
                    print_items.append(row)

            elif sheet_name == SHEET_NAME_SRC:
                row = [self.parent_package_name, self.name, self.version, ','.join(license_to_print),
                       self.download_location,
                       self.homepage, self.copyright, exclude, self.comment]
                for column_name in additional_column:
                    row.append(self.additional_data.get(column_name, ''))
                print_items.append(row)
        return print_items


def update_license(license_name):
    license_map_list = {"bsd": "bsd-3-clause", "closed": const_other_proprietary_license, "mit-style": "mit-like license",
                        "bsd-style": "bsd-like license"}

    license_name = license_name.strip()
    license_name_ignore_case = license_name.lower()

    if license_name_ignore_case in license_map_list:
        return license_map_list[license_name_ignore_case]
    else:
        return license_name_ignore_case


def set_value_switch(oss, key, value, nested_pkg_name):
    if key == 'name' or key == 'oss_name':
        oss.oss_name = value
    elif key == 'version':
        oss.version = value
    elif key == 'source':
        oss.download_location = value
    elif key == 'version':
        oss.version = value
    elif key == 'copyright':
        oss.copyright = value
    elif key == 'license':
        oss.license = value
    elif key == 'file':
        oss.files = value
    elif key == 'exclude':
        oss.exclude = value
    elif key == 'comment':
        oss.comment = value
    elif key == 'homepage':
        oss.homepage = value
    elif key == 'src_path':
        oss.src_path = value
    elif key == 'file_path':
        oss.file_path = value
    elif key == 'license_flags':
        oss.set_license_flags(value)
    elif key == 'package':
        update_package_name(oss, value, nested_pkg_name)
    elif key == 'yocto_package':
        oss.yocto_package = value
    elif key == 'yocto_recipe':
        oss.yocto_recipe = value
    elif key == 'additional_data':
        oss.additional_data = value
    elif key == 'source_done':
        oss.source_done = value
    elif key == 'full_src_uri':
        oss.full_src_uri = value
    elif key == 'package_format':
        oss.pf = value


def update_package_name(oss, value, nested_pkg_name):
    if oss.package_name != value:
        if value in nested_pkg_name:
            oss.parent_package_name = nested_pkg_name[value]
            oss.comment = f"Installed Package Name: {value}"
        else:
            oss.parent_package_name = value
        oss.package_name = value
    return oss


def remove_null_values(data):
    return [item for item in data if item is not None]
