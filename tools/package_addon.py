#!/usr/bin/env python3
"""
Package IfcLCA-blend addon for distribution

Usage:
    python3 package_addon.py
    
    OR
    
    ./package.sh
    
This will create a timestamped zip file ready for distribution.
"""
import os
import zipfile
from datetime import datetime
from pathlib import Path

# Files and directories to exclude
EXCLUDE_PATTERNS = {
    '__pycache__',
    '.pyc',
    '.pyo',
    '.DS_Store',
    'htmlcov',
    '.pytest_cache',
    '.coverage',
    '*.egg-info',
    'test_results.log',
    'test_*.py',  # Exclude test files
    'debug_*.py',  # Exclude debug scripts
    '.git',
    '.gitignore',
    'tests/',  # Test directory
    'tools/',  # Build tools directory
    '.github/', # GitHub specific files
    '*.zip',   # Exclude zip files
}

def should_include(file_path: Path) -> bool:
    """Check if a file should be included in the zip"""
    import fnmatch
    
    # Check file name patterns
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith('*.'):
            # File extension check
            if file_path.suffix == pattern[1:]:
                return False
        elif pattern.endswith('/'):
            # Directory check
            if pattern[:-1] in file_path.parts:
                return False
        elif '*' in pattern or '?' in pattern:
            # Wildcard pattern matching
            if fnmatch.fnmatch(file_path.name, pattern):
                return False
        else:
            # Name pattern check
            if pattern in str(file_path):
                return False
            # Exact filename match
            if file_path.name == pattern:
                return False
    
    return True

def create_addon_zip():
    """Create a zip file of the IfcLCA-blend addon"""
    # Get timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d")
    zip_filename = f"IfcLCA-blend_{timestamp}.zip"
    
    # Base directory for the addon (parent of tools directory)
    addon_dir = Path(__file__).parent.parent
    
    if not addon_dir.exists():
        print(f"Error: {addon_dir} directory not found!")
        return
    
    print(f"Creating {zip_filename}...")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the addon directory
        for root, dirs, files in os.walk(addon_dir):
            root_path = Path(root)
            
            # Skip excluded directories
            dirs[:] = [d for d in dirs if should_include(root_path / d)]
            
            for file in files:
                file_path = root_path / file
                
                if should_include(file_path):
                    # Handle the new structure - map src/ files to root of addon
                    if "src/" in str(file_path):
                        # Map src/ files to the root of the addon in the zip
                        rel_path = file_path.relative_to(addon_dir / "src")
                        arcname = Path("IfcLCA-blend") / rel_path
                    else:
                        # Keep other files in their relative positions
                        arcname = Path("IfcLCA-blend") / file_path.relative_to(addon_dir)
                    
                    # No special file renaming needed
                    
                    print(f"  Adding: {arcname}")
                    zipf.write(file_path, arcname)
    
    # Get file size
    size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
    print(f"\n✅ Created {zip_filename} ({size_mb:.2f} MB)")
    
    # List what's included
    print("\nIncluded files:")
    with zipfile.ZipFile(zip_filename, 'r') as zipf:
        namelist = sorted(zipf.namelist())
        for name in namelist[:20]:  # Show first 20 files
            print(f"  - {name}")
        if len(namelist) > 20:
            print(f"  ... and {len(namelist) - 20} more files")
    
    print(f"\nTotal files: {len(namelist)}")

if __name__ == "__main__":
    create_addon_zip() 