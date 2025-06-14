"""
Blender properties for IfcLCA integration

Defines custom properties for storing LCA data and UI state
"""

try:
    import bpy
    from bpy.props import (
        StringProperty,
        FloatProperty,
        EnumProperty,
        CollectionProperty,
        IntProperty,
        BoolProperty
    )
    from bpy.types import PropertyGroup
except ImportError:
    # For testing, use mock
    from unittest.mock import MagicMock
    PropertyGroup = type
    StringProperty = MagicMock()
    FloatProperty = MagicMock()
    EnumProperty = MagicMock()
    CollectionProperty = MagicMock()
    IntProperty = MagicMock()
    BoolProperty = MagicMock()


class MaterialResult(PropertyGroup):
    """Property group for storing material LCA results"""
    name: StringProperty(name="Material Name")
    volume: FloatProperty(name="Volume", unit='VOLUME')
    mass: FloatProperty(name="Mass", unit='MASS')
    carbon: FloatProperty(name="Carbon", unit='MASS')


class MaterialMapping(PropertyGroup):
    """Property group for material mapping"""
    ifc_material_name: StringProperty(name="IFC Material")
    database_id: StringProperty(name="Database Material ID")
    database_name: StringProperty(name="Database Material Name")
    is_mapped: BoolProperty(name="Is Mapped", default=False)
    carbon_per_unit: FloatProperty(name="Carbon per Unit")
    density: FloatProperty(name="Density")


class IfcLCAProperties(PropertyGroup):
    """Main property group for IfcLCA"""
    
    # IFC file settings
    ifc_file_path: StringProperty(
        name="IFC File",
        description="Path to IFC file",
        subtype='FILE_PATH',
        default=""
    )
    
    ifc_loaded: BoolProperty(
        name="IFC Loaded",
        description="Whether an IFC file is currently loaded",
        default=False
    )
    
    # Database settings
    database_type: EnumProperty(
        name="Database Type",
        description="Environmental database to use",
        items=[
            ('KBOB', "KBOB (Swiss)", "Swiss KBOB database"),
            ('OKOBAUDAT', "ÖKOBAUDAT (German)", "German ÖKOBAUDAT database"),
            ('CUSTOM', "Custom", "Custom JSON database")
        ],
        default='KBOB'
    )
    
    kbob_data_path: StringProperty(
        name="KBOB Data Path",
        description="Path to KBOB data directory or file",
        subtype='DIR_PATH',
        default=""
    )
    
    okobaudat_csv_path: StringProperty(
        name="ÖKOBAUDAT CSV File",
        description="Path to ÖKOBAUDAT CSV file",
        subtype='FILE_PATH',
        default=""
    )
    
    database_file: StringProperty(
        name="Database File",
        description="Path to database file (for ÖKOBAUDAT CSV or custom JSON)",
        subtype='FILE_PATH',
        default=""
    )
    
    # Results
    total_carbon: FloatProperty(
        name="Total Carbon",
        description="Total embodied carbon (kg CO2-eq)",
        default=0.0,
        unit='MASS'
    )
    
    results_text: StringProperty(
        name="Results Text",
        description="Formatted results text",
        default=""
    )
    results_json: StringProperty(
        name="Results JSON",
        description="Analysis results in JSON",
        default="",
    )

    
    show_results: BoolProperty(
        name="Show Results",
        description="Whether to show results panel",
        default=False
    )
    
    # Material collections
    materials: CollectionProperty(type=MaterialResult)
    material_mappings: CollectionProperty(type=MaterialMapping)
    
    # UI state
    selected_material_index: IntProperty(default=0)
    selected_mapping_index: IntProperty(default=0)
    active_mapping_index: IntProperty(default=0)
    filter_mapped: BoolProperty(
        name="Show Mapped Only",
        description="Show only mapped materials",
        default=False
    )
    
    # Element filter settings
    filter_ifc_class: EnumProperty(
        name="IFC Class Filter",
        description="Filter elements by IFC class",
        items=[
            ('ALL', "All Elements", "Include all IFC elements"),
            ('IfcWall', "Walls", "Only walls"),
            ('IfcSlab', "Slabs", "Only slabs"),
            ('IfcColumn', "Columns", "Only columns"),
            ('IfcBeam', "Beams", "Only beams"),
            ('IfcWindow', "Windows", "Only windows"),
            ('IfcDoor', "Doors", "Only doors"),
        ],
        default='ALL'
    )
    
    filter_building_storey: StringProperty(
        name="Building Storey",
        description="Filter by building storey name (leave empty for all)",
        default=""
    )
    
    # Analysis options
    include_openings: BoolProperty(
        name="Include Openings",
        description="Include windows and doors in analysis",
        default=False
    )
    
    use_net_volumes: BoolProperty(
        name="Use Net Volumes",
        description="Use net volumes instead of gross volumes where available",
        default=False
    )


# List of classes for registration
classes = [
    MaterialResult,
    MaterialMapping,
    IfcLCAProperties
] 