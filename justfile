set positional-arguments

PYTHON_DIR := if os_family() == "windows" { "./.venv/Scripts" } else { "./.venv/bin" }
PYTHON := PYTHON_DIR + if os_family() == "windows" { "/python.exe" } else { "/python3" }
SYSTEM_PYTHON := if os_family() == "windows" { "py.exe -3" } else { "python3" }

create-venv:
  {{SYSTEM_PYTHON}} -m venv .venv

install:
  {{PYTHON}} -m pip install -U pip
  {{PYTHON}} -m pip install -e ".[dev]"

run *ARGS:
  {{PYTHON}} -m cmake-lint {{ARGS}}

test:
  {{PYTHON}} -m pytest
  just clean

snapshot:
  {{PYTHON}} -m pytest --snapshot-update

build:
  {{PYTHON}} -m build

release version:
  @echo 'Tagging {{version}}...'
  git tag {{version}}
  @echo 'Push to GitHub to trigger publish process...'
  git push --tags

clean:
  rm -rf tmp/
  rm -rf .pytest_cache/

clean-builds:
  rm -rf build/
  rm -rf dist/
  rm -rf *.egg-info/

lint:
  {{PYTHON}} -m ruff check .

fmt:
  {{PYTHON}} -m ruff format .

ci-test:
  {{PYTHON}} -m pytest
  just clean
