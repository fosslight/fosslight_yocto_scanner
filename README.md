<!--
SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
SPDX-License-Identifier: Apache-2.0
-->
# FOSSLight Yocto Scanner

**FOSSLight Yocto Scanner** is a Python package that outputs OSS information about the package included in the rootfs image in FOSSLight Report format when building based on Yocto Project.

- How to print OSS information: Prints the OSS information (OSS Name, OSS Version, LICENSE, Download location) defined in the recipe.
- ⚠️ <U>**For images (ex- kernel, boot loader) mounted on target other than the rootfs image, the script does not print.**</U> Therefore, for this, the user must manually add OSS information to the FOSSLight Report.

## 🚀 How to run
### When you first set up your environment
```
$ pip install virtualenv  
$ virtualenv -p /usr/bin/python3.7 venv  
$ source venv/bin/activate  
(venv)$ pip install fosslight_yocto
```

### Parameters
```
Required Parameters
- i [installed-package-names.txt]
- b [bom.json]
- p [buildhistory/packages]

Optional Parameters
- a [build_analysis_path]
- y [oss-pkg-info.yaml]
- n 
- d
- s
- c
- e
- o [output_path]
- f [file_format]
```

Note.
- a option : Find & analyze binaries.
- y option : Overwrite OSS information from oss-pkg-info.yaml.
- n option : Print to BIN(Android) instead of SRC sheet.
- d option : Select license of OSS registered in OSC System.
- s option : Analyze source code.
- c option : Analysis source code for all recipes.
- e option : Fetch source codes in images with source reference text file
- o option : Output files path
- f option : Output file format (excel, csv, opossum)

### Run with minimal parameters  
```
$ fosslight_yocto -i installed-package-names.txt -b bom.json -p buildhistory/packages
```
### Run with binary analysis
```
$ fosslight_yocto -i installed-package-names.txt -b bom.json -p buildhistory/packages -a output_img_path/
```

## 👏 Contributing Guide

We always welcome your contributions.  
Please see the [CONTRIBUTING guide](https://fosslight.org/fosslight-guide-en/learn/1_contribution.html) for how to contribute.


## 📄 License

FOSSLight Yocto Scanner is Apache-2.0, as found in the [LICENSE][l] file.

[l]: https://github.com/fosslight/fosslight_yocto/blob/main/LICENSE
