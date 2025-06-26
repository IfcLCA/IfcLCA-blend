"""
Bundled dependencies loader for IfcLCA-blend

This module handles loading bundled Python dependencies in a way that's
compatible with Blender's addon guidelines.
"""

import sys
import os
import zipfile
import importlib
import logging

logger = logging.getLogger('IfcLCA')

# Get the directory containing our bundled wheels
LIBS_DIR = os.path.dirname(os.path.abspath(__file__))

# Track loaded modules to avoid duplicates
_loaded_modules = set()


def load_bundled_wheel(wheel_filename, module_name):
    """Load a module from a bundled wheel file"""
    wheel_path = os.path.join(LIBS_DIR, wheel_filename)
    
    if not os.path.exists(wheel_path):
        logger.error(f"Wheel file not found: {wheel_path}")
        return None
    
    # Check if already loaded
    if module_name in _loaded_modules:
        return sys.modules.get(module_name)
    
    # Create a unique namespace for this addon's dependencies
    addon_namespace = f"ifclca_libs.{module_name}"
    
    # Check if already in sys.modules under our namespace
    if addon_namespace in sys.modules:
        _loaded_modules.add(module_name)
        return sys.modules[addon_namespace]
    
    try:
        # Extract wheel to memory and load
        with zipfile.ZipFile(wheel_path, 'r') as wheel:
            # Get the module directory from the wheel
            module_dirs = [name for name in wheel.namelist() 
                         if name.startswith(f"{module_name}/") or name == f"{module_name}.py"]
            
            if not module_dirs:
                logger.error(f"Module {module_name} not found in wheel {wheel_filename}")
                return None
            
            # Create a temporary import hook
            class WheelImporter:
                def __init__(self, wheel_file, prefix=""):
                    self.wheel = wheel_file
                    self.prefix = prefix
                
                def find_module(self, fullname, path=None):
                    if fullname.startswith(self.prefix):
                        return self
                    return None
                
                def load_module(self, fullname):
                    if fullname in sys.modules:
                        return sys.modules[fullname]
                    
                    # Remove prefix to get actual module name
                    actual_name = fullname[len(self.prefix)+1:] if self.prefix else fullname
                    
                    # Try to find the module in the wheel
                    module_path = actual_name.replace('.', '/') + '.py'
                    init_path = actual_name.replace('.', '/') + '/__init__.py'
                    
                    module_data = None
                    is_package = False
                    
                    try:
                        module_data = self.wheel.read(module_path)
                    except KeyError:
                        try:
                            module_data = self.wheel.read(init_path)
                            is_package = True
                        except KeyError:
                            raise ImportError(f"Cannot find module {actual_name}")
                    
                    # Create module
                    module = importlib.util.module_from_spec(
                        importlib.util.spec_from_loader(fullname, loader=None)
                    )
                    
                    # Set module attributes
                    module.__file__ = f"<wheel:{wheel_filename}:{module_path}>"
                    module.__loader__ = self
                    if is_package:
                        module.__path__ = [f"<wheel:{wheel_filename}:{actual_name}>"]
                        module.__package__ = fullname
                    else:
                        module.__package__ = fullname.rpartition('.')[0]
                    
                    # Execute module code
                    sys.modules[fullname] = module
                    exec(module_data, module.__dict__)
                    
                    return module
            
            # Install our importer temporarily
            importer = WheelImporter(wheel, "ifclca_libs")
            sys.meta_path.insert(0, importer)
            
            try:
                # Import the module under our namespace
                imported_module = importlib.import_module(addon_namespace)
                _loaded_modules.add(module_name)
                
                # Also make it available under the simple name within our package
                sys.modules[f"ifclca_libs.{module_name}"] = imported_module
                
                return imported_module
            finally:
                # Remove our importer
                sys.meta_path.remove(importer)
                
    except Exception as e:
        logger.error(f"Failed to load bundled module {module_name}: {e}")
        return None


def ensure_requests_available():
    """Ensure the requests module and its dependencies are available"""
    
    # Define dependencies in order
    dependencies = [
        ("certifi-2025.6.15-py3-none-any.whl", "certifi"),
        ("idna-3.10-py3-none-any.whl", "idna"),
        ("urllib3-2.5.0-py3-none-any.whl", "urllib3"),
        ("charset_normalizer-3.4.2-py3-none-any.whl", "charset_normalizer"),
        ("requests-2.32.4-py3-none-any.whl", "requests"),
    ]
    
    # Load each dependency
    for wheel_file, module_name in dependencies:
        module = load_bundled_wheel(wheel_file, module_name)
        if module is None:
            return False
    
    return True


# Simple approach: extract and add to path (fallback method)
def _simple_load_wheels():
    """Simple fallback method: extract wheels to a temporary directory"""
    import tempfile
    
    # Create a temporary directory for extracted modules
    temp_dir = tempfile.mkdtemp(prefix="ifclca_libs_")
    
    # List of wheel files
    wheels = [
        "certifi-2025.6.15-py3-none-any.whl",
        "idna-3.10-py3-none-any.whl",
        "urllib3-2.5.0-py3-none-any.whl",
        "charset_normalizer-3.4.2-py3-none-any.whl",
        "requests-2.32.4-py3-none-any.whl",
    ]
    
    # Extract all wheels
    for wheel_file in wheels:
        wheel_path = os.path.join(LIBS_DIR, wheel_file)
        if os.path.exists(wheel_path):
            with zipfile.ZipFile(wheel_path, 'r') as zf:
                zf.extractall(temp_dir)
    
    # Add to Python path (at the beginning to take precedence)
    if temp_dir not in sys.path:
        sys.path.insert(0, temp_dir)
    
    return temp_dir


# Try simple loading on import
_temp_libs_dir = None
try:
    _temp_libs_dir = _simple_load_wheels()
    import requests
    HAS_REQUESTS = True
except Exception as e:
    logger.warning(f"Failed to load bundled requests module: {e}")
    HAS_REQUESTS = False 