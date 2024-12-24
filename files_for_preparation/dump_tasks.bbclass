# Copyright (c) 2025 LG Electronics, Inc.
# SPDX-License-Identifier: Apache-2.0
#
# This class adds dumptasks to dump configure and build task procedure,
# Those files are only operated by -e option 

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

