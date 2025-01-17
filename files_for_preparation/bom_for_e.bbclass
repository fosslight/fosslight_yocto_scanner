# Copyright (c) 2020 LG Electronics, Inc.
# SPDX-License-Identifier: Apache-2.0
#
# This class adds write_bom_info and write_abi_xml_data,
# Each of them can be run by bitake --runall option.
# They are useful to verify build output specification.
 
do_write_bom_info[nostamp] = "1"
addtask write_bom_info
python do_write_bom_info() {
    import json
    import time
    # We want one recipe per line, starting with arch and recipe keys,
    # so that it's easy to sort and compare them
    class BomJSONEncoder(json.JSONEncoder):
        def iterencode(self, obj, _one_shot=True):
            if isinstance(obj, dict):
                output = []
                if "arch" in obj.keys() and "recipe" in obj.keys():
                    output.append(json.dumps("arch") + ": " + self.encode(obj["arch"]))
                    output.append(json.dumps("recipe") + ": " + self.encode(obj["recipe"]))
                for key, value in sorted(obj.items()):
                    if key == "arch" or key == "recipe":
                        continue
                    output.append(json.dumps(key) + ": " + self.encode(value))
                return "{" + ",".join(output) + "}"
            else:
                return json.JSONEncoder().iterencode(obj, _one_shot)
 

    jsondata = {}
    jsondata["src_path"] = d.getVar("S", True)
    jsondata["src_uri"] = d.getVar("SRC_URI", True)
    jsondata["srcrev"] = "".join(d.getVar("SRCREV", True).split())
    jsondata["recipe"] = d.getVar("PN", True)
    jsondata["file"] = d.getVar("FILE", True)[len(d.getVar("TOPDIR", True)):]
    jsondata["arch"] = d.getVar("PACKAGE_ARCH", True)
    jsondata["author"] = d.getVar("AUTHOR", True)
    license = d.getVar("LICENSE", True)
    license_flags = d.getVar("LICENSE_FLAGS", True)
    packages = d.getVar("PACKAGES", True)
    jsondata["license"] = license
    jsondata["license_flags"] = license_flags
    jsondata["complete"] = int(time.time())
    jsondata["packages"] = packages
    pkg_lic = {}
    if packages:
        for pkg in packages.split():
            lic = d.getVar("LICENSE_%s" % pkg, True)
            if lic and lic != license:
                pkg_lic[pkg] = lic
    jsondata["pkg_lic"] = pkg_lic
    jsondata["pe"] = d.getVar("PE", True)
    jsondata["pv"] = d.getVar("PV", True)
    jsondata["pr"] = d.getVar("PR", True)
    jsondata["pf"] = d.getVar("PF", True)
    jsondata["extendprauto"] = d.getVar("EXTENDPRAUTO", True)
    jsondata["extendpkgv"] = d.getVar("EXTENDPKGV", True)
    jsondata["description"] = d.getVar("DESCRIPTION", True)
    jsondata["summary"] = d.getVar("SUMMARY", True)
    jsondata["cve_check_whitelist "] = d.getVar("CVE_CHECK_WHITELIST", True)

    cpe_ids = get_cpe_ids(d.getVar("CVE_VENDOR",""), d.getVar("CVE_PRODUCT",""), d.getVar("CVE_VERSION",""), jsondata["recipe"], jsondata["pv"])
    jsondata["source_info"] = cpe_ids

    datafile = os.path.join(d.getVar("TOPDIR", True), "bom.json")
    lock = bb.utils.lockfile(datafile + '.lock')
    with open(datafile, "a") as f:
        json.dump(jsondata, f, sort_keys=True, cls=BomJSONEncoder)
        f.write(',\n')
    bb.utils.unlockfile(lock)
}


python do_dumptasks() {
    
    #Dump BitBake tasks to ${TOPDIR}/dumped_tasks/${PF}.task_name.
    
    import os
    import bb

    ar_outdir = os.path.join(d.getVar('TOPDIR', True), "dumped_tasks")  # 기본값 설정
    ar_dumptasks = ["do_configure", "do_compile"]  # 기본값 설정
    pf = d.getVar('PF', True)

    bb.utils.mkdirhier(ar_outdir)

    for task in ar_dumptasks:
        # Do not export tasks that are set to do not run
        if d.getVarFlag(task, 'noexec') == '1':
            bb.warn('%s: skipping task %s: [noexec]' % (pf, task))
            continue

        dumpfile = os.path.join(ar_outdir, '%s.%s' % (pf, task))
        bb.note('Dumping task %s into %s' % (task, dumpfile))

        # We assume the task as a shell script and then check if it is
        # actually a Python script.
        emit_func = bb.data.emit_func
        if d.getVarFlag(task, 'python') == '1':
            emit_func = bb.data.emit_func_python

        try:
            with open(dumpfile, 'w') as f:
                emit_func(task, f, d)
        except Exception as e:
            bb.fatal('%s: Cannot export %s: %s' % (pf, task, e))
}

# do_dumptasks 작업을 빌드 순서에 포함시키기
addtask do_dumptasks after do_configure before do_compile


def get_cpe_ids(cve_vendor, cve_product, cve_version, pn, pv):
    
    #Get list of CPE identifiers for the given product and version

    if cve_vendor is None:
        cve_vendor = ""
    if cve_product is None:
        cve_product = ""
    if cve_version is None:
        cve_version = ""

    version = cve_version.split("+git")[0]

    if cve_version.startswith("$"):
        version = pv

    cpe_ids = []
    for product in cve_product.split():
        # CVE_PRODUCT in recipes may include vendor information for CPE identifiers. If not,
        # use wildcard for vendor.
        if ":" in product:
            cve_vendor, product = product.split(":", 1)

        if product.startswith("$"):
            product = pn

        if cve_vendor is None:
            cve_vendor = ""

        cpe_id = f'cpe:2.3:a:{cve_vendor}:{product}:{version}:*:*:*:*:*:*:*'
        cpe_ids.append(cpe_id)

    return cpe_ids



