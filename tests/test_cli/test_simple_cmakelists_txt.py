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

from ..conftest import TEST_DIR
from .utils import _run_and_check

CMAKELISTS = "CMakeLists.txt"


def test_invocation():
    (TEST_DIR / CMAKELISTS).touch()
    _run_and_check("", [CMAKELISTS], 0, [""], ["Total Errors: 0", ""])
