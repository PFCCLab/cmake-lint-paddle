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

import sys

from cmakelint.cli import parse_args
from cmakelint.error_code import ERROR_CODE_FOUND_ISSUE
from cmakelint.lint import process_file
from cmakelint.state import _lint_state


def main():
    files = parse_args(sys.argv[1:])

    for filename in files:
        process_file(filename)
    if _lint_state.errors > 0 or not _lint_state.quiet:
        sys.stderr.write(f"Total Errors: {_lint_state.errors}\n")
    if _lint_state.errors > 0:
        return ERROR_CODE_FOUND_ISSUE
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
