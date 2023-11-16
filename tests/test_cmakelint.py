#!/usr/bin/env python
"""
Copyright 2009 Richard Quirk

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

import contextlib
import os
import sys
import unittest
from unittest import mock

import cmakelint.__main__
import cmakelint.__version__


# stderr suppression from https://stackoverflow.com/a/1810086
@contextlib.contextmanager
def nostderr():
    savestderr = sys.stderr

    class Devnull:
        def write(self, _):
            pass

        def flush(self):
            pass

    sys.stderr = Devnull()
    try:
        yield
    finally:
        sys.stderr = savestderr


class ErrorCollector:
    def __init__(self):
        self._errors = []

    def __call__(self, unused_filename, unused_line, category, message):
        if cmakelint.__main__.ShouldPrintError(category):
            self._errors.append(message)

    def Results(self):
        if len(self._errors) < 2:
            return "".join(self._errors)
        return self._errors


class CMakeLintTestBase(unittest.TestCase):
    def doTestLint(self, code, expected_message):
        errors = ErrorCollector()
        clean_lines = cmakelint.__main__.CleansedLines([code])
        cmakelint.__main__.ProcessLine("foo.cmake", 0, clean_lines, errors)
        self.assertEqual(expected_message, errors.Results())

    def doTestMultiLineLint(self, code, expected_message):
        errors = ErrorCollector()
        clean_lines = cmakelint.__main__.CleansedLines(code.split("\n"))
        for i in clean_lines.LineNumbers():
            cmakelint.__main__.ProcessLine("foo.cmake", i, clean_lines, errors)
        self.assertEqual(expected_message, errors.Results())

    def doTestCheckRepeatLogic(self, code, expected_message):
        errors = ErrorCollector()
        clean_lines = cmakelint.__main__.CleansedLines(code.split("\n"))
        for i in clean_lines.LineNumbers():
            cmakelint.__main__.CheckRepeatLogic("foo.cmake", i, clean_lines, errors)
        self.assertEqual(expected_message, errors.Results())

    def doTestCheckFileName(self, filename, expected_message):
        errors = ErrorCollector()
        cmakelint.__main__.CheckFileName(filename, errors)
        self.assertEqual(expected_message, errors.Results())

    def doTestCheckFindPackage(self, filename, code, expected_message):
        errors = ErrorCollector()
        clean_lines = cmakelint.__main__.CleansedLines(code.split("\n"))
        for i in clean_lines.LineNumbers():
            cmakelint.__main__.CheckFindPackage(filename, i, clean_lines, errors)
        cmakelint.__main__._package_state.Done(filename, errors)
        self.assertEqual(expected_message, errors.Results())

    def doTestGetArgument(self, expected_arg, code):
        clean_lines = cmakelint.__main__.CleansedLines(code.split("\n"))
        self.assertEqual(expected_arg, cmakelint.__main__.GetCommandArgument(0, clean_lines))


class CMakeLintTest(CMakeLintTestBase):
    def setUp(self):
        cmakelint.__main__._lint_state.filters = []

    def testLineLength(self):
        self.doTestLint("# " + ("o" * 80), "Lines should be <= 80 characters long")

    def testUpperAndLowerCase(self):
        self.doTestMultiLineLint(
            """project()\nCMAKE_MINIMUM_REQUIRED()\n""", "Do not mix upper and lower case commands"
        )

    def testContainsCommand(self):
        self.assertTrue(cmakelint.__main__.ContainsCommand("project()"))
        self.assertTrue(cmakelint.__main__.ContainsCommand("project("))
        self.assertTrue(cmakelint.__main__.ContainsCommand("project  ( "))
        self.assertFalse(cmakelint.__main__.ContainsCommand("VERSION"))

    def testGetCommand(self):
        self.assertEqual("project", cmakelint.__main__.GetCommand("project()"))
        self.assertEqual("project", cmakelint.__main__.GetCommand("project("))
        self.assertEqual("project", cmakelint.__main__.GetCommand("project  ( "))
        self.assertEqual("", cmakelint.__main__.GetCommand("VERSION"))

    def testIsCommandUpperCase(self):
        self.assertTrue(cmakelint.__main__.IsCommandUpperCase("PROJECT"))
        self.assertTrue(cmakelint.__main__.IsCommandUpperCase("CMAKE_MINIMUM_REQUIRED"))
        self.assertFalse(cmakelint.__main__.IsCommandUpperCase("cmake_minimum_required"))
        self.assertFalse(cmakelint.__main__.IsCommandUpperCase("project"))
        self.assertFalse(cmakelint.__main__.IsCommandUpperCase("PrOjEct"))

    def testIsCommandMixedCase(self):
        self.assertTrue(cmakelint.__main__.IsCommandMixedCase("PrOjEct"))
        self.assertFalse(cmakelint.__main__.IsCommandMixedCase("project"))
        self.assertFalse(cmakelint.__main__.IsCommandMixedCase("CMAKE_MINIMUM_REQUIRED"))
        self.assertTrue(cmakelint.__main__.IsCommandMixedCase("CMAKE_MINIMUM_required"))

    def testCleanComment(self):
        self.assertEqual(("", False), cmakelint.__main__.CleanComments("# Comment to zap"))
        self.assertEqual(("project()", False), cmakelint.__main__.CleanComments("project() # Comment to zap"))

    def testCleanCommentQuotes(self):
        self.assertEqual(
            ('CHECK_C_SOURCE_COMPILES("', True), cmakelint.__main__.CleanComments('CHECK_C_SOURCE_COMPILES("')
        )

        self.assertEqual(("", True), cmakelint.__main__.CleanComments(" some line in a comment ", True))

        self.assertEqual(('")', False), cmakelint.__main__.CleanComments(' end of comment") ', True))

    def testCommandSpaces(self):
        self.doTestMultiLineLint("""project ()""", "Extra spaces between 'project' and its ()")

    def testTabs(self):
        self.doTestLint("\tfoo()", "Tab found; please use spaces")

    def testTrailingSpaces(self):
        self.doTestLint("# test ", "Line ends in whitespace")
        self.doTestMultiLineLint("  foo() \n  foo()\n", "Line ends in whitespace")
        self.doTestLint("    set(var value)", "")

    def testCommandSpaceBalance(self):
        self.doTestMultiLineLint("""project( Foo)""", "Mismatching spaces inside () after command")
        self.doTestMultiLineLint("""project(Foo )""", "Mismatching spaces inside () after command")

    def testCommandNotEnded(self):
        self.doTestMultiLineLint(
            """project(
                Foo
                #
                #""",
            "Unable to find the end of this command",
        )

    def testRepeatLogicExpression(self):
        self.doTestCheckRepeatLogic("else(foo)", "Expression repeated inside else; " "better to use only else()")
        self.doTestCheckRepeatLogic("ELSEIF(NOT ${VAR})", "")
        self.doTestCheckRepeatLogic(
            "ENDMACRO( my_macro foo bar baz)", "Expression repeated inside endmacro; " "better to use only ENDMACRO()"
        )

    def testFindTool(self):
        self.doTestCheckFileName(
            "path/to/FindFooBar.cmake", "Find modules should use uppercase names; " "consider using FindFOOBAR.cmake"
        )
        self.doTestCheckFileName("CMakeLists.txt", "")
        self.doTestCheckFileName("cmakeLists.txt", "File should be called CMakeLists.txt")

    def testIsFindPackage(self):
        self.assertTrue(cmakelint.__main__.IsFindPackage("path/to/FindFOO.cmake"))
        self.assertFalse(cmakelint.__main__.IsFindPackage("path/to/FeatureFOO.cmake"))

    def testCheckFindPackage(self):
        self.doTestCheckFindPackage(
            "FindFoo.cmake",
            "",
            [
                "Package should include FindPackageHandleStandardArgs",
                "Package should use FIND_PACKAGE_HANDLE_STANDARD_ARGS",
            ],
        )
        self.doTestCheckFindPackage(
            "FindFoo.cmake",
            """INCLUDE(FindPackageHandleStandardArgs)""",
            "Package should use FIND_PACKAGE_HANDLE_STANDARD_ARGS",
        )
        self.doTestCheckFindPackage(
            "FindFoo.cmake",
            """FIND_PACKAGE_HANDLE_STANDARD_ARGS(FOO DEFAULT_MSG)""",
            "Package should include FindPackageHandleStandardArgs",
        )
        self.doTestCheckFindPackage(
            "FindFoo.cmake",
            """INCLUDE(FindPackageHandleStandardArgs)
                FIND_PACKAGE_HANDLE_STANDARD_ARGS(KK DEFAULT_MSG)""",
            "Weird variable passed to std args, should be FOO not KK",
        )
        self.doTestCheckFindPackage(
            "FindFoo.cmake",
            """INCLUDE(FindPackageHandleStandardArgs)
                FIND_PACKAGE_HANDLE_STANDARD_ARGS(FOO DEFAULT_MSG)""",
            "",
        )

    def testGetCommandArgument(self):
        self.doTestGetArgument(
            "KK",
            """SET(
                KK)""",
        )
        self.doTestGetArgument("KK", "Set(  KK)")
        self.doTestGetArgument("KK", "FIND_PACKAGE_HANDLE_STANDARD_ARGS(KK BLEUGH)")

    def testIsValidFile(self):
        self.assertTrue(cmakelint.__main__.IsValidFile("CMakeLists.txt"))
        self.assertTrue(cmakelint.__main__.IsValidFile("cmakelists.txt"))
        self.assertTrue(cmakelint.__main__.IsValidFile("/foo/bar/baz/CMakeLists.txt"))
        self.assertTrue(cmakelint.__main__.IsValidFile("Findkk.cmake"))
        self.assertFalse(cmakelint.__main__.IsValidFile("foobar.h.in"))

    def testFilterControl(self):
        self.doTestMultiLineLint(("# lint_cmake: -whitespace/eol\n" "  foo() \n" "  foo()\n"), "")

    def testBadPragma(self):
        self.doTestMultiLineLint(
            ("# lint_cmake: I am badly formed\n" "if(TRUE)\n" "endif()\n"), "Filter should start with - or +"
        )

    def testBadPragma2(self):
        self.doTestMultiLineLint(
            ("# lint_cmake: -unknown thing\n" "if(TRUE)\n" "endif()\n"), "Filter not allowed: -unknown thing"
        )

    def testWhitespaceIssue16(self):
        self.doTestMultiLineLint(
            ("if(${CONDITION})\n" "  set(VAR\n" "      foo\n" "      bar\n" "  )\n" "endif()\n"), ""
        )

    def testWhitespaceIssue16NonRegression(self):
        self.doTestMultiLineLint(("if(${CONDITION})\n" "  set(VAR\n" "      foo\n" "      bar)\n" "endif()\n"), "")

    def testWhitespaceIssue16FalseNegative(self):
        self.doTestMultiLineLint(
            ("if(${CONDITION})\n" "  set(VAR\n" "      foo\n" "      bar  )\n" "endif()\n"),
            "Mismatching spaces inside () after command",
        )

    def testNoEnd(self):
        self.doTestMultiLineLint('file(APPEND ${OUT} "#endif${nl}")\n', "")

    def testBackslashComment(self):
        self.doTestMultiLineLint(r'file(APPEND ${OUT} " \"") # comment\n', "")

    def testFalsePositiveSourceCompiles(self):
        self.doTestMultiLineLint(
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

    def testIndent(self):
        try:
            cmakelint.__main__._lint_state.spaces = 2
            self.doTestLint("no_indent(test)", "")
            self.doTestLint("  two_indent(test)", "")
            self.doTestLint("    four_indent(test)", "")
            self.doTestLint(" one_indent(test)", "Weird indentation; use 2 spaces")
            self.doTestLint("   three_indent(test)", "Weird indentation; use 2 spaces")

            cmakelint.__main__._lint_state.spaces = 3
            self.doTestLint("no_indent(test)", "")
            self.doTestLint("  two_indent(test)", "Weird indentation; use 3 spaces")
            self.doTestLint("    four_indent(test)", "Weird indentation; use 3 spaces")
            self.doTestLint(" one_indent(test)", "Weird indentation; use 3 spaces")
            self.doTestLint("   three_indent(test)", "")
        finally:
            cmakelint.__main__._lint_state.spaces = 2

    def testParseArgs(self):
        old_usage = cmakelint.__main__._USAGE
        old_version = cmakelint.__version__.VERSION
        old_cats = cmakelint.__main__._ERROR_CATEGORIES
        old_spaces = cmakelint.__main__._lint_state.spaces
        try:
            cmakelint.__main__._USAGE = ""
            cmakelint.__main__._ERROR_CATEGORIES = ""
            cmakelint.__main__._VERSION = ""
            with nostderr():
                self.assertRaises(SystemExit, cmakelint.__main__.ParseArgs, [])
                self.assertRaises(SystemExit, cmakelint.__main__.ParseArgs, ["--help"])
                self.assertRaises(SystemExit, cmakelint.__main__.ParseArgs, ["--bogus-option"])
                self.assertRaises(SystemExit, cmakelint.__main__.ParseArgs, ["--filter="])
                self.assertRaises(SystemExit, cmakelint.__main__.ParseArgs, ["--filter=foo"])
                self.assertRaises(SystemExit, cmakelint.__main__.ParseArgs, ["--filter=+x,b,-c", "foo.cmake"])
                self.assertRaises(SystemExit, cmakelint.__main__.ParseArgs, ["--spaces=c", "foo.cmake"])
                self.assertRaises(SystemExit, cmakelint.__main__.ParseArgs, ["--version"])
            cmakelint.__main__._lint_state.filters = []
            self.assertEqual(["foo.cmake"], cmakelint.__main__.ParseArgs(["--filter=-whitespace", "foo.cmake"]))
            cmakelint.__main__._lint_state.filters = []
            self.assertEqual(["foo.cmake"], cmakelint.__main__.ParseArgs(["foo.cmake"]))
            filt = "-,+whitespace"
            cmakelint.__main__._lint_state.filters = []
            self.assertEqual(
                ["foo.cmake"],
                cmakelint.__main__.ParseArgs(["--config=None", "--spaces=3", "--filter=" + filt, "foo.cmake"]),
            )
            self.assertEqual(["-", "+whitespace"], cmakelint.__main__._lint_state.filters)
            self.assertEqual(3, cmakelint.__main__._lint_state.spaces)
            cmakelint.__main__._lint_state.filters = []
            filt = "-,+whitespace/eol, +whitespace/tabs"
            self.assertEqual(
                ["foo.cmake"],
                cmakelint.__main__.ParseArgs(["--config=None", "--spaces=3", "--filter=" + filt, "foo.cmake"]),
            )
            self.assertEqual(["-", "+whitespace/eol", "+whitespace/tabs"], cmakelint.__main__._lint_state.filters)

            cmakelint.__main__._lint_state.filters = []
            cmakelint.__main__.ParseArgs(["--config=./foo/bar", "foo.cmake"])
            self.assertEqual("./foo/bar", cmakelint.__main__._lint_state.config)
            cmakelint.__main__.ParseArgs(["--config=None", "foo.cmake"])
            self.assertEqual(None, cmakelint.__main__._lint_state.config)
            cmakelint.__main__.ParseArgs(["foo.cmake"])
            self.assertEqual(
                os.path.expanduser("~") + os.path.sep + ".cmakelintrc", cmakelint.__main__._lint_state.config
            )
            config = {"return_value": True}
            patcher = mock.patch("os.path.isfile", **config)
            try:
                patcher.start()
                self.assertEqual(["CMakeLists.txt"], cmakelint.__main__.ParseArgs([]))
                self.assertEqual(
                    os.path.expanduser("~") + os.path.sep + ".cmakelintrc", cmakelint.__main__._lint_state.config
                )
            finally:
                patcher.stop()
        finally:
            cmakelint.__main__._USAGE = old_usage
            cmakelint.__main__._ERROR_CATEGORIES = old_cats
            cmakelint.__main__._VERSION = old_version
            cmakelint.__main__._lint_state.filters = []
            cmakelint.__main__._lint_state.spaces = old_spaces

    def testParseOptionsFile(self):
        old_usage = cmakelint.__main__._USAGE
        old_cats = cmakelint.__main__._ERROR_CATEGORIES
        old_spaces = cmakelint.__main__._lint_state.spaces
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
            self.assertEqual(["-", "+whitespace"], cmakelint.__main__._lint_state.filters)
            cmakelint.__main__.ParseArgs(["--filter=+syntax", "foo.cmake"])
            self.assertEqual(["-", "+whitespace", "+syntax"], cmakelint.__main__._lint_state.filters)
            self.assertEqual(3, cmakelint.__main__._lint_state.spaces)

            cmakelint.__main__._lint_state.spaces = 2
            cmakelint.__main__.ParseOptionFile(
                """
                    # skip comment
                    spaces= 4
                    """.split("\n"),
                ignore_space=True,
            )
            self.assertEqual(2, cmakelint.__main__._lint_state.spaces)

            cmakelint.__main__.ParseOptionFile(
                """
                    # skip comment
                    linelength= 90
                    """.split("\n"),
                ignore_space=True,
            )
            self.assertEqual(90, cmakelint.__main__._lint_state.linelength)

            cmakelint.__main__.ParseOptionFile(
                """
                    # skip comment
                    """.split("\n"),
                ignore_space=False,
            )
            self.assertEqual(2, cmakelint.__main__._lint_state.spaces)

            cmakelint.__main__.ParseOptionFile(
                """
                    quiet
                    """.split("\n"),
                ignore_space=False,
            )
            self.assertTrue(cmakelint.__main__._lint_state.quiet)

            cmakelint.__main__._lint_state.quiet = True
            cmakelint.__main__.ParseOptionFile(
                """
                    # quiet
                    """.split("\n"),
                ignore_space=False,
            )
            self.assertTrue(cmakelint.__main__._lint_state.quiet)
        finally:
            cmakelint.__main__._USAGE = old_usage
            cmakelint.__main__._ERROR_CATEGORIES = old_cats
            cmakelint.__main__._lint_state.spaces = old_spaces


if __name__ == "__main__":
    unittest.main()
