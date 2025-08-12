set positional-arguments

install:
  uv sync --all-extras --dev

run *ARGS:
  uv run cmakelint {{ARGS}}

test:
  uv run pytest
  just clean

fmt:
  uv run ruff format .
  prettier --write '**/*.md'

lint:
  uv run ruff check .

snapshot-update:
  uv run pytest --snapshot-update

build:
  uv build

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

ci-install:
  just install

ci-fmt-check:
  uv run ruff format --check --diff .
  prettier --check '**/*.md'

ci-lint:
  just lint

ci-test:
  uv run pytest
  just clean

fmt-check:
  uv run ruff format --check --diff .
