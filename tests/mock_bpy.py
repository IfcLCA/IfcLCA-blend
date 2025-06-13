"""
Mock Blender API (bpy) for testing

Provides minimal mock implementation of Blender's API
"""

from unittest.mock import MagicMock, Mock
import sys


class MockPropertyGroup:
    """Mock for bpy.types.PropertyGroup"""
    pass


class MockOperator:
    """Mock for bpy.types.Operator"""
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return self.execute(context)
    
    report = Mock()


class MockPanel:
    """Mock for bpy.types.Panel"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    
    @classmethod
    def poll(cls, context):
        return True


class MockContext:
    """Mock Blender context"""
    def __init__(self):
        self.scene = MockScene()
        self.object = None
        self.selected_objects = []
        self.view_layer = Mock()
        self.area = Mock()
        self.space_data = Mock()


class MockScene:
    """Mock Blender scene"""
    def __init__(self):
        self.ifclca_props = MockIfcLCAProperties()
        self.BIMProperties = MockBIMProperties()


class MockIfcLCAProperties:
    """Mock IfcLCA properties"""
    def __init__(self):
        self.ifc_file = ""
        self.database_type = 'KBOB'
        self.database_file = ""
        self.total_carbon = 0.0
        self.materials = []
        self.material_mapping = []
        self.selected_material_index = 0
        self.selected_mapping_index = 0


class MockBIMProperties:
    """Mock BIM properties"""
    def __init__(self):
        self.ifc_file = ""


class MockBpy:
    """Mock bpy module"""
    
    @classmethod
    def setup(cls):
        """Set up the mock bpy module in sys.modules"""
        mock_bpy = cls()
        sys.modules['bpy'] = mock_bpy
        sys.modules['bpy.types'] = mock_bpy.types
        sys.modules['bpy.props'] = mock_bpy.props
        sys.modules['bpy_extras'] = type(sys)('bpy_extras')
        sys.modules['bpy_extras.io_utils'] = type(sys)('io_utils')
    
    def __init__(self):
        self.context = MockContext()
        # Set up nested classes as attributes
        self.types = self.Types()
        self.props = self.Props()
        self.data = self.Data()
        self.ops = self.Ops()
        self.utils = self.Utils()
        self.path = self.Path()
    
    class Types:
        PropertyGroup = MockPropertyGroup
        Operator = MockOperator
        Panel = MockPanel
        Scene = Mock()
        
    class Props:
        StringProperty = Mock()
        EnumProperty = Mock()
        FloatProperty = Mock()
        CollectionProperty = Mock()
        IntProperty = Mock()
        PointerProperty = Mock()
        BoolProperty = Mock()
        
    class Utils:
        register_class = Mock()
        unregister_class = Mock()
        
    class Ops:
        mesh = Mock()
        object = Mock()
        
    class Data:
        def __init__(self):
            self.objects = {}
            self.scenes = [MockScene()]
        
    class Path:
        @staticmethod
        def abspath(path):
            return path


class MockBonsaiBIM:
    """Mock BonsaiBIM module"""
    
    class bim:
        class ifc:
            IfcStore = Mock()
            IfcStore.get_file = Mock(return_value=None)
            
    class core:
        class geometry:
            @staticmethod
            def get_element_quantity(element, quantity_name):
                """Mock quantity getter"""
                quantities = {
                    'GrossVolume': 3.6,  # Default volume
                    'NetVolume': 3.4,
                    'GrossArea': 100.0,
                    'NetArea': 95.0
                }
                return quantities.get(quantity_name, 0.0)


class MockIfcOpenShell:
    """Mock ifcopenshell module"""
    
    @staticmethod
    def open(filepath):
        """Mock IFC file opening"""
        return Mock()
    
    class util:
        class element:
            @staticmethod
            def get_material(element):
                """Mock material getter"""
                return Mock()
            
            @staticmethod
            def get_psets(element, psets_only=False, qtos_only=False):
                """Mock property set getter"""
                if qtos_only:
                    return {
                        'BaseQuantities': {
                            'GrossVolume': 3.6,
                            'GrossSideArea': 12.0
                        }
                    }
                return {}
    
    class api:
        @staticmethod
        def run(*args, **kwargs):
            return Mock()


def setup_mock_modules():
    """Setup mock modules in sys.modules"""
    sys.modules['bpy'] = MockBpy()
    sys.modules['bonsaibim'] = MockBonsaiBIM()
    sys.modules['ifcopenshell'] = MockIfcOpenShell()
    sys.modules['ifcopenshell.util'] = MockIfcOpenShell.util
    sys.modules['ifcopenshell.util.element'] = MockIfcOpenShell.util.element
    sys.modules['ifcopenshell.api'] = MockIfcOpenShell.api
    sys.modules['bonsaibim.bim'] = MockBonsaiBIM.bim
    sys.modules['bonsaibim.bim.ifc'] = MockBonsaiBIM.bim.ifc
    sys.modules['bonsaibim.core'] = MockBonsaiBIM.core
    sys.modules['bonsaibim.core.geometry'] = MockBonsaiBIM.core.geometry
    
    # Return references for use in tests
    return MockBpy(), MockBonsaiBIM(), MockIfcOpenShell()


def cleanup_mock_modules():
    """Remove mock modules from sys.modules"""
    mock_modules = [
        'bpy',
        'bonsaibim',
        'bonsaibim.bim',
        'bonsaibim.bim.ifc',
        'bonsaibim.core',
        'bonsaibim.core.geometry',
        'ifcopenshell',
        'ifcopenshell.util',
        'ifcopenshell.util.element',
        'ifcopenshell.api'
    ]
    
    for module in mock_modules:
        if module in sys.modules:
            del sys.modules[module] 