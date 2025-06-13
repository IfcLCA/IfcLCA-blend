"""
Pytest configuration for IfcLCA-blend tests
"""
import sys
import os
from pathlib import Path

# Add the parent directory (IfcLCA-blend) to sys.path so we can import the addon modules
addon_dir = Path(__file__).parent.parent
if str(addon_dir) not in sys.path:
    sys.path.insert(0, str(addon_dir))

# Add tests directory to path as well
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))

# Mock bpy before any imports
from tests.mock_bpy import MockBpy
MockBpy.setup()

# Now we can import bpy safely
import bpy

# Mock ifcopenshell if not available
try:
    import ifcopenshell
except ImportError:
    # Create a mock ifcopenshell module
    class MockIfcOpenShell:
        def open(self, filepath):
            return MockIFC()
            
    class MockIFC:
        def by_type(self, type_name):
            return []
            
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
            
    sys.modules['ifcopenshell'] = MockIfcOpenShell()
    
# Mock bonsai if not available
try:
    import bonsai
except ImportError:
    from unittest.mock import MagicMock
    sys.modules['bonsai'] = MagicMock()
    sys.modules['bonsai.bim'] = MagicMock()
    sys.modules['bonsai.bim.tool'] = MagicMock() 

# Add test fixtures here if needed 