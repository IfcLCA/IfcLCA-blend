bl_info = {
    "name": "IfcLCA Integration",
    "author": "louistrue",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > IfcLCA Tab",
    "description": "Life Cycle Assessment for IFC models using IfcLCA",
    "warning": "",
    "doc_url": "https://github.com/IfcLCA",
    "category": "LCA",
}

# Only import bpy when running inside Blender
try:
    import bpy
    from bpy.props import StringProperty, EnumProperty, PointerProperty
    from bpy.types import PropertyGroup
    _BPY_AVAILABLE = True
except ImportError:
    _BPY_AVAILABLE = False
    # For testing purposes, create dummy bpy module
    import sys
    if 'pytest' in sys.modules:
        from tests.mock_bpy import MockBpy
        bpy = MockBpy()

import logging
import sys

# Set up global logger for IfcLCA
def setup_ifclca_logger():
    """Set up logging for IfcLCA that outputs to Blender's console"""
    logger = logging.getLogger('IfcLCA')
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('[IfcLCA] %(levelname)s: %(message)s')
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger

def get_ifclca_logger():
    """Get the IfcLCA logger - useful for console debugging"""
    return logging.getLogger('IfcLCA')

# Initialize logger
_logger = setup_ifclca_logger()

# Import our modules - handle relative imports carefully
if _BPY_AVAILABLE:
    # Normal Blender imports
    from . import panels
    from . import operators
    from . import properties
else:
    # For testing, use absolute imports
    try:
        import panels
        import operators  
        import properties
    except ImportError:
        # If that fails, we're probably in a test environment
        # where the modules aren't importable
        panels = None
        operators = None
        properties = None

# Module reload support for development
if _BPY_AVAILABLE and "bpy" in locals():
    import importlib
    if panels:
        importlib.reload(panels)
    if operators:
        importlib.reload(operators)
    if properties:
        importlib.reload(properties)

classes = []

def register():
    """Register all classes and properties"""
    if not _BPY_AVAILABLE or not all([panels, operators, properties]):
        return
        
    # Register property classes first
    for cls in properties.classes:
        bpy.utils.register_class(cls)
        
    # Register operators
    for cls in operators.classes:
        bpy.utils.register_class(cls)
        
    # Register panels
    for cls in panels.classes:
        bpy.utils.register_class(cls)
    
    # Register property groups
    bpy.types.Scene.ifclca_props = PointerProperty(type=properties.IfcLCAProperties)
    
    # Make logger available in console
    bpy.ifclca_logger = get_ifclca_logger()
    
    _logger.info("IfcLCA Integration add-on registered")
    print("IfcLCA Integration add-on registered")
    print("Access logger in console with: bpy.ifclca_logger.info('your message')")

def unregister():
    """Unregister all classes and properties"""
    if not _BPY_AVAILABLE or not all([panels, operators, properties]):
        return
        
    # Unregister in reverse order
    for cls in reversed(panels.classes):
        bpy.utils.unregister_class(cls)
        
    for cls in reversed(operators.classes):
        bpy.utils.unregister_class(cls)
        
    for cls in reversed(properties.classes):
        bpy.utils.unregister_class(cls)
    
    # Remove property groups
    del bpy.types.Scene.ifclca_props
    
    # Remove logger from bpy
    if hasattr(bpy, 'ifclca_logger'):
        del bpy.ifclca_logger
    
    _logger.info("IfcLCA Integration add-on unregistered")
    print("IfcLCA Integration add-on unregistered")

if __name__ == "__main__" and _BPY_AVAILABLE:
    register() 