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

import contextlib
import sys

import cmakelint.__main__


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
        if cmakelint.__main__.should_print_error(category):
            self._errors.append(message)

    def results(self):
        if len(self._errors) < 2:
            return "".join(self._errors)
        return self._errors


def do_test_lint(code, expected_message):
    errors = ErrorCollector()
    clean_lines = cmakelint.__main__.CleansedLines([code])
    cmakelint.__main__.process_line("foo.cmake", 0, clean_lines, errors)
    assert errors.results() == expected_message


def do_test_multi_line_lint(code, expected_message):
    errors = ErrorCollector()
    clean_lines = cmakelint.__main__.CleansedLines(code.split("\n"))
    for i in clean_lines.line_numbers():
        cmakelint.__main__.process_line("foo.cmake", i, clean_lines, errors)
    assert errors.results() == expected_message


def do_test_check_repeat_logic(code, expected_message):
    errors = ErrorCollector()
    clean_lines = cmakelint.__main__.CleansedLines(code.split("\n"))
    for i in clean_lines.line_numbers():
        cmakelint.__main__.check_repeat_logic("foo.cmake", i, clean_lines, errors)
    assert errors.results() == expected_message


def do_test_check_file_name(filename, expected_message):
    errors = ErrorCollector()
    cmakelint.__main__.check_file_name(filename, errors)
    assert errors.results() == expected_message


def do_test_check_find_package(filename, code, expected_message):
    errors = ErrorCollector()
    clean_lines = cmakelint.__main__.CleansedLines(code.split("\n"))
    for i in clean_lines.line_numbers():
        cmakelint.__main__.check_find_package(filename, i, clean_lines, errors)
    cmakelint.__main__._package_state.done(filename, errors)
    assert errors.results() == expected_message


def do_test_get_argument(expected_arg, code):
    clean_lines = cmakelint.__main__.CleansedLines(code.split("\n"))
    assert cmakelint.__main__.get_command_argument(0, clean_lines) == expected_arg
