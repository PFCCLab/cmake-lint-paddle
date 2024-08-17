# CMakeLint

<p align="center">
   <a href="https://python.org/" target="_blank"><img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/cmake-lint-paddle?logo=python&style=flat-square"></a>
   <a href="https://pypi.org/project/cmake-lint-paddle/" target="_blank"><img src="https://img.shields.io/pypi/v/cmake-lint-paddle?style=flat-square" alt="pypi"></a>
   <a href="https://pypi.org/project/cmake-lint-paddle/" target="_blank"><img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/cmake-lint-paddle?style=flat-square"></a>
   <a href="LICENSE"><img alt="LICENSE" src="https://img.shields.io/github/license/PFCCLab/cmake-lint-paddle?style=flat-square"></a>
   <a href="https://github.com/astral-sh/uv"><img alt="uv" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json&style=flat-square"></a>
   <a href="https://github.com/astral-sh/ruff"><img alt="ruff" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat-square"></a>
   <a href="https://gitmoji.dev"><img src="https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67?style=flat-square" alt="Gitmoji"></a>
</p>

cmakelint parses CMake files and reports style issues.

cmakelint requires Python.

## Installation

To install cmakelint from PyPI, run:

```bash
pip install cmake-lint-paddle
```

## Usage

```bash
cmakelint --help
usage: cmakelint [-h] [-v] [--filter -X,+Y] [--config CONFIG] [--spaces SPACES] [--linelength LINELENGTH] [--quiet] [files ...]

cmakelint

positional arguments:
  files                 files to lint

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  --filter -X,+Y        Specify a comma separated list of filters to apply
  --config CONFIG       Use the given file for configuration. By default the file $PWD/.cmakelintrc, ~/.config/cmakelintrc,
                        $XDG_CONFIG_DIR/cmakelintrc or ~/.cmakelintrc is used if it exists. Use the value "None" to use no configuration file
                        (./None for a file called literally None) Only the option "filter=" is currently supported in this file.
  --spaces SPACES       Indentation should be a multiple of N spaces
  --linelength LINELENGTH
                        This is the allowed line length for the project. The default value is 80 characters.
  --quiet               makes output quiet unless errors occurs Mainly used by automation tools when parsing huge amount of files. In those
                        cases actual error might get lost in the pile of other stats prints. This argument is also handy for build system
                        integration, so it's possible to add automated lint target to a project and invoke it via build system and have no
                        pollution of terminals or IDE.
```

Run the `--filter=` option with no filter to see available options. Currently
these are:

```
convention/filename
linelength
package/consistency
readability/logic
readability/mixedcase
readability/wonkycase
syntax
whitespace/eol
whitespace/extra
whitespace/indent
whitespace/mismatch
whitespace/newline
whitespace/tabs
```

An example .cmakelintrc file would be as follows:

```
filter=-whitespace/indent
```

With this file in your home directory, running these commands would have the
same effect:

```bash
cmakelint.py CMakeLists.txt
cmakelint.py --filter=-whitespace/indent CMakeLists.txt
```

Filters can optionally be directly enabled/disabled from within a CMake file,
overriding the configuration from file or CLI argument:

```
# lint_cmake: <+ or -><filter name>
# e.g.:
# lint_cmake: -readability/wonkycase
# add multiple filters as list:
# lint_cmake: <+/-><filter1>, <+/-><filter2>
```

cmakelint can also be run with [pre-commit](https://pre-commit.com). Add the following configuration block to your `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/PFCCLab/cmake-lint-paddle
  rev: v1.5.2
  hooks:
     - id: cmakelint
```

# Output status codes

The program should exit with the following status codes:

-  0 if everything went fine
-  1 if an error message was issued
-  32 on usage error
