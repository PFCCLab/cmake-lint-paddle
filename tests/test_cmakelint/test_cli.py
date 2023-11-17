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
from pathlib import Path
from unittest import mock

import pytest

import cmakelint
from cmakelint.cli import _DEFAULT_FILENAME

from .utils import (
    nostderr,
)


def test_parse_args():
    old_cats = cmakelint.rules.ERROR_CATEGORIES
    try:
        cmakelint.rules.ERROR_CATEGORIES = ""
        with nostderr():
            pytest.raises(SystemExit, cmakelint.cli.parse_args, [])
            pytest.raises(SystemExit, cmakelint.cli.parse_args, ["--help"])
            pytest.raises(SystemExit, cmakelint.cli.parse_args, ["--bogus-option"])
            pytest.raises(SystemExit, cmakelint.cli.parse_args, ["--filter="])
            pytest.raises(SystemExit, cmakelint.cli.parse_args, ["--filter=foo"])
            pytest.raises(SystemExit, cmakelint.cli.parse_args, ["--filter=+x,b,-c", "foo.cmake"])
            pytest.raises(SystemExit, cmakelint.cli.parse_args, ["--spaces=c", "foo.cmake"])
            pytest.raises(SystemExit, cmakelint.cli.parse_args, ["--version"])
        cmakelint.state._lint_state.filters = []
        assert cmakelint.cli.parse_args(["--filter=-whitespace", "foo.cmake"]) == ["foo.cmake"]
        cmakelint.state._lint_state.filters = []
        assert cmakelint.cli.parse_args(["foo.cmake"]) == ["foo.cmake"]
        filt = "-,+whitespace"
        cmakelint.state._lint_state.filters = []

        assert cmakelint.cli.parse_args(["--config=None", "--spaces=3", "--filter=" + filt, "foo.cmake"]) == [
            "foo.cmake"
        ]
        assert cmakelint.state._lint_state.filters == ["-", "+whitespace"]
        assert cmakelint.state._lint_state.spaces == 3
        cmakelint.state._lint_state.filters = []
        filt = "-,+whitespace/eol, +whitespace/tabs"
        assert cmakelint.cli.parse_args(["--config=None", "--spaces=3", "--filter=" + filt, "foo.cmake"]) == [
            "foo.cmake"
        ]
        assert cmakelint.state._lint_state.filters == ["-", "+whitespace/eol", "+whitespace/tabs"]

        cmakelint.state._lint_state.filters = []
        cmakelint.cli.parse_args(["--config=./foo/bar", "foo.cmake"])
        assert cmakelint.state._lint_state.config == "./foo/bar"

        cmakelint.cli.parse_args(["--config=None", "foo.cmake"])
        assert cmakelint.state._lint_state.config is None
        cmakelint.state._lint_state.reset()

        cmakelint.cli.parse_args(["foo.cmake"])
        assert cmakelint.state._lint_state.config == str(Path("~").expanduser() / ".cmakelintrc")

        original_isfile = os.path.isfile

        def patched_isfile(filename, *args, **kwargs):
            if filename == _DEFAULT_FILENAME:
                return True
            return original_isfile(filename, *args, **kwargs)

        patcher = mock.patch("os.path.isfile", patched_isfile)
        with patcher:
            assert cmakelint.cli.parse_args([]) == ["CMakeLists.txt"]
            assert cmakelint.state._lint_state.config == str(Path("~").expanduser() / ".cmakelintrc")

    finally:
        cmakelint.rules.ERROR_CATEGORIES = old_cats
        cmakelint.state._lint_state.reset()


def test_parse_options_file():
    old_cats = cmakelint.rules.ERROR_CATEGORIES
    try:
        cmakelint.rules.ERROR_CATEGORIES = ""
        cmakelint.cli.parse_option_file(
            """
                # skip comment
                filter=-,+whitespace
                spaces= 3
                """.split("\n"),
            ignore_space=False,
        )
        assert cmakelint.state._lint_state.filters == ["-", "+whitespace"]
        cmakelint.cli.parse_args(["--filter=+syntax", "foo.cmake"])
        assert cmakelint.state._lint_state.filters == ["-", "+whitespace", "+syntax"]
        assert cmakelint.state._lint_state.spaces == 3

        cmakelint.state._lint_state.spaces = 2
        cmakelint.cli.parse_option_file(
            """
                # skip comment
                spaces= 4
                """.split("\n"),
            ignore_space=True,
        )
        assert cmakelint.state._lint_state.spaces == 2

        cmakelint.cli.parse_option_file(
            """
                # skip comment
                linelength= 90
                """.split("\n"),
            ignore_space=True,
        )
        assert cmakelint.state._lint_state.linelength == 90

        cmakelint.cli.parse_option_file(
            """
                # skip comment
                """.split("\n"),
            ignore_space=False,
        )
        assert cmakelint.state._lint_state.spaces == 2

        cmakelint.cli.parse_option_file(
            """
                quiet
                """.split("\n"),
            ignore_space=False,
        )
        assert cmakelint.state._lint_state.quiet

        cmakelint.state._lint_state.quiet = True
        cmakelint.cli.parse_option_file(
            """
                # quiet
                """.split("\n"),
            ignore_space=False,
        )
        assert cmakelint.state._lint_state.quiet
    finally:
        cmakelint.rules.ERROR_CATEGORIES = old_cats
        cmakelint.state._lint_state.reset()
