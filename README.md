<!--
SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
SPDX-License-Identifier: Apache-2.0
-->
<p align='right'>
  <a href="https://fosslight.org/fosslight-guide/scanner/5_yocto.html">
    [Korean]
 </a>
</p>

# FOSSLight Yocto Scanner
<img src="https://img.shields.io/pypi/l/fosslight_yocto" alt="FOSSLight Yocto Scanner is released under the Apache-2.0 License." /> <img src="https://img.shields.io/pypi/v/fosslight_yocto" alt="Current python package version." /> <img src="https://img.shields.io/pypi/pyversions/fosslight_yocto" /> [![REUSE status](https://api.reuse.software/badge/github.com/fosslight/fosslight_yocto_scanner)](https://api.reuse.software/info/github.com/fosslight/fosslight_yocto_scanner) [![Guide](http://img.shields.io/badge/-doc-blue?style=flat-square&logo=github&link=https://fosslight.org/fosslight-guide-en/scanner/5_yocto.html)](https://fosslight.org/fosslight-guide-en/scanner/5_yocto.html)
</p>

**FOSSLight Yocto Scanner** is a Python package that outputs OSS information about the package included in the rootfs image in FOSSLight Report format when building based on Yocto Project.

- How to print OSS information: Prints the OSS information (OSS Name, OSS Version, LICENSE, Download location) defined in the recipe.
- ⚠️ <U>**For images (ex- kernel, boot loader) mounted on target other than the rootfs image, the script does not print.**</U> Therefore, for this, the user must manually add OSS information to the FOSSLight Report.


## 📖 User Guide

We describe the user guide in the FOSSLight guide page.
Please see the [**User Guide**](https://fosslight.org/fosslight-guide-en/scanner/5_yocto.html) for more information on how to install and run it.


## 👏 Contributing Guide

We always welcome your contributions.  
Please see the [CONTRIBUTING guide](https://fosslight.org/fosslight-guide-en/learn/1_contribution.html) for how to contribute.


## 📄 License

FOSSLight Yocto Scanner is Apache-2.0, as found in the [LICENSE][l] file.

[l]: https://github.com/fosslight/fosslight_yocto/blob/main/LICENSE
