set positional-arguments

install:
  uv sync

run *ARGS:
  uv run cmakelint {{ARGS}}

test:
  uv run pytest
  just clean

snapshot:
  uv run pytest --snapshot-update

build:
  uv tool run --from build python -m build --installer uv .

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
  uv run ruff check .

fmt:
  uv run ruff format .

ci-test:
  uv run pytest
  just clean
