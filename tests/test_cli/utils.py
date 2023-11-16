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


def run_command(rel_cwd, args):
    cmd = with_base_cmd(args)
    cwd = str(TEST_DIR / rel_cwd)
    # command to reproduce
    print("\ncd " + cwd + " && " + cmd + " 2> <filename>")
    status, stdout, stderr = run_shell_command(cmd, cwd)
    return {
        "status": status,
        "stdout": stdout.decode("utf8").split("\n"),
        "stderr": stderr.decode("utf8").split("\n"),
    }
