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

from cmakelint.error_code import ERROR_CODE_WRONG_USAGE

from .utils import run_shell_command, with_base_cmd


def test_help():
    (status, out, err) = run_shell_command(with_base_cmd(["--help"]))
    assert status == 0
    assert out.startswith(b"usage: cmakelint [-h] [-v] [--filter -X,+Y] [--config CONFIG]"), out
    assert err == b""


def test_wrong_usage():
    (status, out, err) = run_shell_command(with_base_cmd(["--unknown-option"]))
    assert status == ERROR_CODE_WRONG_USAGE
    assert out == b""
    assert err.startswith(b"usage: cmakelint [-h] [-v] [--filter -X,+Y] [--config CONFIG]"), err
