<!--
SPDX-FileCopyrightText: Copyright 2023 LG Electronics Inc.
SPDX-License-Identifier: Apache-2.0
-->
# FOSSLight Yocto Scanner

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
