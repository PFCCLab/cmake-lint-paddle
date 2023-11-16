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

from .utils import run_command


def test_blender_check(snapshot):
    assert run_command("samples/blender", ["src/CMakeLists.txt"]) == snapshot


def test_blender_nolinelen(snapshot):
    assert (
        run_command("samples/blender", ["--filter=-linelength,-readability/mixedcase", "src/CMakeLists.txt"])
        == snapshot
    )
