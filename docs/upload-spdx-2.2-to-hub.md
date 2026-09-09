<!--
SPDX-FileCopyrightText: Copyright 2026 LG Electronics Inc.
SPDX-License-Identifier: Apache-2.0
-->

# create-spdx 2.2 산출물을 FOSSLight Hub에 업로드하는 방안

Yocto `create-spdx`(SPDX 2.2)는 **문서 여러 장 + 참조**로 SBOM을 만든다. Hub는 SPDX 2.x를 **파일 하나**의 `packages[]`만 Identification에 넣는다. 이 문서는 생성 방식, Hub에 올리기 전에 필요한 정제, 그 정제를 **Hub가 할지 scanner가 할지**, 그리고 제외 대상을 **어떤 값으로 판별할지**를 정리한다.

Hub load 규칙: Hub `docs/project/load/spdx.md` (2.2/2.3 동일). SPDX 생성: [create-spdx.md](./create-spdx.md) (있는 경우).

## 1. create-spdx 2.2가 문서를 만드는 방식

이미지 디렉터리에는 `*.spdx.json`이 아니라 `*.spdx.tar.zst`가 나온다. 아카이브를 풀면 JSON이 여러 개다. `*rootfs*.spdx.json`은 합본이 아니라 **이미지 문서**다.

```text
레시피마다
  do_create_spdx
    recipe-<PN>.spdx.json     레시피 패키지 + {PN}-source-N (실제 downloadLocation)
    <pkg>.spdx.json           PACKAGES의 각 패키지. GENERATED_FROM → 레시피
  do_create_runtime_spdx
    runtime-<pkg>.spdx.json   RDEPENDS. packages[] 없음. RUNTIME_DEPENDENCY_OF

이미지 rootfs
  image_combine_spdx
    설치 패키지에 CONTAINS 부여
    참조된 JSON을 tar.zst로 묶음 + index.json
```

정보 위치:

| 정보 | 있는 문서 |
| ---- | --------- |
| 설치 패키지 목록 | 이미지 JSON의 `relationships` `CONTAINS` |
| 패키지 name / PV / `licenseDeclared` | `<pkg>.spdx.json` |
| homepage, CPE | `recipe-<PN>.spdx.json` |
| 다운로드 URL | 레시피 문서의 `{PN}-source-N` |
| 런타임 의존 | `runtime-<pkg>.spdx.json` |

이미지 JSON의 `packages[]`는 보통 이미지 자신(`core-image-minimal`) 하나다. 설치 OSS는 `DocumentRef-<pkg>:SPDXRef-Package-<pkg>`로 **다른 파일**을 가리킨다. 그 파일만 Hub에 올리면 Identification에는 이미지 1행만 들어간다.

## 2. Hub가 한 파일에서 읽는 것

Hub는 업로드한 SPDX의 한 문서만 본다. `externalDocumentRefs`를 따라가지 않는다.

| Hub 필드 | 읽는 SPDX 칸 | Yocto 2.2 원본 |
| -------- | ------------ | -------------- |
| OSS Name | `name` | 문서에 따라 이미지명 / 패키지명 / `{PN}-source-N` |
| Version | `versionInfo` | `PV` 원문 (`2.39+git` 등) |
| Download | `downloadLocation` | 패키지·레시피는 `NOASSERTION` |
| Homepage | `homepage` | 레시피 문서에만 있음 |
| License | `licenseConcluded`, 빈 값이면 `licenseDeclared` (스펙). 구현은 Concluded만일 수 있음 | Concluded는 항상 `NOASSERTION`. 실제 값은 Declared |
| Copyright | `copyrightText` | 보통 `NOASSERTION` |
| Package URL | `externalRefs` purl | CPE만 있음. purl 없음 |
| Depends On | `DEPENDS_ON`만 | `CONTAINS` / `GENERATED_FROM` / `RUNTIME_DEPENDENCY_OF`만 있음 |

빈 값(공란 / `NONE` / `NOASSERTION`)은 공란으로 load한다. `LICENSE=CLOSED` → SPDX `NONE` → 공란.

원본 tar를 그대로 올리는 경로로는 Identification이 비거나 잘못된 행이 된다. **설치 패키지만 한 SPDX 2.2 JSON으로 펼친 파일**이 필요하다.

## 3. 합본(flatten) 방안

`packages[]`를 이어 붙이면 안 된다. 레시피·source-N·이미지·native가 OSS 행이 된다.

권장 산출물: `core-image-minimal.spdx.json` 하나 (`spdxVersion: SPDX-2.2`).

1. `index.json`은 `{"documents":[{"filename","documentNamespace","sha1"}, ...]}` 형태다. 문서 ID는 `filename`에서 `.spdx.json`을 **통째로** 뺀 값이다. (`pathlib.Path.stem`은 `.json`만 제거해 `base-files.spdx`가 되므로 쓰면 안 된다.)
2. 이미지 문서의 `CONTAINS`만 설치 패키지로 본다. 이게 target이다. (`installed-package-names.txt`와 집합이 같아야 한다.)
3. 각 설치 패키지 문서를 한 `SPDXPackage`로 넣고, `GENERATED_FROM` 레시피와 `{PN}-source-N`에서 빈 칸을 채운다.
4. 패키지 JSON의 `files[]`는 합본에 넣지 않는다. (패키지 문서 `packages[]`는 보통 1개지만 `files[]`/`CONTAINS` 파일 관계는 Hub Identification에 불필요.)

| Hub 필드 | 합본에 넣을 값 |
| -------- | -------------- |
| name | 레시피 PN (`libc6` → `glibc`). Hub OSS 매칭 |
| versionInfo | 패키지 `versionInfo` (`PV` 원문). fosslight Excel처럼 `+`/`-`/`~` truncate는 **선택** |
| downloadLocation | `{PN}-source-1`의 `downloadLocation`. **`file://` SRC_URI는 source-N이 안 만들어져 비므로**, scanner와 맞추려면 bom/`SRC_URI` 폴백이 필요하다 |
| homepage | 레시피 `homepage` (fosslight Excel은 기본 공란) |
| licenseConcluded · licenseDeclared | 패키지 `licenseDeclared`(PKG 단위). `DocumentRef-...:LicenseRef-...`는 레시피 문서의 `hasExtractedLicensingInfos`를 합본으로 옮긴 뒤 `LicenseRef-`로 푼다. **주의:** fosslight Excel은 레시피 `LICENSE`를 쓰므로 `libblkid1`처럼 PKG 라이선스가 더 좁으면 값이 달라진다. Excel과 동일하게 가려면 레시피 `licenseDeclared`를 쓴다 |
| externalRefs purl | 없으면 `pkg:yocto/{BPN}@{PV}` (`PV`의 `+`는 `%2B`) |
| relationships | runtime `RUNTIME_DEPENDENCY_OF`를 설치 패키지 간 `DEPENDS_ON`으로 변환 |

같은 레시피의 `busybox` / `busybox-syslog`는 **행을 나누고** name만 레시피로 맞춘다. 한 행으로 합치면 라이선스·파일이 섞인다.

## 4. 넣지 말 것 — 판별에 쓰는 값

시작점을 이미지 `CONTAINS`로 두면 native·source-N·레시피 문서는 설치 집합에 안 들어온다. 그래도 tar 전체를 순회하거나 Hub가 zip을 받을 때는 아래 값으로 걸러야 한다.

### 4.1 이미지 패키지

이미지 자신(`core-image-minimal`)은 OSS가 아니다.

| 볼 곳 | 판별 |
| ----- | ---- |
| 파일명 | `*rootfs*.spdx.json` 또는 `<IMAGE_NAME>-<MACHINE>.spdx.json` |
| `document.name` | `<IMAGE>-<MACHINE>.rootfs-<timestamp>` 형태 |
| `packages[].SPDXID` | `SPDXRef-Image-` 접두 |
| `packages[].name` | 이미지 레시피 PN (`core-image-minimal`) |
| `relationships` | 이 패키지가 `CONTAINS`의 `spdxElementId` (from) |

이미지 문서의 `CONTAINS` **대상**은 설치 패키지이므로 유지하고, from 쪽 이미지 패키지만 합본 `packages[]`에서 뺀다.

### 4.2 `{PN}-source-N` (다운로드 패키지)

소스 tarball/git을 가리키는 가상 패키지다. OSS 행으로 넣지 않고, 부모 레시피의 Download location으로만 쓴다.

| 볼 곳 | 판별 |
| ----- | ---- |
| `packages[].name` | 정규식 `^.+-source-[0-9]+$` (예: `busybox-source-1`, `glibc-source-1`) |
| 위치 | `recipe-<PN>.spdx.json`의 `packages[]` (레시피 본문과 같이 있음) |
| `versionInfo` | 대체로 없음 |
| `licenseDeclared` / `licenseConcluded` | 보통 `NOASSERTION` |
| `downloadLocation` | 실제 URI (`https://...` 또는 `git+https://...@rev`) |
| `relationships` | 이 패키지 → 레시피 `BUILD_DEPENDENCY_OF` |
| `SPDXID` | 다운로드용 ID (구현에 따라 `SPDXRef-Download-...`) |

`file://` SRC_URI는 source 패키지 자체가 안 만들어진다.

### 4.3 native / cross

호스트 도구다. rootfs target에 안 들어간다. 이미지 `CONTAINS`만 따라가면 이미 빠진다. tar 전체에서 레시피 문서를 건드릴 때만 아래가 필요하다.

| 볼 곳 | 판별 |
| ----- | ---- |
| 레시피 `packages[].annotations[].comment` | `isNative` (`native` 또는 `cross` 클래스일 때 create-spdx가 넣음) |
| 레시피 / 문서 이름 `PN` | 접미사 `-native`, `-cross`, `-crosssdk`, `-cross-canadian-<arch>`, `-initial`, `-intermediate` |
| `PN` 접두 | `nativesdk-` |
| 이미지 `CONTAINS` | 없으면 설치 대상이 아님 (가장 안전한 필터) |

패키지 JSON만 보면 annotation이 없을 수 있다. 그때는 `GENERATED_FROM`으로 레시피 문서를 열고 `isNative` / PN을 본다.

### 4.4 `packagegroup-*`

메타 패키지다. 이미지에는 설치되지만 소스 OSS가 아니다.

| 볼 곳 | 판별 |
| ----- | ---- |
| `packages[].name` (설치 패키지 문서) | `packagegroup-` 접두 (예: `packagegroup-core-boot`) |
| 이미지 `CONTAINS` | 포함됨. target 목록에는 있다 |

처리: 합본에서 **빼거나**, 넣고 Exclude/Comment로 `packagegroup`임을 남긴다. `fosslight_yocto`는 행을 남기고 Exclude한다. Hub SPDX에는 Exclude 컬럼이 없으므로, SPDX로 올릴 때는 **행을 빼는 쪽**이 맞다. Excel(DEP)로 올리면 Exclude를 쓸 수 있다.

### 4.5 runtime 문서

의존 관계만 있는 문서다. 패키지 행이 없다. 의존이 없으면 `AMENDS`만 있고 `RUNTIME_DEPENDENCY_OF`가 없다(이 빌드에서 runtime 문서 35개 중 의존 관계 10건).

| 볼 곳 | 판별 |
| ----- | ---- |
| 파일명 / `document.name` | `runtime-<pkg>` |
| `packages[]` | 없거나 비어 있음 |
| `relationships[].relationshipType` | `AMENDS`, (있을 때) `RUNTIME_DEPENDENCY_OF` |
| `externalDocumentRefs[].externalDocumentId` | 피의존: `DocumentRef-package-<pkg>`. 의존 대상: **`DocumentRef-runtime-dependency-<dep>`** (패키지 문서를 가리키지만 ID 접두가 `runtime-dependency-`) |
| 이미지 JSON의 `OTHER` | comment `Runtime dependencies for <pkg>` → `DocumentRef-runtime-<pkg>` |

합본 `packages[]`에 넣지 않는다. `RUNTIME_DEPENDENCY_OF`만 읽어 `DEPENDS_ON`으로 바꾼다.

- 의미: `spdxElementId`(의존 패키지) `RUNTIME_DEPENDENCY_OF` `relatedSpdxElement`(피의존 패키지) → 합본에서는 피의존 `DEPENDS_ON` 의존.
- 패키지명 추출: `DocumentRef-…:SPDXRef-Package-<name>`의 `<name>`을 쓴다. (`DocumentRef-runtime-dependency-kmod` → `kmod`)
- Hub는 `DEPENDS_ON`만 load한다. fosslight Excel `Depends On`은 비어 있으므로, Excel과 맞출 거면 합본에서도 관계를 생략해도 된다.

### 4.6 필터 순서 (권장)

```text
1. index.json 로드
2. *rootfs*.spdx.json 식별 (4.1)
3. CONTAINS 대상 DocumentRef → 설치 패키지 집합 (target)
4. 그 집합에서 name이 packagegroup-* 이면 제외 또는 Exclude (4.4)
5. runtime-* 문서는 패키지로 쓰지 않고 관계만 사용 (4.5)
6. recipe-* 의 *-source-N 은 downloadLocation만 사용 (4.2)
7. isNative / -native 레시피는 설치 집합 밖이면 무시 (4.3)
```

## 5. 보완 작업을 어디서 할지

Yocto 문서 그래프를 해석하는 일은 **scanner(또는 전용 flatten 도구)**, SPDX 일반 규칙만 **Hub**.

| 작업 | 담당 | 이유 |
| ---- | ---- | ---- |
| tar.zst / 여러 JSON을 한 문서로 펼치기 | **scanner** | Hub는 단일 SPDX만 받음. zip+DocumentRef 추적은 Yocto 전용 |
| 설치 패키지만 고르기 (이미지 `CONTAINS`) | **scanner** | 이미지/`CONTAINS`는 create-spdx 관례 |
| 이미지 · source-N · native · runtime 문서 제외 | **scanner** | 위 4장의 판별 값이 Yocto 전용 |
| `packagegroup-*` 제외 또는 Exclude | **scanner** | Hub SPDX에 Exclude 없음 |
| 레시피에서 homepage, source-N에서 download 채우기 | **scanner** | 파일 밖 필드 |
| `DocumentRef-...:LicenseRef-...` 풀기 | **scanner** | Extracted License가 레시피 문서에 있음 |
| `licenseConcluded`에 declared 복사 | **scanner** (합본 시) | 원본 concluded는 항상 `NOASSERTION`. 합본을 Hub가 바로 읽게 하려면 칸을 맞춰야 함 |
| 공란 / `NONE` / `NOASSERTION` → 공란 | **Hub** | 모든 SPDX 공통 |
| Concluded가 빈 값이면 Declared | **Hub** | 일반 SPDX에도 필요. 합본이 concluded를 채워도 이중으로 안전 |
| OSS Name을 레시피 PN으로 | **scanner** | Identification 정책. 일반 SPDX `name`을 Hub가 바꾸면 안 됨 |
| `pkg:yocto/...` PURL | **scanner** | Yocto purl. 원본에 없음 |
| `RUNTIME_DEPENDENCY_OF` → `DEPENDS_ON` + PURL | **scanner** | Hub는 `DEPENDS_ON`만 load |
| `CLOSED`/`NONE` → `other proprietary license` | **scanner** (FOSSLight 관례를 유지할 때) | SPDX `NONE`을 Hub가 proprietary로 바꾸면 다른 SBOM과 충돌 |
| PV truncate (`2.39+git` → `2.39`) | **scanner** (선택) | Hub는 SPDX 원문을 유지하는 편이 맞음 |
| `file://` SRC_URI download 폴백 | **scanner** | create-spdx는 source-N을 안 만듦. Excel과 맞출 때 bom/`SRC_URI` 필요 |
| 라이선스를 레시피 `LICENSE`로 통일 | **scanner** (선택) | 기본 flatten은 PKG `licenseDeclared`(더 좁을 수 있음) |
| CPE | 합본에 넣어도 됨. Hub는 아직 Identification에 안 씀 | — |

**결론:** Hub는 빈 값 처리와 License Concluded→Declared 폴백만 맡긴다. create-spdx 2.2를 올리려면 **scanner가 flatten한 단일 SPDX(또는 기존 Excel DEP)** 를 올린다. 그래프 해석을 Hub에 넣으면 Hub가 Yocto 전용 파서가 된다.

기존 `fosslight_yocto` Excel은 이미 설치 목록 + 레시피명 + 라이선스 별칭 + `pkg:yocto` PURL + packagegroup Exclude를 한다. SPDX 경로를 쓰려면 같은 정책을 flatten SPDX에 맞추면 된다.

## 6. 실측 비교 (core-image-minimal, SPDX 2.2)

대상 (동일 Scarthgap 빌드):

| 산출물 | 경로 |
| ------ | ---- |
| create-spdx 2.2 풀린 트리 | `/home/soim/yocto/tmp` (`*.spdx.json` + `index.json`, 원본 `*.spdx.tar.zst` 해제) |
| 이미지 문서 | `core-image-minimal-qemux86-64.rootfs-20260904022846.spdx.json` |
| fosslight_yocto 보고서 | `/home/soim/yocto/poky/build/fosslight_report_yocto_20260909_110447.xlsx` (DEP 35행) |
| 설치 목록 | `buildhistory/.../core-image-minimal/installed-package-names.txt` (35행) |

합본은 이 문서 3·4장 규칙으로 로컬에서 생성해 Excel과 대조했다. (문서 ID 매핑은 `.spdx.json` 접미사 제거.)

### 6.1 Target 패키지가 모두 나오는지

이미지 JSON (`spdxVersion: SPDX-2.2`):

- `packages[]`: **1개** (`core-image-minimal` 1.0) — 이미지 자신
- `CONTAINS`: **35개** — rootfs **target 설치 패키지**
- `OTHER`: 35개 — 각 패키지 runtime 문서

집합 일치 (실측):

```text
이미지 CONTAINS  35
installed-package-names.txt  35
fosslight_yocto DEP 행  35
문서 규칙 flatten packages[]  35

CONTAINS − ipn = ∅
ipn − CONTAINS = ∅
CONTAINS ⊆ Excel(레시피 매핑 + Comment의 Installed Package Name) = 전부 매칭
```

`CONTAINS` 목록:

```text
base-files
base-passwd
busybox
busybox-hwclock
busybox-syslog
busybox-udhcpc
eudev
init-ifupdown
init-system-helpers-service
initscripts
initscripts-functions
kernel-6.6.147-yocto-standard
kernel-image-6.6.147-yocto-standard
kernel-image-bzimage-6.6.147-yocto-standard
kernel-module-uvesafb-6.6.147-yocto-standard
kmod
ldconfig
libblkid1
libc6
libcrypto3
libkmod2
liblzma5
libz1
modutils-initscripts
netbase
openssl-conf
openssl-ossl-module-legacy
packagegroup-core-boot
sysvinit
sysvinit-inittab
sysvinit-pidof
ttyrun
update-alternatives-opkg
update-rc.d
v86d
```

| 경로 | target 35개가 Identification에 들어가는가 |
| ---- | ---------------------------------------- |
| 이미지 JSON만 Hub에 업로드 | **아니오.** OSS 1행 = `core-image-minimal` |
| tar 안 JSON을 각각 업로드 | 설치·레시피·source-N·files가 섞임. **target만 안 골라짐** |
| `fosslight_yocto` (`-i installed-package-names.txt`) | **예.** 35행 전부. `packagegroup-core-boot`는 Exclude |
| 이 문서의 flatten 합본 | **예.** `CONTAINS` 35. Hub SPDX면 `packagegroup-*`는 행 삭제 권장(4.4) |

레시피 매핑 예: `libc6`/`ldconfig` → `glibc`, `libblkid1` → `util-linux`, kernel-* → `linux-yocto`, `update-alternatives-opkg` → `opkg-utils`. 패키지명 ≠ 레시피명인 행은 Excel Comment에 `Installed Package Name:`이 남는 경우가 많다(전부는 아님).

### 6.2 flatten 합본 vs fosslight Excel — 필드

같은 설치 패키지 35개를 레시피명으로 짝지은 뒤 비교.

| 항목 | create-spdx → flatten (이 문서 3장) | fosslight_yocto DEP | 실측 |
| ---- | ----------------------------------- | ------------------- | ---- |
| 행 수 / target 커버 | 35 / 전부 | 35 / 전부 | **일치** |
| OSS Name | 레시피 PN | 레시피 PN | **일치** |
| Version | `PV` 원문 (`2.39+git`, `6.6.147+git`) | `+`/`-`/`~` truncate (`2.39`, `6.6.147`) | 7행 상이 (의도적 정책) |
| License | 패키지 `licenseDeclared` (대문자, `AND`, `LicenseRef-…`) | 레시피 `LICENSE` (소문자, 쉼표) | 형식 전부. **내용**은 PKG vs 레시피 차로 `libblkid1`/`libkmod2`/`liblzma5` 등 상이 |
| Download | source-N URI (`git+https://…@rev` 등) | `SRC_URI` 첫 항목 (`git://…;branch=…`) | URI 스킴/쿼리 형식 다름. **`file://` 6행**은 SPDX에 source-N 없음 → flatten 공란 / Excel `file://…` |
| Homepage | 레시피 homepage (다수 채움) | 기본 공란 | flatten에만 값 (31행) |
| Package URL | `pkg:yocto/{BPN}@{PV}` | 동일 형식 (`+` → `%2B`) | **일치** (짝 맞춘 뒤) |
| Depends On | runtime 10건 → `DEPENDS_ON` 가능 | 항상 공란 | Excel 맞추면 생략 |
| packagegroup | 행 유지 또는 삭제 | 행 유지 + Exclude | 정책만 다름 |
| Copyright | `NOASSERTION` → Hub 공란 | 공란 | 일치 |

라이선스 예시:

| 설치 패키지 | flatten (PKG declared) | Excel (레시피 LICENSE) |
| ----------- | ---------------------- | ---------------------- |
| `busybox*` | `GPL-2.0-only AND LicenseRef-bzip2-1.0.4` | `bzip2-1.0.4,gpl-2.0-only` |
| `libblkid1` | `LGPL-2.1-or-later` | util-linux 전체 (`bsd-2-clause,…,gpl-2.0-or-later`) |
| `libkmod2` | `LGPL-2.1-or-later` | `lgpl-2.1-or-later,gpl-2.0-or-later` |

`file://` 로 download가 비는 패키지(이 빌드): `base-files`, `init-ifupdown`, `initscripts`, `initscripts-functions`, `modutils-initscripts`, `sysvinit-inittab`.

### 6.3 요약

- **Target 누락 없음:** `CONTAINS` = `installed-package-names.txt` = fosslight DEP = flatten **각 35**.
- 이미지 JSON만으로는 추출 실패(1행). flatten 또는 Excel이 필요.
- 필드까지 Hub/Excel과 같게 하려면: (1) 버전 truncate 여부, (2) PKG vs 레시피 라이선스, (3) `file://` download 폴백, (4) homepage 채움 여부, (5) packagegroup 삭제 vs Exclude, (6) `DEPENDS_ON` 포함 여부를 정책으로 고정한다.
- Hub에 SPDX로 올릴 때는 flatten 단일 JSON. Excel DEP를 올리면 기존 scanner 경로 그대로다.

### 6.4 로컬 대조 스크립트

```bash
SPDX_DIR=/home/soim/yocto/tmp
IPN=/home/soim/yocto/poky/build/buildhistory/images/qemux86_64/glibc/core-image-minimal/installed-package-names.txt
IMG=$SPDX_DIR/core-image-minimal-qemux86-64.rootfs-20260904022846.spdx.json

# 1) CONTAINS
python3 -c '
import json,sys
d=json.load(open(sys.argv[1]))
for r in d.get("relationships") or []:
    if r.get("relationshipType")=="CONTAINS":
        print(r["relatedSpdxElement"].split(":")[0].replace("DocumentRef-","",1))
' "$IMG" | sort > /tmp/spdx-contains.txt

# 2) installed-package-names
sort "$IPN" > /tmp/ipn.txt
comm -3 /tmp/spdx-contains.txt /tmp/ipn.txt   # 비어 있어야 함

# 3) Excel DEP: 행 수 35, packagegroup Exclude, libc6 → OSS Name glibc
#    Comment의 Installed Package Name + OSS Name(레시피)으로 CONTAINS와 짝지음
```

대조 체크리스트:

1. CONTAINS 35 = ipn 35 = Excel 35
2. Excel에만 / SPDX에만 있는 설치 패키지명 없음
3. `packagegroup-core-boot` Excel Exclude (또는 flatten에서 삭제)
4. `libc6` → OSS Name `glibc`, `libblkid1` → `util-linux`
5. (선택) PKG 라이선스 vs 레시피 라이선스, `file://` download, 버전 truncate 정책 확인

## 7. 권장 작업 순서

1. Hub: 빈 값(공란/`NONE`/`NOASSERTION`) + Concluded 빈 값이면 Declared — 일반 SPDX.
2. scanner: tar.zst → 설치 패키지 flatten SPDX 2.2 (4장 필터 + 3장 필드) 또는 기존 Excel 유지.
3. flatten SPDX를 Hub에 올려 Identification이 35개(또는 packagegroup 제외 34개)인지 확인.
