<!--
SPDX-FileCopyrightText: Copyright 2026 LG Electronics Inc.
SPDX-License-Identifier: Apache-2.0
-->

# Yocto `create-spdx`로 SPDX 출력하기

Yocto Project / OpenEmbedded는 이미지 빌드 시 SPDX SBOM을 생성할 수 있다. 이 문서는 `create-spdx` 클래스를 켜고, 버전별로 SPDX 2.2 또는 3.0 결과를 어디에 어떤 형태로 받는지 정리한다.

참조. 공식 설명: [Yocto Project — Creating a Software Bill of Materials](https://docs.yoctoproject.org/dev-manual/sbom.html)

## 1. Yocto 버전과 SPDX 버전

`create-spdx`는 “지금 지원하는 최신 SPDX”를 가리키는 별칭이다. 실제 스펙 버전은 Yocto 릴리스에 따라 바뀐다. Yocto는 SPDX **2.3을 기본 출력으로 쓰지 않았고**, 2.2에서 3.0으로 바로 넘어갔다.

| Yocto                            | 기본`create-spdx`                       | SPDX 2.2                        | SPDX 3.0                     |
| -------------------------------- | ----------------------------------------- | ------------------------------- | ---------------------------- |
| Honister (3.4) ~ 5.0 이전        | 2.2 (`INHERIT += "create-spdx"` 필요)   | 기본                            | 없음                         |
| Scarthgap (5.0, LTS)             | **2.2** (`INHERIT_DISTRO`에 포함) | 기본                            | `create-spdx-3.0`으로 전환 |
| Styhead (5.1) ~ Whinlatter (5.3) | **3.0**                             | `create-spdx-2.2`로 전환      | 기본                         |
| Wrynose (6.0, LTS) 이후          | **3.0만**                           | 불가 (`create-spdx-2.2` 삭제) | 기본                         |

활성 버전 확인:

```bash
bitbake -e core-image-minimal | grep '^SPDX_VERSION='
```

- SPDX 2.2: `SPDX_VERSION="2.2"`
- SPDX 3.0: `SPDX_VERSION="3.0.1"` (릴리스에 따라 `3.0`)

## 2. `create-spdx` 켜기

Scarthgap(5.0)부터는 `meta/conf/distro/defaultsetup.conf`의 `INHERIT_DISTRO`에 `create-spdx`가 들어 있어, Poky 기본 설정이면 이미지 빌드만 해도 SPDX가 나온다.

없거나 끈 상태라면 `conf/local.conf`에 추가한다.

```bitbake
INHERIT += "create-spdx"
```

이미 `INHERIT_DISTRO`에 있으면 한 번 더 넣어도 동작은 같지만, 중복 상속이 되므로 기본값이 있는지 먼저 확인한다.

```bash
bitbake -e core-image-minimal | grep '^INHERIT_DISTRO='
```

비활성화:

```bitbake
INHERIT_DISTRO:remove = "create-spdx"
```

## 3. SPDX 2.2를 뽑고 싶을 때

### Scarthgap (5.0)

기본이 2.2이므로 추가 설정 없이 이미지 빌드하면 된다.

### Styhead (5.1) ~ Whinlatter (5.3)

기본이 3.0이므로 클래스를 바꾼다.

```bitbake
INHERIT:remove = "create-spdx"
INHERIT += "create-spdx-2.2"
```

`INHERIT_DISTRO`로 들어간 값을 빼려면 아래가 더 확실하다.

```bitbake
INHERIT_DISTRO:remove = "create-spdx"
INHERIT += "create-spdx-2.2"
```

### Wrynose (6.0) 이후

`create-spdx-2.2` 클래스가 삭제되었다. 빌드 시스템에서 SPDX 2.2를 다시 켤 수 없다. SPDX 3.0만 생성된다.

## 4. 자주 쓰는 옵션

`conf/local.conf`에 둔다. 값이 `1`이면 활성화.

| 변수                            | 설명                                                                     |
| ------------------------------- | ------------------------------------------------------------------------ |
| `SPDX_PRETTY = "1"`           | JSON을 들여 쓰기 해서 사람이 읽기 쉽게 만든다. 비교·디버깅에 유용하다.  |
| `SPDX_INCLUDE_SOURCES = "1"`  | 호스트 도구/타깃 패키지 생성에 쓴 소스 파일 정보를 SPDX에 넣는다.        |
| `SPDX_ARCHIVE_SOURCES = "1"`  | 해당 소스 아카이브(`.tar.zst`)를 함께 배포한다. 소스 제공 의무 대응용. |
| `SPDX_ARCHIVE_PACKAGED = "1"` | 타깃 패키지에 들어간 파일 아카이브를 함께 배포한다. (SPDX 2.2)           |
| `SPDX_CUSTOM_ANNOTATION_VARS` | 레시피에 커스텀 주석을 붙일 BitBake 변수 목록.                           |

비교만 할 때는 `SPDX_PRETTY = "1"`만 켜도 충분하다. 소스/패키지 아카이브는 산출물이 매우 커진다.

## 5. 빌드

일반적인 이미지 빌드와 같다. SPDX 태스크는 패키징·rootfs 뒤에 붙으므로 별도 타깃을 지정할 필요는 없다.

```bash
source oe-init-build-env
bitbake core-image-minimal
```

`<image>`를 실제 이미지 레시피 이름으로 바꾼다.

## 6. 산출물 위치와 형식

`MACHINE` 예: `qemux86-64`. 빌드 디렉터리는 `${TOPDIR}` (보통 `poky/build`).

### SPDX 2.2

패키지/레시피마다 SPDX JSON이 나뉘고, 이미지 시점에 묶어 `tar.zst`로 배포한다.

| 파일                  | 위치                                                           |
| --------------------- | -------------------------------------------------------------- |
| 이미지 SPDX 아카이브  | `tmp/deploy/images/<MACHINE>/<IMAGE>-<MACHINE>.spdx.tar.zst` |
| 심볼릭 링크           | 같은 디렉터리의`<IMAGE_LINK_NAME>.spdx.tar.zst`              |
| 레시피·패키지별 JSON | `tmp/deploy/spdx/2.2/` 및 아카이브 내부                      |

아카이브 안 구조:

```text
index.json                          # 문서 목록 (filename, documentNamespace, sha1)
<image-name>.spdx.json              # 이미지 문서. CONTAINS로 설치 패키지를 가리킴
recipe-<pn>.spdx.json               # 레시피 문서
<package>.spdx.json                 # 패키지 문서
runtime-<package>.spdx.json         # 런타임 의존성
```

압축 풀기:

```bash
zstd -d -c tmp/deploy/images/qemux86-64/core-image-minimal-qemux86-64.spdx.tar.zst \
  | tar -tf - | head

mkdir -p spdx-2.2 && cd spdx-2.2
zstd -d -c ../tmp/deploy/images/qemux86-64/core-image-minimal-qemux86-64.spdx.tar.zst \
  | tar -xf -
```

이미지 JSON의 `packages`, `relationships`, `externalDocumentRefs`와 `index.json`을 보면 설치 패키지와 레시피 매핑을 따라갈 수 있다. `spdxVersion`은 `SPDX-2.2`이다.

### SPDX 3.0

한 장의 JSON-LD 문서로 합쳐진다. `index.json`이나 per-package tarball이 없다.

| 파일        | 위치                                                                                                            |
| ----------- | --------------------------------------------------------------------------------------------------------------- |
| 이미지 SPDX | `tmp/deploy/images/<MACHINE>/<IMAGE>-<MACHINE>.rootfs.spdx.json` (이름 접미사는 릴리스에 따라 `.spdx.json`) |
| 레시피 SBOM | 이미지 SPDX에 포함. 레시피만 뽑을 때는`bitbake <recipe> -c create_recipe_sbom` (6.0 문서 기준)                |

파일 크기가 크다. `core-image-minimal`만 해도 비압축 JSON-LD가 수백 MB가 될 수 있다.

## 7. 체크리스트

- [ ] `SPDX_VERSION`이 기대한 값(2.2 또는 3.0.1)인가
- [ ] `INHERIT`에 `create-spdx` 또는 `create-spdx-2.2` / `create-spdx-3.0`이 있는가
- [ ] `tmp/deploy/images/<MACHINE>/`에 `.spdx.tar.zst`(2.2) 또는 `.spdx.json`(3.0)이 있는가
