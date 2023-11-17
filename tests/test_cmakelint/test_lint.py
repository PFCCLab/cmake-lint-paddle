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

import cmakelint

from .utils import (
    do_test_check_file_name,
    do_test_check_find_package,
    do_test_check_repeat_logic,
    do_test_get_argument,
    do_test_lint,
    do_test_multi_line_lint,
)


def test_line_length():
    do_test_lint("# " + ("o" * 80), "Lines should be <= 80 characters long")


def test_upper_and_lowerCase():
    do_test_multi_line_lint("""project()\nCMAKE_MINIMUM_REQUIRED()\n""", "Do not mix upper and lower case commands")


def test_contains_command():
    assert cmakelint.lint.contains_command("project()")
    assert cmakelint.lint.contains_command("project(")
    assert cmakelint.lint.contains_command("project  ( ")
    assert not cmakelint.lint.contains_command("VERSION")


def test_get_command():
    assert cmakelint.lint.get_command("project()") == "project"
    assert cmakelint.lint.get_command("project(") == "project"
    assert cmakelint.lint.get_command("project  ( ") == "project"
    assert cmakelint.lint.get_command("VERSION") == ""


def test_is_command_upper_case():
    assert cmakelint.lint.is_command_upper_case("PROJECT")
    assert cmakelint.lint.is_command_upper_case("CMAKE_MINIMUM_REQUIRED")
    assert not cmakelint.lint.is_command_upper_case("cmake_minimum_required")
    assert not cmakelint.lint.is_command_upper_case("project")
    assert not cmakelint.lint.is_command_upper_case("PrOjEct")


def test_is_command_mixed_case():
    assert cmakelint.lint.is_command_mixed_case("PrOjEct")
    assert not cmakelint.lint.is_command_mixed_case("project")
    assert not cmakelint.lint.is_command_mixed_case("CMAKE_MINIMUM_REQUIRED")
    assert cmakelint.lint.is_command_mixed_case("CMAKE_MINIMUM_required")


def test_clean_comment():
    assert cmakelint.lint.clean_comments("# Comment to zap") == ("", False)
    assert cmakelint.lint.clean_comments("project() # Comment to zap") == ("project()", False)


def test_clean_comment_quotes():
    assert cmakelint.lint.clean_comments('CHECK_C_SOURCE_COMPILES("') == ('CHECK_C_SOURCE_COMPILES("', True)
    assert cmakelint.lint.clean_comments(" some line in a comment ", True) == ("", True)
    assert cmakelint.lint.clean_comments(' end of comment") ', True) == ('")', False)


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
    assert cmakelint.state.is_find_package("path/to/FindFOO.cmake")
    assert not cmakelint.state.is_find_package("path/to/FeatureFOO.cmake")


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
    assert cmakelint.lint.is_valid_file("CMakeLists.txt")
    assert cmakelint.lint.is_valid_file("cmakelists.txt")
    assert cmakelint.lint.is_valid_file("/foo/bar/baz/CMakeLists.txt")
    assert cmakelint.lint.is_valid_file("Findkk.cmake")
    assert not cmakelint.lint.is_valid_file("foobar.h.in")


def test_filter_control():
    do_test_multi_line_lint(("# lint_cmake: -whitespace/eol\n" "  foo() \n" "  foo()\n"), "")


def test_bad_pragma():
    do_test_multi_line_lint(
        ("# lint_cmake: I am badly formed\n" "if(TRUE)\n" "endif()\n"), "Filter should start with - or +"
    )
    cmakelint.state._lint_state.reset()


def test_bad_pragma2():
    do_test_multi_line_lint(
        ("# lint_cmake: -unknown thing\n" "if(TRUE)\n" "endif()\n"), "Filter not allowed: -unknown thing"
    )
    cmakelint.state._lint_state.reset()


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
        cmakelint.state._lint_state.spaces = 2
        do_test_lint("no_indent(test)", "")
        do_test_lint("  two_indent(test)", "")
        do_test_lint("    four_indent(test)", "")
        do_test_lint(" one_indent(test)", "Weird indentation; use 2 spaces")
        do_test_lint("   three_indent(test)", "Weird indentation; use 2 spaces")

        cmakelint.state._lint_state.spaces = 3
        do_test_lint("no_indent(test)", "")
        do_test_lint("  two_indent(test)", "Weird indentation; use 3 spaces")
        do_test_lint("    four_indent(test)", "Weird indentation; use 3 spaces")
        do_test_lint(" one_indent(test)", "Weird indentation; use 3 spaces")
        do_test_lint("   three_indent(test)", "")
    finally:
        cmakelint.state._lint_state.reset()
