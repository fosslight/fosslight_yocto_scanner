# Changelog

## v4.0.9 (17/04/2026)
## Changes
## 🐛 Hotfixes

- Resolve PyMySQL compatibility and optimize DB lookups @soimkim (#63)
- Fix excel generation bugs and update DB endpoint @soimkim (#62)
- Fix the attribute errors that occur during source code analysis @hyesung22 (#60)

## 🔧 Maintenance

- Update -s flag description for source analysis @soimkim (#64)
- Add scanner version log at startup @woocheol-lge (#61)

---

## v4.0.8 (09/04/2026)
## Changes
## 🔧 Maintenance

- feat(python): add Python 3.13/3.14 support @soimkim (#59)
- Remove "Type of change" section from PR default template @woocheol-lge (#57)

---

## v4.0.7 (26/02/2026)
## Changes
## 🔧 Maintenance

- Print comment only OR in LICENSE @soimkim (#56)
- Update dependency from requirements.txt @soimkim (#55)
- Add .coderabbit.yaml configuration file for review @soimkim (#54)
- Update python version to 3.10 @soimkim (#52)

---

## v4.0.6 (16/07/2025)
## Changes
## 🔧 Maintenance

- Change the minimum Python version to 3.10 @soimkim (#51)

---

## v4.0.5 (07/03/2025)
## Changes
## 🔧 Maintenance

- Fix empty source bug after fetching source code @heedu (#50)

---

## v4.0.4 (27/02/2025)
## Changes
## 🔧 Maintenance

- Updating -e option by adding new dump feature @heedu (#47)

---

## v4.0.3 (20/02/2025)
## Changes
## 🐛 Hotfixes

- Check null into yocto_recipe/package @dd-jy (#49)

---

## v4.0.2 (15/01/2025)
## Changes
## 🐛 Hotfixes

- Change null to empty string for output @soimkim (#48)

## 🔧 Maintenance

- Exclude for packagegroup @soimkim (#46)

---

## v4.0.1 (01/11/2024)
## Changes
## 🐛 Hotfixes

- Fix AttributeError Related to os.EX_DATAERR and os.EX_NOINPUT in Windows Environment @ParkSangsin (#36)

## 🔧 Maintenance

- Update requirements.txt @dd-jy (#42)
- Print option name with error msg @bjk7119 (#40)
- Fix typo in variable name from error_mgs to error_msg @ParkSangsin (#37)

---

## v4.0.0 (08/09/2024)
## Changes
## 🔧 Maintenance

- Refactoring OSS Item from FOSSLight Util @soimkim (#33)
- Limit installation to fosslight_util 1.4.* @soimkim (#32)

---

## v3.1.31 (12/06/2024)
## Changes
## 🔧 Maintenance

- Prints even if some package is missing @soimkim (#31)

---

## v3.1.30 (10/06/2024)
## Changes
## 🚀 Features

- Add Scanner Info sheet @dd-jy (#28)

## 🔧 Maintenance

- Update the column names @soimkim (#30)
- Do not print text file @soimkim (#29)

---

## v3.1.29 (14/05/2024)
## Changes
## 🔧 Maintenance

- Do not exclude binaries without OSS information @soimkim (#27)
- Print an error if -i, -ip is entered incorrectly @soimkim (#26)

---

## v3.1.28 (11/04/2024)
## Changes
## 🔧 Maintenance

- Add PV and PR separators @soimkim (#25)

---

## v3.1.27 (09/04/2024)
## Changes
## 🚀 Features

- Add TLSH, SHA1 column at report @bjk7119 (#23)

## 🐛 Hotfixes

- Find installed packages in the latest files @soimkim (#24)

---

## v3.1.26 (06/03/2024)
## Changes
## 🐛 Hotfixes

- Print package information when using the y option @soimkim (#22)

## 🔧 Maintenance

- Remove python-magic from requirements @JustinWonjaePark (#21)
- Use common github actions @bjk7119 (#20)

---

## v3.1.25 (02/01/2024)
## Changes
## 🐛 Hotfixes

- Fix error without attribute @soimkim (#19)

---

## v3.1.24 (13/10/2023)
## Changes
## 🔧 Maintenance

- Replace ScanCode with FOSSLight Source @soimkim (#18)
- Upgrade Python minimum version to 3.8 @JustinWonjaePark (#17)

---

## v3.1.23 (11/09/2023)
## Changes
## 🔧 Maintenance

- Add error message for -a option @soimkim (#16)
- Fix the vulnerability @dd-jy (#14)

---

## v3.1.22 (25/07/2023)
## Changes
## 🔧 Maintenance

- Update the scacode-toolkit version @dd-jy (#13)

---

## v3.1.21 (20/07/2023)
## Changes
## 🔧 Maintenance

- Add fields that extract from the recipe. @soimkim (#12)

---

## v3.1.20 (11/07/2023)
## Changes
## 🔧 Maintenance

- Fix the version of ScanCode @soimkim (#11)

---

## v3.1.19 (09/07/2023)
## Changes
## 🚀 Features

- Print all data of bom.json with pr option @soimkim (#9)

## 🔧 Maintenance

- Add pr option to help messages @soimkim (#10)
- Update the ubuntu version for deploy action @dd-jy (#8)

---

## v3.1.18 (06/03/2023)
## Changes
## 🐛 Hotfixes

- Fix bug with -d option @soimkim (#7)

## 🔧 Maintenance

- Update git user in release action @bjk7119 (#6)
- Add the package name to result and log file @bjk7119 (#5)

---

## v3.1.17 (23/02/2023)
## Changes
## 🔧 Maintenance

- Add the package name to result and log file @bjk7119 (#5)
- Change the output file name @soimkim (#4)
- Add Korean link to README @soimkim (#3)

---

## v3.1.16 (10/02/2023)
## Changes
## 🔧 Maintenance

- Apply additional return val of 'parsing_yml' @bjk7119 (#2)
