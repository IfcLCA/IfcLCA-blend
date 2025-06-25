# Packaging IfcLCA-blend Addon

## Quick Start

To create a distribution package of the IfcLCA-blend addon:

```bash
# From the repository root
./tools/package.sh
```

OR

```bash
# From the repository root
python3 tools/package_addon.py
```

OR

```bash
# From the tools directory
cd tools
./package.sh
```

This will create a timestamped zip file (e.g., `IfcLCA-blend_20250625.zip`) containing all necessary files for the Blender addon.

## What's Included

The package includes:
- Core Python files (__init__.py, logic.py, operators.py, panels.py, etc.)
- Web interface files (HTML, CSS, JavaScript)
- Sample database files (KBOB and CSV samples)
- License file
- Installation README

## What's Excluded

The following are automatically excluded:
- Test files (test_*.py)
- Debug scripts (debug_*.py)
- Python cache files (__pycache__, *.pyc)
- Coverage reports (htmlcov, .coverage)
- Development files (pytest.ini, CONTRIBUTING.md)
- Git files (.git, .gitignore)

## Customization

To modify what's included/excluded, edit the `EXCLUDE_PATTERNS` set in `package_addon.py`.

## Distribution

The generated zip file can be:
1. Uploaded to GitHub releases
2. Shared directly with users
3. Submitted to Blender addon repositories

Users can install it directly in Blender via Edit > Preferences > Add-ons > Install. 