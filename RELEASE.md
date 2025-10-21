# Release Process

This document describes how to publish a new release of rupy-api to PyPI.

## Package Name

The package is published on PyPI as **`rupy-api`** (with the name change from the original `rupy` to avoid naming conflicts).

## Automatic Publishing

The repository is configured with a GitHub Actions workflow (`.github/workflows/publish.yml`) that automatically publishes to PyPI when a new release is created on GitHub.

### How to Publish a New Release

1. **Update the version** in `pyproject.toml`:
   ```toml
   [project]
   name = "rupy-api"
   version = "0.2.0"  # Update this
   ```

2. **Commit and push** the version change:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.2.0"
   git push origin main
   ```

3. **Create a GitHub Release**:
   - Go to https://github.com/manoelhc/rupy/releases/new
   - Click "Choose a tag" and create a new tag (e.g., `v0.2.0`)
   - Fill in the release title (e.g., "Release 0.2.0")
   - Add release notes describing changes
   - Click "Publish release"

4. **Automated workflow will**:
   - Run all Rust tests
   - Build Python wheels for Ubuntu, Windows, and macOS
   - Run Python tests
   - Build source distribution (sdist)
   - Publish all distributions to PyPI using trusted publishing

5. **Verify the release**:
   - Check the Actions tab for the workflow run status
   - Once complete, verify on PyPI: https://pypi.org/project/rupy-api/

## Setup Requirements

### PyPI Trusted Publishing (OIDC)

The workflow uses PyPI's trusted publishing feature, which eliminates the need for API tokens. To set this up:

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new publisher with these settings:
   - **PyPI Project Name**: `rupy-api`
   - **Owner**: `manoelhc`
   - **Repository name**: `rupy`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`

### GitHub Environment

Create a GitHub environment named `pypi` (this is already configured in the workflow):

1. Go to repository Settings → Environments
2. Create an environment named `pypi`
3. (Optional) Add protection rules like requiring manual approval

## Workflow Details

The publish workflow consists of three jobs:

1. **Test Job** (`test`):
   - Runs on Ubuntu
   - Executes Rust tests
   - Builds the Python package
   - Tests package installation
   - Runs Python test suite

2. **Build Wheels Job** (`build-wheels`):
   - Runs in parallel on Ubuntu, Windows, and macOS
   - Builds platform-specific wheels
   - Uploads wheels as artifacts

3. **Publish Job** (`publish`):
   - Downloads all wheels
   - Builds source distribution
   - Publishes to PyPI using trusted publishing

## Manual Build and Test

To manually build and test the package locally:

```bash
# Install maturin
pip install maturin

# Build the package
maturin build --release

# Install locally
pip install target/wheels/rupy_api-*.whl

# Test import
python -c "from rupy import Rupy; print('Success!')"

# Run tests
pip install pytest requests
pytest tests/
```

## Troubleshooting

### Workflow fails during publish

- Check that PyPI trusted publishing is configured correctly
- Verify the `pypi` environment exists in GitHub
- Check workflow logs in the Actions tab

### Version already exists on PyPI

- PyPI does not allow re-uploading the same version
- Increment the version number in `pyproject.toml`
- Create a new release

### Tests fail

- Review the test job logs
- Fix any failing tests before creating a release
- Consider running tests locally first

## Package Installation

Users can install the published package with:

```bash
pip install rupy-api
```

Or in `pyproject.toml`:

```toml
[project]
dependencies = [
    "rupy-api>=0.1.0"
]
```
