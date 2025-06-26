# Bundled Dependencies

This directory contains bundled Python wheels for the `requests` module and its dependencies, allowing Ökobaudat API functionality to work without requiring users to install packages in Blender.

## Contents

- `requests-2.32.4-py3-none-any.whl` - HTTP library for API calls
- `certifi-2025.6.15-py3-none-any.whl` - SSL certificate bundle
- `charset_normalizer-3.4.2-py3-none-any.whl` - Character encoding detection
- `idna-3.10-py3-none-any.whl` - Internationalized Domain Names support
- `urllib3-2.5.0-py3-none-any.whl` - HTTP client library

## Implementation

The `__init__.py` file in this directory handles:
1. Extracting wheels to a temporary directory
2. Adding the directory to Python's path
3. Making `requests` available for import

This approach follows Blender's addon guidelines:
- Self-contained: No external pip installations required
- Bundled modules: All dependencies are included as wheels
- No global changes: Modules are loaded into addon's namespace only

## Compatibility

All wheels are pure Python (platform-independent) to ensure maximum compatibility across different operating systems and Blender installations. 