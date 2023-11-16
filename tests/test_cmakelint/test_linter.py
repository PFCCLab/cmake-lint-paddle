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

from pathlib import Path
from unittest import mock

import pytest

import cmakelint.__main__
import cmakelint.__version__

from .utils import (
    do_test_check_file_name,
    do_test_check_find_package,
    do_test_check_repeat_logic,
    do_test_get_argument,
    do_test_lint,
    do_test_multi_line_lint,
    nostderr,
)


def test_line_length():
    do_test_lint("# " + ("o" * 80), "Lines should be <= 80 characters long")


def test_upper_and_lowerCase():
    do_test_multi_line_lint("""project()\nCMAKE_MINIMUM_REQUIRED()\n""", "Do not mix upper and lower case commands")


def test_contains_command():
    assert cmakelint.__main__.ContainsCommand("project()")
    assert cmakelint.__main__.ContainsCommand("project(")
    assert cmakelint.__main__.ContainsCommand("project  ( ")
    assert not cmakelint.__main__.ContainsCommand("VERSION")


def test_get_command():
    assert cmakelint.__main__.GetCommand("project()") == "project"
    assert cmakelint.__main__.GetCommand("project(") == "project"
    assert cmakelint.__main__.GetCommand("project  ( ") == "project"
    assert cmakelint.__main__.GetCommand("VERSION") == ""


def test_is_command_upper_case():
    assert cmakelint.__main__.IsCommandUpperCase("PROJECT")
    assert cmakelint.__main__.IsCommandUpperCase("CMAKE_MINIMUM_REQUIRED")
    assert not cmakelint.__main__.IsCommandUpperCase("cmake_minimum_required")
    assert not cmakelint.__main__.IsCommandUpperCase("project")
    assert not cmakelint.__main__.IsCommandUpperCase("PrOjEct")


def test_is_command_mixed_case():
    assert cmakelint.__main__.IsCommandMixedCase("PrOjEct")
    assert not cmakelint.__main__.IsCommandMixedCase("project")
    assert not cmakelint.__main__.IsCommandMixedCase("CMAKE_MINIMUM_REQUIRED")
    assert cmakelint.__main__.IsCommandMixedCase("CMAKE_MINIMUM_required")


def test_clean_comment():
    assert cmakelint.__main__.CleanComments("# Comment to zap") == ("", False)
    assert cmakelint.__main__.CleanComments("project() # Comment to zap") == ("project()", False)


def test_clean_comment_quotes():
    assert cmakelint.__main__.CleanComments('CHECK_C_SOURCE_COMPILES("') == ('CHECK_C_SOURCE_COMPILES("', True)
    assert cmakelint.__main__.CleanComments(" some line in a comment ", True) == ("", True)
    assert cmakelint.__main__.CleanComments(' end of comment") ', True) == ('")', False)


def test_command_spaces():
    do_test_multi_line_lint("""project ()""", "Extra spaces between 'project' and its ()")


def test_tabs():
    do_test_lint("\tfoo()", "Tab found; please use spaces")


def test_trailing_spaces():
    do_test_lint("# test ", "Line ends in whitespace")
    do_test_multi_line_lint("  foo() \n  foo()\n", "Line ends in whitespace")
    do_test_lint("    set(var value)", "")


def test_command_space_balance():
    do_test_multi_line_lint("""project( Foo)""", "Mismatching spaces inside () after command")
    do_test_multi_line_lint("""project(Foo )""", "Mismatching spaces inside () after command")


def test_command_not_ended():
    do_test_multi_line_lint(
        """project(
            Foo
            #
            #""",
        "Unable to find the end of this command",
    )


def test_repeat_logic_expression():
    do_test_check_repeat_logic("else(foo)", "Expression repeated inside else; " "better to use only else()")
    do_test_check_repeat_logic("ELSEIF(NOT ${VAR})", "")
    do_test_check_repeat_logic(
        "ENDMACRO( my_macro foo bar baz)", "Expression repeated inside endmacro; " "better to use only ENDMACRO()"
    )


def test_find_tool():
    do_test_check_file_name(
        "path/to/FindFooBar.cmake", "Find modules should use uppercase names; " "consider using FindFOOBAR.cmake"
    )
    do_test_check_file_name("CMakeLists.txt", "")
    do_test_check_file_name("cmakeLists.txt", "File should be called CMakeLists.txt")


def test_is_find_package():
    assert cmakelint.__main__.IsFindPackage("path/to/FindFOO.cmake")
    assert not cmakelint.__main__.IsFindPackage("path/to/FeatureFOO.cmake")


def test_check_find_package():
    do_test_check_find_package(
        "FindFoo.cmake",
        "",
        [
            "Package should include FindPackageHandleStandardArgs",
            "Package should use FIND_PACKAGE_HANDLE_STANDARD_ARGS",
        ],
    )
    do_test_check_find_package(
        "FindFoo.cmake",
        """INCLUDE(FindPackageHandleStandardArgs)""",
        "Package should use FIND_PACKAGE_HANDLE_STANDARD_ARGS",
    )
    do_test_check_find_package(
        "FindFoo.cmake",
        """FIND_PACKAGE_HANDLE_STANDARD_ARGS(FOO DEFAULT_MSG)""",
        "Package should include FindPackageHandleStandardArgs",
    )
    do_test_check_find_package(
        "FindFoo.cmake",
        """INCLUDE(FindPackageHandleStandardArgs)
            FIND_PACKAGE_HANDLE_STANDARD_ARGS(KK DEFAULT_MSG)""",
        "Weird variable passed to std args, should be FOO not KK",
    )
    do_test_check_find_package(
        "FindFoo.cmake",
        """INCLUDE(FindPackageHandleStandardArgs)
            FIND_PACKAGE_HANDLE_STANDARD_ARGS(FOO DEFAULT_MSG)""",
        "",
    )


def test_get_command_argument():
    do_test_get_argument(
        "KK",
        """SET(
            KK)""",
    )
    do_test_get_argument("KK", "Set(  KK)")
    do_test_get_argument("KK", "FIND_PACKAGE_HANDLE_STANDARD_ARGS(KK BLEUGH)")


def test_is_valid_file():
    assert cmakelint.__main__.IsValidFile("CMakeLists.txt")
    assert cmakelint.__main__.IsValidFile("cmakelists.txt")
    assert cmakelint.__main__.IsValidFile("/foo/bar/baz/CMakeLists.txt")
    assert cmakelint.__main__.IsValidFile("Findkk.cmake")
    assert not cmakelint.__main__.IsValidFile("foobar.h.in")


def test_filter_control():
    do_test_multi_line_lint(("# lint_cmake: -whitespace/eol\n" "  foo() \n" "  foo()\n"), "")


def test_bad_pragma():
    do_test_multi_line_lint(
        ("# lint_cmake: I am badly formed\n" "if(TRUE)\n" "endif()\n"), "Filter should start with - or +"
    )
    cmakelint.__main__._lint_state.reset()


def test_bad_pragma2():
    do_test_multi_line_lint(
        ("# lint_cmake: -unknown thing\n" "if(TRUE)\n" "endif()\n"), "Filter not allowed: -unknown thing"
    )
    cmakelint.__main__._lint_state.reset()


def test_whitespace_issue16():
    do_test_multi_line_lint(("if(${CONDITION})\n" "  set(VAR\n" "      foo\n" "      bar\n" "  )\n" "endif()\n"), "")


def test_whitespace_issue16_non_regression():
    do_test_multi_line_lint(("if(${CONDITION})\n" "  set(VAR\n" "      foo\n" "      bar)\n" "endif()\n"), "")


def test_whitespace_issue16_false_negative():
    do_test_multi_line_lint(
        ("if(${CONDITION})\n" "  set(VAR\n" "      foo\n" "      bar  )\n" "endif()\n"),
        "Mismatching spaces inside () after command",
    )


def test_no_end():
    do_test_multi_line_lint('file(APPEND ${OUT} "#endif${nl}")\n', "")


def test_backslash_comment():
    do_test_multi_line_lint(r'file(APPEND ${OUT} " \"") # comment\n', "")


def test_false_positive_source_compiles():
    do_test_multi_line_lint(
        (
            'CHECK_C_SOURCE_COMPILES("\n'
            "#include\n"
            "void foo(void) {}\n"
            "int main()\n"
            "{\n"
            "pthread_once_t once_control = PTHREAD_ONCE_INIT;\n"
            "pthread_once(&once_control, foo);\n"
            "return 0;\n"
            '}"\n'
            "HAVE_PTHREAD_ONCE_INIT\n"
            ")\n"
        ),
        "",
    )


def test_indent():
    try:
        cmakelint.__main__._lint_state.spaces = 2
        do_test_lint("no_indent(test)", "")
        do_test_lint("  two_indent(test)", "")
        do_test_lint("    four_indent(test)", "")
        do_test_lint(" one_indent(test)", "Weird indentation; use 2 spaces")
        do_test_lint("   three_indent(test)", "Weird indentation; use 2 spaces")

        cmakelint.__main__._lint_state.spaces = 3
        do_test_lint("no_indent(test)", "")
        do_test_lint("  two_indent(test)", "Weird indentation; use 3 spaces")
        do_test_lint("    four_indent(test)", "Weird indentation; use 3 spaces")
        do_test_lint(" one_indent(test)", "Weird indentation; use 3 spaces")
        do_test_lint("   three_indent(test)", "")
    finally:
        cmakelint.__main__._lint_state.reset()


def test_parse_args():
    old_usage = cmakelint.__main__._USAGE
    old_version = cmakelint.__version__.VERSION
    old_cats = cmakelint.__main__._ERROR_CATEGORIES
    old_spaces = cmakelint.__main__._lint_state.spaces
    try:
        cmakelint.__main__._USAGE = ""
        cmakelint.__main__._ERROR_CATEGORIES = ""
        cmakelint.__main__._VERSION = ""
        with nostderr():
            pytest.raises(SystemExit, cmakelint.__main__.ParseArgs, [])
            pytest.raises(SystemExit, cmakelint.__main__.ParseArgs, ["--help"])
            pytest.raises(SystemExit, cmakelint.__main__.ParseArgs, ["--bogus-option"])
            pytest.raises(SystemExit, cmakelint.__main__.ParseArgs, ["--filter="])
            pytest.raises(SystemExit, cmakelint.__main__.ParseArgs, ["--filter=foo"])
            pytest.raises(SystemExit, cmakelint.__main__.ParseArgs, ["--filter=+x,b,-c", "foo.cmake"])
            pytest.raises(SystemExit, cmakelint.__main__.ParseArgs, ["--spaces=c", "foo.cmake"])
            pytest.raises(SystemExit, cmakelint.__main__.ParseArgs, ["--version"])
        cmakelint.__main__._lint_state.filters = []
        assert cmakelint.__main__.ParseArgs(["--filter=-whitespace", "foo.cmake"]) == ["foo.cmake"]
        cmakelint.__main__._lint_state.filters = []
        assert cmakelint.__main__.ParseArgs(["foo.cmake"]) == ["foo.cmake"]
        filt = "-,+whitespace"
        cmakelint.__main__._lint_state.filters = []

        assert cmakelint.__main__.ParseArgs(["--config=None", "--spaces=3", "--filter=" + filt, "foo.cmake"]) == [
            "foo.cmake"
        ]
        assert cmakelint.__main__._lint_state.filters == ["-", "+whitespace"]
        assert cmakelint.__main__._lint_state.spaces == 3
        cmakelint.__main__._lint_state.filters = []
        filt = "-,+whitespace/eol, +whitespace/tabs"
        assert cmakelint.__main__.ParseArgs(["--config=None", "--spaces=3", "--filter=" + filt, "foo.cmake"]) == [
            "foo.cmake"
        ]
        assert cmakelint.__main__._lint_state.filters == ["-", "+whitespace/eol", "+whitespace/tabs"]

        cmakelint.__main__._lint_state.filters = []
        cmakelint.__main__.ParseArgs(["--config=./foo/bar", "foo.cmake"])
        assert cmakelint.__main__._lint_state.config == "./foo/bar"
        cmakelint.__main__.ParseArgs(["--config=None", "foo.cmake"])
        assert cmakelint.__main__._lint_state.config is None
        cmakelint.__main__.ParseArgs(["foo.cmake"])
        assert cmakelint.__main__._lint_state.config == str(Path("~").expanduser() / ".cmakelintrc")
        config = {"return_value": True}
        patcher = mock.patch("os.path.isfile", **config)
        try:
            patcher.start()
            assert cmakelint.__main__.ParseArgs([]) == ["CMakeLists.txt"]
            assert cmakelint.__main__._lint_state.config == str(Path("~").expanduser() / ".cmakelintrc")
        finally:
            patcher.stop()
    finally:
        cmakelint.__main__._USAGE = old_usage
        cmakelint.__main__._ERROR_CATEGORIES = old_cats
        cmakelint.__main__._VERSION = old_version
        cmakelint.__main__._lint_state.reset()


def testParseOptionsFile():
    old_usage = cmakelint.__main__._USAGE
    old_cats = cmakelint.__main__._ERROR_CATEGORIES
    try:
        cmakelint.__main__._USAGE = ""
        cmakelint.__main__._ERROR_CATEGORIES = ""
        cmakelint.__main__.ParseOptionFile(
            """
                # skip comment
                filter=-,+whitespace
                spaces= 3
                """.split("\n"),
            ignore_space=False,
        )
        assert cmakelint.__main__._lint_state.filters == ["-", "+whitespace"]
        cmakelint.__main__.ParseArgs(["--filter=+syntax", "foo.cmake"])
        assert cmakelint.__main__._lint_state.filters == ["-", "+whitespace", "+syntax"]
        assert cmakelint.__main__._lint_state.spaces == 3

        cmakelint.__main__._lint_state.spaces = 2
        cmakelint.__main__.ParseOptionFile(
            """
                # skip comment
                spaces= 4
                """.split("\n"),
            ignore_space=True,
        )
        assert cmakelint.__main__._lint_state.spaces == 2

        cmakelint.__main__.ParseOptionFile(
            """
                # skip comment
                linelength= 90
                """.split("\n"),
            ignore_space=True,
        )
        assert cmakelint.__main__._lint_state.linelength == 90

        cmakelint.__main__.ParseOptionFile(
            """
                # skip comment
                """.split("\n"),
            ignore_space=False,
        )
        assert cmakelint.__main__._lint_state.spaces == 2

        cmakelint.__main__.ParseOptionFile(
            """
                quiet
                """.split("\n"),
            ignore_space=False,
        )
        assert cmakelint.__main__._lint_state.quiet

        cmakelint.__main__._lint_state.quiet = True
        cmakelint.__main__.ParseOptionFile(
            """
                # quiet
                """.split("\n"),
            ignore_space=False,
        )
        assert cmakelint.__main__._lint_state.quiet
    finally:
        cmakelint.__main__._USAGE = old_usage
        cmakelint.__main__._ERROR_CATEGORIES = old_cats
        cmakelint.__main__._lint_state.reset()
