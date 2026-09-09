<!--
SPDX-FileCopyrightText: Copyright 2026 LG Electronics Inc.
SPDX-License-Identifier: Apache-2.0
-->

# Yocto create-spdx 2.2 vs fosslight_yocto spreadsheet

같은 Yocto 빌드에서 나온 두 산출물을 FOSSLight Hub Identification에 넣었을 때, **어떤 행이 생기고 각 필드가 어떻게 채워지는지**를 비교한다.

| 경로 | 입력 | Hub에 들어가는 방식 |
| ---- | ---- | ------------------- |
| A. Yocto `create-spdx` 2.2 | `*.spdx.json` (스펙 `SPDX-2.2`) | Hub `docs/project/load/spdx.md` (SPDX 2.3 규칙, 2.2에도 동일 적용) |
| B. `fosslight_yocto` | `bom.json` + `buildhistory` + `installed-package-names.txt` | FOSSLight Report spreadsheet (기본 **DEP** 시트, `-n`이면 **BIN (Yocto)**, `-a`면 **BIN** 추가) |

SPDX 생성 방법: [create-spdx.md](./create-spdx.md)

아래 필드 예시는 Scarthgap(5.0) `core-image-minimal` 빌드의 `tmp/deploy/spdx/2.2/` 실제 값이다. Hub load 결과는 `spdx.md` 규칙에 그 값을 대입한 것이다.

## 1. 파이프라인이 보는 단위가 다르다

이 차이가 필드 매핑보다 먼저 온다. 같은 이미지라도 **행 집합과 OSS Name이 일치하지 않는다.**

### fosslight_yocto (B)

- 행 1개 = **이미지에 설치된 패키지 1개** (`installed-package-names.txt`)
- OSS Name = **레시피 PN** (`bom.json`의 `recipe`). `lib32-` prefix만 제거
- 같은 레시피에서 나온 패키지(`busybox`, `busybox-syslog`)는 OSS Name/Version이 같고, 설치 패키지 이름만 Comment 등에 남을 수 있다
- `packagegroup-*` 는 Exclude
- native / 미설치 레시피는 행이 없다

### Yocto SPDX 2.2 → Hub (A)

산출물이 **문서 여러 장**으로 나뉜다. Hub는 파일 하나(변환된 Package Info 시트)의 `packages[]`만 읽고, **다른 JSON의 필드를 따라가지 않는다.** `externalDocumentRefs` / `relationships`는 변환 과정에서 제거되기도 한다.

| 문서 | `packages[]` | Hub가 load하는 OSS Name | 비고 |
| ---- | ------------ | ----------------------- | ---- |
| 이미지 (`<image>.spdx.json`) | 이미지 레시피 1개 (`core-image-minimal`) | 이미지 이름 | `CONTAINS`로 설치 패키지를 **다른 파일**에 가리킴. 이미지 JSON만 올리면 설치 OSS가 안 들어온다 |
| 패키지 (`<pkg>.spdx.json`) | 설치/생성 패키지 1개 (`busybox`, `busybox-syslog`, `libc6`) | **패키지 이름** (PKG) | 레시피 문서의 homepage / source download를 포함하지 않음 |
| 레시피 (`recipe-<pn>.spdx.json`) | 레시피 PN + `{PN}-source-N` | `busybox` 와 `busybox-source-1` **두 행** | source 패키지는 다운로드 URL만 있고 버전·라이선스가 비어 있다 |
| runtime (`runtime-<pkg>.spdx.json`) | 패키지 없음 | 행 없음 | `RUNTIME_DEPENDENCY_OF` / `AMENDS`만 있음. Hub는 `DEPENDS_ON`만 load |

이미지 `.spdx.tar.zst`를 통째로 올려도 Hub는 멀티 문서 아카이브를 하나의 SBOM으로 합치지 않는다. 패키지 JSON을 각각 올리면 행은 설치 패키지에 가깝지만, OSS Name이 `libc6`처럼 **패키지명**이 된다. fosslight_yocto는 같은 구성 요소를 `glibc`로 쓴다.

```text
레시피 glibc  (PV=2.39+git)
  ├─ 패키지 SPDX name = libc6          ← Hub A (패키지 JSON)
  ├─ 패키지 SPDX name = libc6-dev
  └─ fosslight OSS Name = glibc        ← Hub B (DEP)
```

## 2. Hub Identification 필드 비교

`spdx.md` Package Info 컬럼과 fosslight_yocto DEP 컬럼을 같은 Hub 필드에 맞춰 본다. 값은 “그 경로를 그대로 load했을 때”이다.

| Hub 필드 | A. SPDX 2.2 → `spdx.md` | B. fosslight_yocto DEP | 일치? |
| -------- | ----------------------- | ---------------------- | ----- |
| OSS Name | `packages[].name` | 레시피 PN (`lib32-` 제거) | 아니오. A는 문서 종류에 따라 이미지명 / 패키지명 / `{PN}-source-N` |
| OSS version | `versionInfo` 그대로 | `PV`를 `-` `~` `+`에서 자르고, `+gitAUTOINC+` 등은 commit을 Download에 붙임 | 아니오. A: `2.39+git` / B: `2.39` |
| Download location | `downloadLocation`. `NONE`/`NOASSERTION` → 공란 | `SRC_URI` **첫 항목** 원문 | 아니오. 패키지/레시피 SPDX는 `NOASSERTION` → 공란. 실제 URL은 `{PN}-source-N`에만 있음 |
| Homepage | `homepage`. 없으면 공란(또는 `NONE`) | 기본 공란. git AUTOINC일 때만 Download를 복사 | 아니오. A는 레시피 문서에만 HOMEPAGE가 있음 |
| License | `licenseConcluded`. 없거나 공란/`NONE`/`NOASSERTION`이면 `licenseDeclared`. AND/OR면 분할하고 원문을 Comment에 둠 | `LICENSE` / `pkg_lic`, 소문자, `&`/`|` 분할. `CLOSED` → `other proprietary license` | 부분. 폴백 후 A는 SPDX ID(`GPL-2.0-only`). B는 소문자. `CLOSED`/`NONE`은 A 공란 / B `other proprietary license` |
| Copyright | `copyrightText`. `NONE`/`NOASSERTION` → 공란 | `NOASSERTION`이면 공란. yaml 덮어쓰기가 없으면 비어 있음 | 예(둘 다 공란). Yocto 2.2는 copyright를 안 채움 |
| Comment | `licenseComments` + (AND/OR 라이선스 원문) | `LICENSE_FLAGS`, dual/`|` 원문, nested 설치 패키지명 | 아니오 |
| Package URL | `externalRefs` 중 `purl` | `pkg:yocto/{BPN}@{PV}` | 아니오. Yocto 2.2는 CPE만 넣고 purl이 없음 → A는 공란 |
| Depends On | `relationships[]`의 **`DEPENDS_ON`만**, 대상 PURL로 변환 | 항상 빈 문자열 | 예(둘 다 공란). Yocto는 `DEPENDS_ON`을 안 씀 |
| Exclude | 없음 | `packagegroup-*` | 아니오 |

기본 DEP 시트 컬럼(B): Package URL, OSS Name, OSS Version, License, Download Location, Homepage, Copyright Text, Exclude, Comment, Depends On.

SPDX를 Hub에 올리면 Package Info가 Identification(보통 SRC 계열)으로 들어가고, DEP 탭용 PURL/Depends On은 비어 있다. fosslight_yocto Excel을 올리면 **DEP 탭**으로 들어간다.

## 3. 필드별 상세

### 3.1 OSS Name

**A.** 업로드한 JSON의 `name` 그대로.

- 레시피: `busybox`, `glibc`
- 패키지: `busybox`, `busybox-syslog`, `libc6`
- 소스: `busybox-source-1`, `glibc-source-1`
- 이미지: `core-image-minimal`

**B.** 항상 레시피. `busybox-syslog` 행도 OSS Name은 `busybox`.

Hub OSS DB 매칭이 Name+Version 기준이면, A(패키지 JSON)는 `libc6` / `busybox-syslog`로 찾고 B는 `glibc` / `busybox`로 찾는다.

### 3.2 OSS version

**A.** `PV` 원문. 예: `1.36.1`, `2.39+git`.

**B.** `PackageItem.version` setter:

1. `+gitAUTOINC+` / `gitr+AUTOINC+` / `+gitrAUTOINC+`가 있으면 앞을 버전으로 쓰고, 뒤를 `download_location`에 `commit:`으로 붙임
2. 그다음 원문 `PV`를 `-`, `~`, `+` 기준으로 한 번 더 자름

예: SPDX `2.39+git` → fosslight `2.39`.

### 3.3 Download location

Yocto 2.2는 레시피/패키지 패키지에 `downloadLocation`을 넣지 않는다(기본 `NOASSERTION`). 실제 주소는 레시피 문서의 `{PN}-source-N`에만 있다.

| 객체 | 실제 예 | Hub A load |
| ---- | ------- | ---------- |
| recipe `busybox` | `NOASSERTION` | 공란 |
| package `busybox` | `NOASSERTION` | 공란 |
| `busybox-source-1` | `https://busybox.net/downloads/busybox-1.36.1.tar.bz2` | 해당 URL |
| `glibc-source-1` | `git+https://sourceware.org/git/glibc.git@be1e627c...` | 해당 URI |

create-spdx는 fetch URL을 `type+proto://host/path@srcrev`로 다시 만든다. `file://` SRC_URI는 source 패키지 자체를 만들지 않는다.

**B.** `bom.json` `src_uri`의 **첫 토큰**을 그대로 쓴다. BitBake 원문이라 `git://...;protocol=https;branch=...` 또는 `file://...`가 그대로 남는다. A의 `git+https://...@rev`와 문자열이 다르다.

패키지 JSON만 Hub에 올리면 Download는 전부 공란이다. 레시피 JSON을 올리면 `busybox` 행은 공란이고 `busybox-source-1` 행에만 URL이 있다.

### 3.4 Homepage

**A.** 레시피 패키지에만 `HOMEPAGE`가 있을 때 채워진다. 예: busybox `https://www.busybox.net`. 패키지 JSON에는 `homepage` 키가 없다 → 공란.

**B.** 레시피 `HOMEPAGE`를 읽지 않는다. git AUTOINC 버전일 때만 Download를 Homepage에 복사한다.

### 3.5 License

Hub `spdx.md`는 `licenseConcluded`를 먼저 보고, 없거나 공란/`NONE`/`NOASSERTION`이면 `licenseDeclared`로 폴백한다.

Yocto create-spdx 2.2는 라이선스를 **`licenseDeclared`에만** 넣고, `licenseConcluded`는 항상 `NOASSERTION`이다. (Scarthgap 샘플: 레시피 164개, 패키지 4008개 모두 동일) 폴백이 있어야 Identification에 라이선스가 들어간다.

| | recipe-busybox | package busybox | fosslight_yocto |
| - | -------------- | --------------- | --------------- |
| declared | `GPL-2.0-only AND LicenseRef-bzip2-1.0.4` | `GPL-2.0-only AND DocumentRef-recipe-busybox:LicenseRef-bzip2-1.0.4` | (없음, BitBake `LICENSE` 사용) |
| concluded | `NOASSERTION` | `NOASSERTION` | — |
| Hub License (폴백 후) | `GPL-2.0-only`, `LicenseRef-bzip2-1.0.4` (AND 분할, 원문은 Comment) | `GPL-2.0-only`, `DocumentRef-recipe-busybox:LicenseRef-bzip2-1.0.4` | `gpl-2.0-only,bzip2-1.0.4` (소문자, `&`/`|` → 콤마) |

추가로:

- Yocto는 `LICENSE=CLOSED`를 SPDX `NONE`으로 바꾼다. concluded·declared 모두 `NONE`이면 Hub는 공란. fosslight는 `other proprietary license`
- Yocto는 `SPDXLICENSEMAP`으로 SPDX ID를 쓴다 (`GPL-2.0-only`, `BSD-3-Clause`)
- fosslight는 소문자 + 일부 별칭 (`bsd` → `bsd-3-clause`, `mit-style` → `mit-like license`)
- dual/`|` : Yocto declared는 `BSD-3-Clause OR GPL-2.0-only`. Hub는 분할하고 원문을 Comment에 넣는다. fosslight는 `|`를 `&`로 바꾸고 원문을 Comment에 넣는다
- 패키지 declared의 `DocumentRef-recipe-...:LicenseRef-...`는 다른 파일의 Extracted License를 가리킨다. Hub는 파일 밖으로 따라가지 않는다

폴백 전에는 AND/OR 분할이 적용될 concluded가 없었다. 폴백 후에는 declared 표현식에 분할이 적용된다.

### 3.6 Copyright

Yocto 2.2는 `copyrightText`를 넣지 않아 `NOASSERTION` → 양쪽 공란. B는 `oss-pkg-info.yaml`(`-y`)이 있을 때만 채워질 수 있다.

### 3.7 Package URL

**A.** Yocto 2.2 `externalRefs`는 CPE(`SECURITY` / `cpe23Type`)뿐이다. `referenceType: purl`이 없다. Hub PURL 규칙은 Category `PACKAGE-MANAGER` + Type `purl`만 보므로 Package URL은 공란. (변환 시 `externalRefs`를 지우면 더 그렇다.)

**B.** `pkg:yocto/{BPN}@{PV}`. BPN은 PN에서 `lib32-` / `-native` 등 prefix·suffix를 뗀 값. 버전은 자른 Identification 버전이 아니라 bom의 `pv`를 쓴다. 예: `pkg:yocto/busybox@1.36.1`, `pkg:yocto/glibc@2.39+git`.

### 3.8 Depends On

Hub는 `DEPENDS_ON`만 PURL 목록으로 load한다.

Yocto 2.2가 쓰는 관계:

| relationshipType | 위치 | Hub load |
| ---------------- | ---- | -------- |
| `DESCRIBES` | 모든 문서 | 무시 |
| `CONTAINS` | 이미지→패키지, 패키지→파일 | 무시 (`DEPENDS_ON` 아님) |
| `GENERATED_FROM` | 패키지→레시피, 파일→소스 | 무시 |
| `BUILD_DEPENDENCY_OF` | 레시피 문서 | `spdx.md` 참고 표에만 있음. load 안 함 |
| `RUNTIME_DEPENDENCY_OF` | runtime 문서 | 참고 표에만 있음. load 안 함 |
| `AMENDS` | runtime | 무시 |
| `DEPENDS_ON` | 없음 | — |

**B.** DEP `Depends On` 컬럼을 항상 `""`로 쓴다. 런타임 의존(`RDEPENDS`)을 시트에 넣지 않는다.

결과: 어느 경로로 올려도 Hub Depends On은 비어 있다. 정보는 runtime SPDX / buildhistory에 있으나 양쪽 파서가 안 읽는다.

### 3.9 Comment / Exclude

**A.** Yocto는 `licenseComments`를 안 넣는다. concluded가 AND/OR가 아니면 Comment도 공란. Exclude 없음.

**B.**

- `LICENSE_FLAGS`가 있으면 `[NEED CHECK]LICENSE_FLAGS = ...`
- `|` dual license면 원문 expression
- buildhistory nested 패키지면 `Installed Package Name: <pkg>`
- `packagegroup-*` → Exclude

## 4. Per File Info / BIN

### A. SPDX Per File Info

패키지 JSON은 `PKGDEST` 파일을 `files[]`로 넣고 `CONTAINS`로 잇는다. 예: `busybox.spdx.json` 파일 4개.

`spdx.md`는 Per File Info의 File Name을 SRC/BIN 경로로 읽고, Package Identifier로 패키지 Name/Version/Download/Homepage를 붙인다. 다만 Yocto 패키지의 Download/Homepage는 비어 있고, License는 파일 `licenseConcluded`도 보통 없어 공란에 가깝다. `SPDX_INCLUDE_SOURCES=1`이면 레시피 문서에 SOURCE 파일이 추가된다.

Hub가 SPDX를 spreadsheet로 바꿀 때 relationships를 제거하면 `hasFiles` 매칭이 약해질 수 있다.

### B. fosslight_yocto BIN

`-a`로 분석 경로를 줄 때만 BIN 시트가 생긴다. Binary Path + OSS 정보 + TLSH/SHA1. 기본 실행에는 파일 단위 행이 없다.

`-n`이면 설치 패키지를 BIN (Yocto) 시트에 쓴다: Binary Path = parent package name, Source Path = 레시피명.

## 5. 같은 구성 요소를 한 줄로 보면

`busybox` 1.36.1 (설치된 패키지 `busybox`) 기준.

| 필드 | A. 패키지 JSON `busybox.spdx.json` | A. 레시피 JSON `recipe-busybox.spdx.json` (busybox 행) | B. fosslight_yocto DEP |
| ---- | ---------------------------------- | ----------------------------------------------------- | ---------------------- |
| OSS Name | `busybox` | `busybox` | `busybox` |
| Version | `1.36.1` | `1.36.1` | `1.36.1` |
| Download | 공란 | 공란 (`busybox-source-1` 행에 URL) | `https://busybox.net/downloads/busybox-1.36.1.tar.bz2` (SRC_URI 첫 항) |
| Homepage | 공란 | `https://www.busybox.net` | 공란 |
| License | `GPL-2.0-only`, `DocumentRef-recipe-busybox:LicenseRef-bzip2-1.0.4` (declared 폴백) | `GPL-2.0-only`, `LicenseRef-bzip2-1.0.4` | `gpl-2.0-only` 및 레시피 라이선스(소문자) |
| Copyright | 공란 | 공란 | 공란 |
| Package URL | 공란 | 공란 (CPE만 있음) | `pkg:yocto/busybox@1.36.1` |
| Depends On | 공란 | 공란 | 공란 |

`glibc` → 설치된 `libc6`:

| 필드 | A. `libc6.spdx.json` | B. DEP |
| ---- | -------------------- | ------ |
| OSS Name | `libc6` | `glibc` |
| Version | `2.39+git` | `2.39` |
| Download | 공란 | 레시피 `SRC_URI` 첫 항 |
| License | `GPL-2.0-only`, `LGPL-2.1-or-later` (declared 폴백) | `gpl-2.0-only,lgpl-2.1-or-later` 형태 |
| Package URL | 공란 | `pkg:yocto/glibc@2.39+git` |

## 6. `create-spdx`로 Hub Identification을 대체하면 빠지는 것

Yocto SPDX 2.2를 `spdx.md` 규칙 그대로 올리면, fosslight_yocto DEP와 비교해 아래가 비거나 달라진다.

1. **License 표기** — 폴백 후 SPDX ID는 들어오지만, 소문자/별칭/`CLOSED`→Other Proprietary는 fosslight_yocto와 다르다. 패키지 JSON의 `DocumentRef-...:LicenseRef-...`는 파일 밖이라 깨진 채로 남을 수 있다
2. **Download** — 패키지 단위 업로드 시 공란. 레시피의 `{PN}-source-N`을 같이 해석해야 함
3. **Homepage** — 패키지 문서에 없음. 레시피 문서와 `GENERATED_FROM`으로 묶어야 함
4. **Package URL** — Yocto 2.2에 purl 없음. DEP 트리/PURL 매칭 불가
5. **OSS Name** — 패키지명 vs 레시피명 (`libc6` vs `glibc`)
6. **Version 정규화** — `2.39+git` vs `2.39`
7. **설치 패키지만 남기기** — 이미지 JSON만으로는 부족하고, 레시피 JSON은 `*-source-N`·미설치 패키지까지 섞임
8. **CLOSED → Other Proprietary License** — SPDX `NONE` → Hub 공란
9. **Depends On** — 어느 쪽도 Hub가 기대하는 `DEPENDS_ON`+purl을 안 만듦
10. **멀티 파일** — homepage/download/licenseRef/런타임 의존이 파일 밖에 있음. Hub는 파일 하나에서만 찾음

반대로 SPDX 쪽에만 있는 것: CPE, `BUILD_DEPENDENCY_OF`, 패키지 파일 해시, Extracted License 텍스트, 이미지 `CONTAINS` 그래프. 현재 Hub SPDX load는 이를 Identification 필드로 쓰지 않는다.

## 7. 정리

- Hub `spdx.md`는 SPDX 2.2/2.3 Package Info의 **한 파일 안** `name` / `versionInfo` / `downloadLocation` / `homepage` / **`licenseConcluded`(없으면 `licenseDeclared`)** / `copyrightText` / purl / `DEPENDS_ON`만 Identification에 넣는다
- Yocto create-spdx 2.2는 concluded를 `NOASSERTION`으로 두고 라이선스는 declared에 넣는다. 다운로드·purl·`DEPENDS_ON`은 Hub가 읽는 칸에 거의 없다. 값은 `{PN}-source-N`, CPE, `GENERATED_FROM` / `CONTAINS` / `RUNTIME_DEPENDENCY_OF`에 흩어져 있다
- fosslight_yocto는 설치 패키지 목록 + bom으로 **레시피 기준 DEP 행**을 만들고, 라이선스 별칭·버전 truncate·`pkg:yocto/...` PURL을 채운다. Homepage·Copyright·Depends On은 기본값으로는 SPDX와 같이 비어 있는 경우가 많다

네이티브 SPDX 2.2를 fosslight_yocto 출력 대신 Hub에 쓰려면, load 쪽에서 **레시피↔패키지↔source 문서 연결**, **설치 패키지 필터**, **레시피명을 OSS Name으로 쓰기**가 더 필요하다. License Declared 폴백은 그중 라이선스 공란만 줄인다.

## 참고

- [create-spdx.md](./create-spdx.md) — Yocto SPDX 생성
- Hub `docs/project/load/spdx.md` — SPDX 2.2/2.3 Identification load
- `meta/classes/create-spdx-2.2.bbclass` — `licenseDeclared`, `{PN}-source-N` `downloadLocation`, CPE, `GENERATED_FROM`
- `src/fosslight_yocto/_package_item.py` — 라이선스 매핑, 버전 truncate, `pkg:yocto` PURL
- `src/fosslight_yocto/_write_result_file.py` — DEP / BIN / BIN (Yocto) 시트
