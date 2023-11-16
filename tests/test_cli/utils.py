"""
Copyright 2009 Richard Quirk
Copyright 2023 Nyakku Shigure, PaddlePaddle Authors

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License. You may obtain a copy of
the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.
"""


from __future__ import annotations

import os
import subprocess
import sys

from ..conftest import TEST_DIR

BASE_CMD = f"{sys.executable} -m cmakelint"


MAX_DIFF = None


def with_base_cmd(args: list[str]):
    return f"{BASE_CMD} {' '.join(args)}"


def run_shell_command(cmd, cwd="."):
    """
    executes a command
    :param cmd: A string to execute.
    :param cwd: from which folder to run.
    """

    stdout_target = subprocess.PIPE
    stderr_target = subprocess.PIPE

    proc = subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=stdout_target, stderr=stderr_target)
    out, err = proc.communicate()
    # print(err) # to get the output at time of test
    return (proc.returncode, out, err)


def check_all_in_folder(folder_name, expected_defs):
    count = 0
    for dirpath, _, fnames in os.walk(folder_name):
        for f in fnames:
            if f.endswith(".def"):
                count += 1
                _check_def(os.path.join(dirpath, f))
    assert count, expected_defs


def _check_def(path):
    """runs command and compares to expected output from def file"""
    # TODO: Use pytest snapshot library to fix the output
    # self.maxDiff = None # to see full diff
    with open(path, "rb") as filehandle:
        datalines = filehandle.readlines()
        stdoutLines = int(datalines[2])
        _run_and_check(
            rel_cwd=os.path.dirname(path),
            args=[datalines[0].decode("utf8").strip()],
            expected_status=int(datalines[1]),
            expected_out=[line.decode("utf8").strip() for line in datalines[3 : 3 + stdoutLines]],
            expected_err=[line.decode("utf8").strip() for line in datalines[3 + stdoutLines :]],
        )


def _run_and_check(rel_cwd, args, expected_status, expected_out, expected_err):
    cmd = with_base_cmd(args)
    cwd = str(TEST_DIR / rel_cwd)
    # command to reproduce
    print("\ncd " + cwd + " && " + cmd + " 2> <filename>")
    (status, out, err) = run_shell_command(cmd, cwd)
    try:
        assert status == expected_status, "bad command status %s" % status
        assert len(err.decode("utf8").split("\n")) == len(expected_err)
        assert err.decode("utf8").split("\n") == expected_err
        assert len(out.decode("utf8").split("\n")) == len(expected_out)
        assert out.decode("utf8").split("\n") == expected_out
    except AssertionError as e:
        e.args += (f"Failed check in {cwd} for command: {cmd}",)
        raise e
