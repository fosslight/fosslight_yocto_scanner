<!--
SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
SPDX-License-Identifier: Apache-2.0
-->

# Create a FOSSLight Report for projects built with yocto
## When you first set up your environment
$ pip install virtualenv  
$ virtualenv -p /usr/bin/python3.7 venv  
$ source venv/bin/activate  
$ pip install fosslight_yocto

## Parameters
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

## Run the script
### Run with minimal parameters  
```
$ fosslight_yocto -i installed-package-names.txt -b bom.json -p buildhistory/packages
```
### Run with binary analysis
```
$ fosslight_yocto -i installed-package-names.txt -b bom.json -p buildhistory/packages -a output_img_path/
```

