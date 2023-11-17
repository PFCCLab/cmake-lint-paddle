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
import re

from cmakelint.rules import ERROR_CATEGORIES


def default_rc():
    """
    Check current working directory and XDG_CONFIG_DIR before ~/.cmakelintrc
    """
    cwdfile = os.path.join(os.getcwd(), ".cmakelintrc")
    if os.path.exists(cwdfile):
        return cwdfile
    xdg = os.path.join(os.path.expanduser("~"), ".config")
    if "XDG_CONFIG_DIR" in os.environ:
        xdg = os.environ["XDG_CONFIG_DIR"]
    xdgfile = os.path.join(xdg, "cmakelintrc")
    if os.path.exists(xdgfile):
        return xdgfile
    return os.path.join(os.path.expanduser("~"), ".cmakelintrc")


def is_find_package(filename):
    return os.path.basename(filename).startswith("Find") and filename.endswith(".cmake")


_DEFAULT_CMAKELINTRC = default_rc()


class _CMakeLintState:
    def __init__(self):
        self.filters = []
        self.config: str | None = _DEFAULT_CMAKELINTRC
        self.errors = 0
        self.spaces = 2
        self.linelength = 80
        self.allowed_categories = ERROR_CATEGORIES.split()
        self.quiet = False

    def set_filters(self, filters):
        if not filters:
            return
        assert isinstance(self.filters, list)
        if isinstance(filters, list):
            self.filters.extend(filters)
        elif isinstance(filters, str):
            self.filters.extend([f.strip() for f in filters.split(",") if f])
        else:
            raise ValueError("Filters should be a list or a comma separated string")
        for f in self.filters:
            if f.startswith("-") or f.startswith("+"):
                allowed = False
                for c in self.allowed_categories:
                    if c.startswith(f[1:]):
                        allowed = True
                if not allowed:
                    raise ValueError("Filter not allowed: %s" % f)
            else:
                raise ValueError("Filter should start with - or +")

    def set_spaces(self, spaces: int):
        self.spaces = spaces

    def set_quiet(self, quiet: bool):
        self.quiet = quiet

    def set_line_length(self, linelength):
        self.linelength = int(linelength)

    def reset(self):
        self.filters = []
        self.config = _DEFAULT_CMAKELINTRC
        self.errors = 0
        self.spaces = 2
        self.linelength = 80
        self.allowed_categories = ERROR_CATEGORIES.split()
        self.quiet = False


class _CMakePackageState:
    def __init__(self):
        self.sets = []
        self.have_included_stdargs = False
        self.have_used_stdargs = False

    def check(self, filename, linenumber, clean_lines, errors):
        pass

    def _get_expected(self, filename):
        package = os.path.basename(filename)
        package = re.sub(r"^Find(.*)\.cmake", lambda m: m.group(1), package)
        return package.upper()

    def done(self, filename, errors):
        try:
            if not is_find_package(filename):
                return
            if self.have_included_stdargs and self.have_used_stdargs:
                return
            if not self.have_included_stdargs:
                errors(filename, 0, "package/consistency", "Package should include FindPackageHandleStandardArgs")
            if not self.have_used_stdargs:
                errors(filename, 0, "package/consistency", "Package should use FIND_PACKAGE_HANDLE_STANDARD_ARGS")
        finally:
            self.have_used_stdargs = False
            self.have_included_stdargs = False

    def have_used_standard_args(self, filename, linenumber, var, errors):
        expected = self._get_expected(filename)
        self.have_used_stdargs = True
        if expected != var:
            errors(
                filename,
                linenumber,
                "package/stdargs",
                "Weird variable passed to std args, should be " + expected + " not " + var,
            )

    def have_included(self, var):
        if var == "FindPackageHandleStandardArgs":
            self.have_included_stdargs = True

    def set(self, var):
        self.sets.append(var)


_lint_state = _CMakeLintState()
_package_state = _CMakePackageState()
