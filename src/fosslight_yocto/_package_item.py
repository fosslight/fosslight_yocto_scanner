#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import re
from fosslight_util.oss_item import OssItem

const_other_proprietary_license = 'other proprietary license'
EXCLUDE_TRUE_VALUE = "Exclude"
IGNORE_COPYRIGHT = "NOASSERTION"


class PackageItem(OssItem):
    def __init__(self):
        self.oss_name = ""  # Default Value : Recipe Name
        self._name = ""  # oss name to print
        self._version = ""  # Default Value : PV
        self.license = []  # Default value : license, it will be overwritten with a pkg_license.
        self._declared_licenses = []  # Declared License in case of multi or dual licenses
        self._source_name_or_path = []  # Files in installed package - Value of "Binary Name"
        self.download_location = ""  # SRC_URI
        self.copyright = ""
        self._comment = ""
        self.exclude = False
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

    def __eq__(self, value):
        return self.spdx_id == value

    def __del__(self):
        pass

    @property
    def package_name(self):
        return self._package_name

    @package_name.setter
    def package_name(self, value):
        self._package_name = value

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, value):
        prefix = False
        comment_value = value
        if type(value) is tuple:
            comment_value, prefix = value
        if self._comment:
            if prefix:
                self._comment = f"{comment_value}/{self._comment}"
            else:
                if comment_value != "":
                    self._comment = f"{self._comment}/{comment_value}"
        else:
            self._comment = comment_value
        self._comment = self._comment.replace("//", "/")

    @property
    def copyright(self):
        return self._copyright

    @copyright.setter
    def copyright(self, value):
        if value:
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
                self.comment = (origin_lic, True)
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

    def get_print_item(self, bin_android_format=False, additional_column=[]):
        print_items = []
        license_to_print = self.license
        exclude = EXCLUDE_TRUE_VALUE if self.exclude else ""
        if len(self.declared_licenses) > 0:
            license_to_print = self.declared_licenses
        if bin_android_format:  # BIN(Android) Sheet
            row = [self.parent_package_name, self.oss_name, "", self.name, self.version,
                   ','.join(license_to_print),
                   self.download_location, self.homepage, self.copyright, exclude, self.comment]
            for column_name in additional_column:
                row.append(self.additional_data.get(column_name, ''))
            print_items.append(row)
        else:
            if len(self.source_name_or_path) > 0:  # BIN Sheet
                for file in self.source_name_or_path:
                    row = [file, self.name, self.version, ','.join(license_to_print), self.download_location,
                           self.homepage, self.copyright, exclude, self.comment]
                    for column_name in additional_column:
                        row.append(self.additional_data.get(column_name, ''))
                    print_items.append(row)

            else:  # SRC Sheet
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
        oss.source_name_or_path = value
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


def update_package_name(oss, value, nested_pkg_name):
    if oss.package_name != value:
        if value in nested_pkg_name:
            oss.parent_package_name = nested_pkg_name[value]
            oss.comment = f"Installed Package Name: {value}"
        else:
            oss.parent_package_name = value
        oss.package_name = value
    return oss
