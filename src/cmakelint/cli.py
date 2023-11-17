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

import argparse
import os
import sys

from cmakelint.__version__ import VERSION as CMAKELINT_VERSION
from cmakelint.error_code import ERROR_CODE_WRONG_USAGE
from cmakelint.rules import ERROR_CATEGORIES
from cmakelint.state import LINT_STATE

_DEFAULT_FILENAME = "CMakeLists.txt"


def print_categories():
    sys.stderr.write(ERROR_CATEGORIES)
    sys.exit(0)


def parse_option_file(contents, ignore_space):
    filters = None
    spaces = None
    linelength = None
    for line in contents:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("filter="):
            filters = line.replace("filter=", "")
        if line.startswith("spaces="):
            spaces = line.replace("spaces=", "")
        if line == "quiet":
            LINT_STATE.set_quiet(True)
        if line.startswith("linelength="):
            linelength = line.replace("linelength=", "")
    LINT_STATE.set_filters(filters)
    if spaces and not ignore_space:
        LINT_STATE.set_spaces(int(spaces.strip()))
    if linelength is not None:
        LINT_STATE.set_line_length(linelength)


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(ERROR_CODE_WRONG_USAGE, f"{self.prog}: error: {message}\n")


def parse_args(argv):
    parser = ArgumentParser("cmakelint", description="cmakelint")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {CMAKELINT_VERSION}")
    parser.add_argument("files", nargs="*", help="files to lint")
    parser.add_argument(
        "--filter", default=None, metavar="-X,+Y", help="Specify a comma separated list of filters to apply"
    )
    parser.add_argument(
        "--config",
        default=None,
        help="""
        Use the given file for configuration. By default the file
        $PWD/.cmakelintrc, ~/.config/cmakelintrc, $XDG_CONFIG_DIR/cmakelintrc or
        ~/.cmakelintrc is used if it exists. Use the value "None" to use no
        configuration file (./None for a file called literally None) Only the
        option "filter=" is currently supported in this file.
        """,
    )
    parser.add_argument("--spaces", type=int, default=None, help="Indentation should be a multiple of N spaces")
    parser.add_argument(
        "--linelength",
        type=int,
        default=None,
        help="This is the allowed line length for the project. The default value is 80 characters.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="""
        makes output quiet unless errors occurs
        Mainly used by automation tools when parsing huge amount of files.
        In those cases actual error might get lost in the pile of other stats
        prints.

        This argument is also handy for build system integration, so it's
        possible to add automated lint target to a project and invoke it
        via build system and have no pollution of terminals or IDE.
        """,
    )

    args = parser.parse_args(argv)
    ignore_space = args.spaces is not None
    if args.config is not None:
        if args.config == "None":
            LINT_STATE.config = None
        elif args.config is not None:
            LINT_STATE.config = args.config
    if args.linelength is not None:
        LINT_STATE.set_line_length(args.linelength)
    if args.spaces is not None:
        LINT_STATE.set_spaces(args.spaces)
    if args.filter is not None:
        if args.filter == "":
            print_categories()
    LINT_STATE.set_quiet(args.quiet)

    try:
        if LINT_STATE.config and os.path.isfile(LINT_STATE.config):
            with open(LINT_STATE.config) as f:
                parse_option_file(f.readlines(), ignore_space)
        LINT_STATE.set_filters(args.filter)
    except ValueError as e:
        parser.error(str(e))

    filenames = args.files
    if not filenames:
        if os.path.isfile(_DEFAULT_FILENAME):
            filenames = [_DEFAULT_FILENAME]
        else:
            parser.error("No files were specified!")
    return filenames
