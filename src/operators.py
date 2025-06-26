try:
    import bpy
    from bpy.types import Operator
    from bpy.props import StringProperty, EnumProperty, IntProperty
    from bpy_extras.io_utils import ImportHelper
except ImportError:
    # For testing
    from unittest.mock import MagicMock
    
    # Create distinct base classes for mocking
    class MockOperator:
        pass
    
    class MockImportHelper:
        pass
    
    Operator = MockOperator
    ImportHelper = MockImportHelper
    StringProperty = MagicMock()
    EnumProperty = MagicMock()

import os
import logging
import sys
import json

# Set up logging for Blender console
def setup_logging():
    """Set up logging to output to Blender's console"""
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

# Initialize logger
logger = setup_logging()

try:
    import ifcopenshell
except ImportError:
    ifcopenshell = None
    logger.error("ifcopenshell not available - IFC functionality will be limited")

# Try relative imports first (when used as addon)
try:
    from .ifclca_core import get_database_reader as get_core_database_reader
    from .logic import IfcMaterialExtractor, run_lca_analysis, format_results
except ImportError:
    # Fallback to absolute imports (for testing)
    from .ifclca_core import get_database_reader as get_core_database_reader
    from .logic import IfcMaterialExtractor, run_lca_analysis, format_results

# Import the extended database reader that supports OKOBAUDAT_API
try:
    from .database_reader import get_extended_database_reader
except ImportError:
    from .database_reader import get_extended_database_reader



# Try to import Bonsai tools if available
try:
    from bonsai.bim.ifc import IfcStore
    HAS_BONSAI = True
    logger.info("Bonsai tools available")
except ImportError:
    HAS_BONSAI = False
    logger.warning("Bonsai tools not available - some features will be limited")

# Global storage for IFC file (could also use Bonsai's IfcStore)
_ifc_file = None
_web_server = None

# Global cache for Ökobaudat materials
class OkobaudatCache:
    """Simple cache manager for Ökobaudat material data"""
    def __init__(self):
        self.cache = {}  # material_id -> full_data
        self.last_query = ""
        self.last_results = []
        
    def get(self, material_id):
        """Get cached material data"""
        return self.cache.get(material_id)
    
    def set(self, material_id, data):
        """Cache material data"""
        self.cache[material_id] = data
        
    def has(self, material_id):
        """Check if material is cached"""
        return material_id in self.cache
    
    def clear(self):
        """Clear all cached data"""
        self.cache.clear()
        self.last_query = ""
        self.last_results = []
        
    def get_query_results(self, query):
        """Get cached query results"""
        if query == self.last_query:
            return self.last_results
        return None
    
    def set_query_results(self, query, results):
        """Cache query results"""
        self.last_query = query
        self.last_results = results

# Initialize global cache
_okobaudat_cache = OkobaudatCache()


def safe_float(value, default=0.0):
    """Safely convert a value to float, handling None and other edge cases"""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        logger.debug(f"Could not convert {value} to float, using default {default}")
        return default


class IFCLCA_OT_LoadIFC(Operator, ImportHelper):
    """Load an IFC file for LCA analysis"""
    bl_idname = "ifclca.load_ifc"
    bl_label = "Load IFC File"
    bl_description = "Load an IFC file for life cycle assessment"
    bl_options = {'REGISTER', 'UNDO'}
    
    # File browser filter
    filter_glob: StringProperty(
        default="*.ifc;*.ifczip",
        options={'HIDDEN'}
    )
    
    def execute(self, context):
        global _ifc_file
        props = context.scene.ifclca_props
        
        if not ifcopenshell:
            logger.error("ifcopenshell not available")
            self.report({'ERROR'}, "ifcopenshell not available")
            return {'CANCELLED'}
        
        try:
            # Load the IFC file
            logger.info(f"Loading IFC file: {self.filepath}")
            _ifc_file = ifcopenshell.open(self.filepath)
            
            # Log IFC file info
            logger.info(f"IFC Schema: {_ifc_file.schema}")
            
            # Check for basic IFC structure
            projects = _ifc_file.by_type("IfcProject")
            logger.info(f"Found {len(projects)} IfcProject(s)")
            
            sites = _ifc_file.by_type("IfcSite")
            logger.info(f"Found {len(sites)} IfcSite(s)")
            
            buildings = _ifc_file.by_type("IfcBuilding")
            logger.info(f"Found {len(buildings)} IfcBuilding(s)")
            
            elements = _ifc_file.by_type("IfcElement")
            logger.info(f"Found {len(elements)} IfcElement(s)")
            
            # Check for geometric representations
            representations = _ifc_file.by_type("IfcShapeRepresentation")
            logger.info(f"Found {len(representations)} geometric representations")
            
            # Update properties
            props.ifc_file_path = self.filepath
            props.ifc_loaded = True
            
            # Clear existing material mappings
            props.material_mappings.clear()
            
            # Extract materials from the IFC file
            logger.info("Extracting materials from IFC file...")
            extractor = IfcMaterialExtractor(_ifc_file)
            materials = extractor.get_all_materials()
            
            logger.info(f"Found {len(materials)} unique materials")
            
            # Create material mapping entries
            for material_name, count in materials:
                logger.debug(f"Material: {material_name} used by {count} elements")
                item = props.material_mappings.add()
                item.ifc_material_name = material_name
                item.database_id = ""
                item.database_name = ""
                item.is_mapped = False
            
            # Diagnostic checks
            if len(elements) == 0:
                logger.warning("No IfcElements found - file may be empty or corrupt")
                self.report({'WARNING'}, "No IFC elements found in file")
            
            if len(representations) == 0:
                logger.warning("No geometric representations found - elements may not be visible")
                self.report({'WARNING'}, "No geometric representations found")
            
            self.report({'INFO'}, f"Loaded IFC file with {len(materials)} materials and {len(elements)} elements")
            logger.info("IFC file loaded successfully")
            return {'FINISHED'}
            
        except Exception as e:
            logger.error(f"Failed to load IFC file: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.report({'ERROR'}, f"Failed to load IFC file: {str(e)}")
            return {'CANCELLED'}


class IFCLCA_OT_UseActiveIFC(Operator):
    """Use the currently active IFC file from Bonsai"""
    bl_idname = "ifclca.use_active_ifc"
    bl_label = "Use Active IFC"
    bl_description = "Use the IFC file currently loaded in Bonsai"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return HAS_BONSAI
    
    def execute(self, context):
        global _ifc_file
        props = context.scene.ifclca_props
        
        if not HAS_BONSAI:
            logger.error("Bonsai is not available")
            self.report({'ERROR'}, "Bonsai is not available")
            return {'CANCELLED'}
        
        try:
            # Get IFC file from Bonsai using IfcStore
            logger.info("Getting active IFC file from Bonsai")
            ifc = IfcStore.get_file()
            
            # Debug: Check what we got
            logger.debug(f"IFC object type: {type(ifc)}")
            logger.debug(f"IFC object: {ifc}")
            
            if not ifc:
                logger.error("No IFC file is currently loaded in Bonsai")
                self.report({'ERROR'}, "No IFC file is currently loaded in Bonsai")
                return {'CANCELLED'}
            
            _ifc_file = ifc
            
            # Log IFC file info
            logger.info(f"Active IFC Schema: {_ifc_file.schema}")
            
            # Check for basic IFC structure
            projects = _ifc_file.by_type("IfcProject")
            logger.info(f"Found {len(projects)} IfcProject(s)")
            
            elements = _ifc_file.by_type("IfcElement")
            logger.info(f"Found {len(elements)} IfcElement(s)")
            
            # Check for geometric representations
            representations = _ifc_file.by_type("IfcShapeRepresentation")
            logger.info(f"Found {len(representations)} geometric representations")
            
            # Update properties
            props.ifc_file_path = "Active Bonsai IFC"
            props.ifc_loaded = True
            
            # Clear existing material mappings
            props.material_mappings.clear()
            
            # Extract materials from the IFC file
            logger.info("Extracting materials from active IFC file...")
            extractor = IfcMaterialExtractor(_ifc_file)
            materials = extractor.get_all_materials()
            
            logger.info(f"Found {len(materials)} unique materials")
            
            # Create material mapping entries
            for material_name, count in materials:
                logger.debug(f"Material: {material_name} used by {count} elements")
                item = props.material_mappings.add()
                item.ifc_material_name = material_name
                item.database_id = ""
                item.database_name = ""
                item.is_mapped = False
            
            # Diagnostic checks
            if len(elements) == 0:
                logger.warning("No IfcElements found in active IFC - file may be empty")
                self.report({'WARNING'}, "No IFC elements found")
            
            if len(representations) == 0:
                logger.warning("No geometric representations found - elements may not be visible")
                self.report({'WARNING'}, "No geometric representations found")
            
            self.report({'INFO'}, f"Using active IFC with {len(materials)} materials and {len(elements)} elements")
            logger.info("Active IFC loaded successfully")
            return {'FINISHED'}
            
        except Exception as e:
            logger.error(f"Failed to get active IFC: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.report({'ERROR'}, f"Failed to get active IFC: {str(e)}")
            return {'CANCELLED'}


class IFCLCA_OT_SortMaterialDatabase(Operator):
    """Sort material database by column"""
    bl_idname = "ifclca.sort_material_database"
    bl_label = "Sort Materials"
    bl_description = "Sort material database by this column"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    column: StringProperty()
    
    def execute(self, context):
        props = context.scene.ifclca_props
        
        # Toggle sort direction if clicking same column
        if props.material_sort_column == self.column:
            props.material_sort_reverse = not props.material_sort_reverse
        else:
            props.material_sort_column = self.column
            props.material_sort_reverse = False
            
        return {'FINISHED'}


class IFCLCA_OT_BrowseMaterials(Operator):
    """Browse and select materials from database"""
    bl_idname = "ifclca.browse_materials"
    bl_label = "Browse Materials"
    bl_description = "Browse and select a material from the database"
    bl_options = {'REGISTER', 'UNDO'}
    
    material_index: StringProperty()
    search_query: StringProperty(
        name="Search",
        description="Search for materials",
        default=""
    )
    
    @staticmethod
    def is_valid_material_name(name):
        """Check if material name is valid (not corrupted)"""
        if not name or len(name) < 2:
            return False
        
        # Count weird characters
        weird_chars = 0
        for char in name:
            # Check for control characters and weird symbols
            if ord(char) < 32 or char in '¤¶`^':
                weird_chars += 1
            # Check for specific weird patterns
            if '*a' in name or '+I' in name:
                return False
        
        # If more than 20% weird chars, skip
        if weird_chars > len(name) * 0.2:
            return False
        
        # Must have at least one normal letter
        if not any(c.isalpha() for c in name):
            return False
            
        return True
    
    def invoke(self, context, event):
        # Load materials into the collection
        props = context.scene.ifclca_props
        
        # Clear existing
        if hasattr(context.scene, 'ifclca_material_database'):
            context.scene.ifclca_material_database.clear()
        
        try:
            # Get database reader
            if props.database_type == 'KBOB':
                db_reader = get_core_database_reader('KBOB', props.kbob_data_path)
            elif props.database_type == 'OKOBAUDAT_API':
                from .database_reader import HAS_REQUESTS
                if not HAS_REQUESTS:
                    self.report({'ERROR'}, "The 'requests' module could not be loaded. Ökobaudat API functionality is disabled.")
                    return {'CANCELLED'}
                
                # Check online access permission
                if hasattr(bpy.app, 'online_access') and not bpy.app.online_access:
                    self.report({'ERROR'}, "Online access is disabled. Enable 'Allow Online Access' in Preferences > System to use Ökobaudat API.")
                    return {'CANCELLED'}
                
                db_reader = get_extended_database_reader('OKOBAUDAT_API', props.okobaudat_api_key)
            else:
                self.report({'ERROR'}, "No database selected")
                return {'CANCELLED'}
            
            # Get all materials
            all_materials = db_reader.get_all_materials()
            
            # For OKOBAUDAT_API, limit initial load to prevent slowness
            if props.database_type == 'OKOBAUDAT_API' and len(all_materials) == 0:
                # Check cache first
                cached_results = _okobaudat_cache.get_query_results("")
                if cached_results:
                    all_materials = cached_results
                    logger.info("Using cached default materials")
                else:
                    # Initial load - just get a reasonable default set
                    db_reader.load_materials(limit=50)
                    all_materials = db_reader.get_all_materials()
                    _okobaudat_cache.set_query_results("", all_materials)
            
            # Clear existing materials before adding new ones
            context.scene.ifclca_material_database.clear()
            
            valid_count = 0
            for mat in all_materials:
                name = mat.get('name', '')
                # Use the same validation
                if self.is_valid_material_name(name):
                    # For OKOBAUDAT_API, DON'T fetch full data here - too slow!
                    # Data will be fetched on-demand when needed
                    item = context.scene.ifclca_material_database.add()
                    item.material_id = mat.get('id', '')
                    item.name = name
                    item.category = mat.get('category', 'Uncategorized')
                    
                                    # Check if we have cached data for this material
                if props.database_type == 'OKOBAUDAT_API':
                    cached_data = _okobaudat_cache.get(item.material_id)
                    if cached_data:
                        item.gwp = safe_float(cached_data.get('carbon_per_unit'))
                        item.density = safe_float(cached_data.get('density'))
                    else:
                        item.gwp = safe_float(mat.get('gwp'))
                        item.density = safe_float(mat.get('density'))
                else:
                    item.gwp = safe_float(mat.get('gwp'))
                    item.density = safe_float(mat.get('density'))
                        
                    valid_count += 1
            
            # Force UI refresh
            for area in context.screen.areas:
                area.tag_redraw()
            
            logger.info(f"Loaded {valid_count} materials into browser")
            
            # Set initial selection to first item if available
            if valid_count > 0:
                context.scene.ifclca_material_database_index = 0
            
            # Show dialog
            wm = context.window_manager
            return wm.invoke_props_dialog(self, width=700)
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load materials: {str(e)}")
            return {'CANCELLED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.ifclca_props
        
        # Main header with integrated search label
        header_box = layout.box()
        header_col = header_box.column()
        
        # Title row
        title_row = header_col.row()
        title_row.label(text="Material Database Browser", icon='VIEWZOOM')
        # Only show impact indicators toggle for non-Ökobaudat databases
        if props.database_type != 'OKOBAUDAT_API':
            title_row.prop(props, "show_impact_indicators", text="", icon='WORLD')
        
        # API Search for Ökobaudat
        if props.database_type == 'OKOBAUDAT_API':
            header_col.separator()
            
            # Search instruction - moved here to be above the search field
            header_col.label(text="Search by material name or category:", icon='INFO')
            
            search_row = header_col.row(align=True)
            search_row.label(text="Search Ökobaudat:", icon='VIEWZOOM')
            search_row.prop(self, "search_query", text="", icon='NONE')
            search_op = search_row.operator("ifclca.search_okobaudat", text="Search", icon='VIEWZOOM')
            search_op.search_query = self.search_query
            
            # Info about EN 15804+A2 compliance
            header_col.label(text="Results filtered for EN 15804+A2 compliance", icon='INFO')
            
            # Info about on-demand loading
            info_box = header_col.box()
            info_box.scale_y = 0.8
            info_col = info_box.column()
            info_col.label(text="Data loads on-demand when you:", icon='INFO')
            info_col.label(text="    • Click on a material")
            info_col.label(text="    • Confirm material selection")
            
            # Cache status
            cache_row = info_col.row(align=True)
            cache_count = len(_okobaudat_cache.cache)
            if cache_count > 0:
                cache_row.label(text=f"{cache_count} materials cached", icon='FILE_CACHE')
                cache_row.operator("ifclca.clear_material_cache", text="Clear", icon='X')
            else:
                cache_row.label(text="No cached data", icon='FILE_CACHE')
        else:
            # For non-API databases, still show the search instruction
            header_col.label(text="Search by material name or category:", icon='INFO')
        
        # Impact legend (only if indicators are enabled and not using Ökobaudat)
        if props.show_impact_indicators and props.database_type != 'OKOBAUDAT_API':
            header_col.separator()
            legend_row = header_col.row()
            legend_row.scale_y = 0.7
            legend_row.label(text="Impact indicators:", icon='WORLD')
            sub_row = legend_row.row(align=True)
            sub_row.label(text="Best", icon='CHECKMARK')
            sub_row.label(text="Good", icon='INFO')
            sub_row.label(text="Fair", icon='ERROR')
            sub_row.label(text="Poor", icon='ORPHAN_DATA')
        
        # Clickable Table Headers
        headers_box = layout.box()
        headers_split = headers_box.split(factor=0.3)
        
        # Category header button
        cat_col = headers_split.column()
        cat_row = cat_col.row(align=True)
        cat_op = cat_row.operator("ifclca.sort_material_database", text="Category", emboss=False)
        cat_op.column = 'CATEGORY'
        
        # Add sort indicator as clickable button
        if props.material_sort_column == 'CATEGORY':
            sort_icon_op = cat_row.operator("ifclca.sort_material_database", text="▼" if props.material_sort_reverse else "▲", emboss=False)
            sort_icon_op.column = 'CATEGORY'
        else:
            sort_icon_op = cat_row.operator("ifclca.sort_material_database", text="♢", emboss=False)
            sort_icon_op.column = 'CATEGORY'
        
        # Name and data headers
        name_data_split = headers_split.split(factor=0.5)
        
        # Name header button
        name_col = name_data_split.column()
        name_row = name_col.row(align=True)
        name_op = name_row.operator("ifclca.sort_material_database", text="Material Name", emboss=False)
        name_op.column = 'NAME'
        
        # Add sort indicator as clickable button
        if props.material_sort_column == 'NAME':
            sort_icon_op = name_row.operator("ifclca.sort_material_database", text="▼" if props.material_sort_reverse else "▲", emboss=False)
            sort_icon_op.column = 'NAME'
        else:
            sort_icon_op = name_row.operator("ifclca.sort_material_database", text="♢", emboss=False)
            sort_icon_op.column = 'NAME'
        
        # Environmental data headers
        data_col = name_data_split.column()
        data_row = data_col.row(align=True)
        
        # GWP sort button
        gwp_op = data_row.operator("ifclca.sort_material_database", text="GWP", emboss=False)
        gwp_op.column = 'GWP'
        # Add sort indicator as clickable button
        if props.material_sort_column == 'GWP':
            sort_icon_op = data_row.operator("ifclca.sort_material_database", text="▼" if props.material_sort_reverse else "▲", emboss=False)
            sort_icon_op.column = 'GWP'
        else:
            sort_icon_op = data_row.operator("ifclca.sort_material_database", text="♢", emboss=False)
            sort_icon_op.column = 'GWP'
            
        # Density sort button
        density_op = data_row.operator("ifclca.sort_material_database", text="Density", emboss=False)
        density_op.column = 'DENSITY'
        # Add sort indicator as clickable button
        if props.material_sort_column == 'DENSITY':
            sort_icon_op = data_row.operator("ifclca.sort_material_database", text="▼" if props.material_sort_reverse else "▲", emboss=False)
            sort_icon_op.column = 'DENSITY'
        else:
            sort_icon_op = data_row.operator("ifclca.sort_material_database", text="♢", emboss=False)
            sort_icon_op.column = 'DENSITY'
        
        # Material list (search bar will appear at the top automatically)
        layout.template_list(
            "IFCLCA_UL_MaterialDatabaseList", "material_browser_list",
            context.scene, "ifclca_material_database",
            context.scene, "ifclca_material_database_index",
            rows=10,
            maxrows=10
        )
        
        # Selection details
        db = context.scene.ifclca_material_database
        idx = context.scene.ifclca_material_database_index
        
        if 0 <= idx < len(db):
            # Selection info box
            box = layout.box()
            col = box.column()
            
            # Selected material header
            row = col.row()
            row.label(text="Selected Material:", icon='FORWARD')
            
            # Material details in two columns
            split = col.split(factor=0.5)
            
            # Left column
            left = split.column()
            left.label(text=f"Name: {db[idx].name}")
            left.label(text=f"Category: {db[idx].category}")
            
            # Right column
            right = split.column()
            if db[idx].gwp > 0:
                right.label(text=f"GWP: {db[idx].gwp:.3f} kg CO₂/kg")
            else:
                if props.database_type == 'OKOBAUDAT_API':
                    row = right.row(align=True)
                    row.label(text="GWP: No data")
                    op = row.operator("ifclca.fetch_material_data", text="", icon='IMPORT')
                    op.material_index = idx
                else:
                    right.label(text="GWP: No data")
            if db[idx].density > 0:
                right.label(text=f"Density: {db[idx].density:.0f} kg/m³")
            else:
                right.label(text="Density: No data")
        else:
            # No selection
            box = layout.box()
            box.label(text="No material selected", icon='ERROR')
        
        # Footer with material count and shortcuts
        footer_box = layout.box()
        footer_col = footer_box.column()
        
        # Material count
        if hasattr(context.scene, 'ifclca_material_database'):
            total = len(context.scene.ifclca_material_database)
            footer_col.label(text=f"Total materials: {total}", icon='INFO')
        
        # Keyboard shortcuts
        footer_col.label(text="↑↓ Navigate • Enter to confirm • Esc to cancel", icon='HAND')
    
    def execute(self, context):
        props = context.scene.ifclca_props
        db = context.scene.ifclca_material_database
        idx = context.scene.ifclca_material_database_index
        
        # Check if any material is selected
        if idx < 0 or idx >= len(db):
            self.report({'WARNING'}, "Please select a material first")
            return {'CANCELLED'}
        
        try:
            # Get selected material
            selected = db[idx]
            mat_idx = int(self.material_index)
            mapping = props.material_mappings[mat_idx]
            
            # For OKOBAUDAT_API, fetch data if we don't have it yet
            if props.database_type == 'OKOBAUDAT_API' and selected.gwp == 0:
                self.report({'INFO'}, "Fetching material data...")
                db_reader = get_extended_database_reader('OKOBAUDAT_API', props.okobaudat_api_key)
                full_data = db_reader.get_full_material_data(selected.material_id)
                
                # Update with fetched data
                selected.gwp = safe_float(full_data.get('carbon_per_unit'))
                selected.density = safe_float(full_data.get('density'))
                
                if selected.gwp == 0:
                    self.report({'WARNING'}, "No GWP data available for this material")
            
            # Update mapping
            mapping.database_id = selected.material_id
            mapping.database_name = selected.name
            mapping.is_mapped = True
            
            # Clear the material database after successful selection
            context.scene.ifclca_material_database.clear()
            
            self.report({'INFO'}, f"✓ Material mapped to: {mapping.database_name}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to map material: {str(e)}")
            return {'CANCELLED'}


class IFCLCA_OT_RunAnalysis(Operator):
    """Run the LCA analysis on the loaded IFC file"""
    bl_idname = "ifclca.run_analysis"
    bl_label = "Calculate Embodied Carbon"
    bl_description = "Run life cycle assessment analysis on the IFC model"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        global _ifc_file
        props = context.scene.ifclca_props
        
        # Validate prerequisites
        if not props.ifc_loaded or not _ifc_file:
            self.report({'ERROR'}, "Please load an IFC file first")
            return {'CANCELLED'}
        
        # Check if any materials are mapped
        mapped_count = sum(1 for m in props.material_mappings if m.is_mapped)
        if mapped_count == 0:
            self.report({'ERROR'}, "Please map at least one material before running analysis")
            return {'CANCELLED'}
        
        try:
            # Get database reader
            if props.database_type == 'KBOB':
                db_reader = get_core_database_reader('KBOB', props.kbob_data_path)
            elif props.database_type == 'OKOBAUDAT_API':
                from .database_reader import HAS_REQUESTS
                if not HAS_REQUESTS:
                    self.report({'ERROR'}, "The 'requests' module could not be loaded. Ökobaudat API functionality is disabled.")
                    return {'CANCELLED'}
                db_reader = get_extended_database_reader('OKOBAUDAT_API', props.okobaudat_api_key)
            else:
                self.report({'ERROR'}, "Invalid database type")
                return {'CANCELLED'}
            
            # Build mapping dictionary
            mapping = {}
            for mat_mapping in props.material_mappings:
                if mat_mapping.is_mapped:
                    mapping[mat_mapping.ifc_material_name] = mat_mapping.database_id
            
            # Run analysis
            self.report({'INFO'}, "Running LCA analysis...")
            results, detailed_results = run_lca_analysis(_ifc_file, db_reader, mapping)
            
            # Add compatibility layer for web interface
            # The web interface expects 'total_carbon' but new analysis returns 'gwp'
            for material_name, details in detailed_results.items():
                if 'gwp' in details and 'total_carbon' not in details:
                    details['total_carbon'] = details['gwp']
                # Also ensure 'elements' key exists for compatibility
                if 'element_count' in details and 'elements' not in details:
                    details['elements'] = details['element_count']
                # Add density information for element calculations
                material_data = db_reader.get_material_data(details.get('database_id', ''))
                if material_data and 'density' not in details:
                    details['density'] = material_data.get('density', 0)
                # Ensure carbon_per_unit for calculations
                if 'carbon_per_unit' not in details and material_data:
                    details['carbon_per_unit'] = material_data.get('gwp', material_data.get('carbon_per_unit', 0))
            
            # Format and store results
            results_text = format_results(results, detailed_results, db_reader)
            props.results_text = results_text
            props.results_json = json.dumps(detailed_results)
            
            # Calculate total - handle both 'gwp' and 'total_carbon' keys for compatibility
            total_carbon = sum(
                detailed_results[m].get('gwp', detailed_results[m].get('total_carbon', 0)) 
                for m in detailed_results
            )
            props.total_carbon = total_carbon
            props.show_results = True
            
            # Log results
            logger.info("Analysis completed successfully")
            logger.info(f"Total: {total_carbon:.1f} kg CO₂e")
            logger.info(f"Results:\n{results_text}")
            self.report({'INFO'}, f"Analysis complete. Total: {total_carbon:.1f} kg CO₂e")
            
            return {'FINISHED'}
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            import traceback
            logger.error(f"Analysis error traceback: {traceback.format_exc()}")
            self.report({'ERROR'}, f"Analysis failed: {str(e)}")
            return {'CANCELLED'}


class IFCLCA_OT_ClearResults(Operator):
    """Clear the analysis results"""
    bl_idname = "ifclca.clear_results"
    bl_label = "Clear Results"
    bl_description = "Clear the current analysis results"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.ifclca_props
        props.results_text = ""
        props.results_json = ""
        props.total_carbon = 0.0
        props.show_results = False
        return {'FINISHED'}


class IFCLCA_OT_AutoMapMaterials(Operator):
    """Attempt to automatically map materials by name matching"""
    bl_idname = "ifclca.auto_map_materials"
    bl_label = "Auto-Map Materials"
    bl_description = "Attempt to automatically map materials based on name matching"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.ifclca_props
        
        try:
            # Get database reader
            if props.database_type == 'KBOB':
                db_reader = get_core_database_reader('KBOB', props.kbob_data_path)
            elif props.database_type == 'OKOBAUDAT_API':
                from .database_reader import HAS_REQUESTS
                if not HAS_REQUESTS:
                    self.report({'ERROR'}, "The 'requests' module is not installed. See console for installation instructions.")
                    return {'CANCELLED'}
                db_reader = get_extended_database_reader('OKOBAUDAT_API', props.okobaudat_api_key)
            else:
                self.report({'ERROR'}, "Invalid database type")
                return {'CANCELLED'}
            
            mapped_count = 0
            already_mapped = 0
            no_match_materials = []
            
            logger.info("Starting auto-mapping...")
            
            # Try to map each material
            for mat_mapping in props.material_mappings:
                if mat_mapping.is_mapped:
                    already_mapped += 1
                    continue
                
                # Clean up material name for better matching
                clean_name = mat_mapping.ifc_material_name.lower()
                
                # Try exact search first
                matches = db_reader.search_materials(mat_mapping.ifc_material_name)
                
                # If no exact match, try common mappings
                if not matches:
                    # Common material mappings
                    material_mappings = {
                        'concrete': ['concrete', 'beton'],
                        'steel': ['steel', 'stahl', 'metal'],
                        'reinforced concrete': ['concrete', 'reinforced'],
                        'wood': ['timber', 'wood', 'holz'],
                        'glass': ['glass', 'glas'],
                        'gypsum': ['gypsum', 'plaster', 'gips'],
                        'brick': ['brick', 'masonry', 'ziegel'],
                        'insulation': ['insulation', 'dämmung'],
                        'aluminum': ['aluminum', 'aluminium']
                    }
                    
                    # Try to find matches based on keywords
                    for key, search_terms in material_mappings.items():
                        if any(term in clean_name for term in search_terms):
                            for term in search_terms:
                                matches = db_reader.search_materials(term)
                                if matches:
                                    break
                            if matches:
                                break
                
                if matches:
                    # Use first match
                    match = matches[0]
                    mat_id = match['id']
                    mat_name = match['name']
                    mat_category = match['category']
                    mat_mapping.database_id = mat_id
                    mat_mapping.database_name = mat_name
                    mat_mapping.is_mapped = True
                    mapped_count += 1
                    logger.debug(f"Mapped '{mat_mapping.ifc_material_name}' to '{mat_name}'")
                else:
                    no_match_materials.append(mat_mapping.ifc_material_name)
            
            # Report results
            total_materials = len(props.material_mappings)
            logger.info(f"Auto-mapping complete: {mapped_count} newly mapped, {already_mapped} already mapped, {len(no_match_materials)} unmatched")
            
            if no_match_materials:
                logger.warning(f"Could not find matches for: {', '.join(no_match_materials[:5])}")
                if len(no_match_materials) > 5:
                    logger.warning(f"... and {len(no_match_materials) - 5} more")
            
            self.report({'INFO'}, f"Auto-mapped {mapped_count} materials. Total: {already_mapped + mapped_count}/{total_materials}")
            return {'FINISHED'}
            
        except Exception as e:
            logger.error(f"Auto-mapping failed: {str(e)}")
            self.report({'ERROR'}, f"Auto-mapping failed: {str(e)}")
            return {'CANCELLED'}


class IFCLCA_OT_ExportResults(Operator):
    """Export LCA results to CSV file"""
    bl_idname = "ifclca.export_results"
    bl_label = "Export Results"
    bl_description = "Export LCA analysis results to CSV file"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(
        name="File Path",
        description="Path to save the CSV file",
        default="lca_results.csv",
        subtype='FILE_PATH'
    )
    
    def invoke(self, context, event):
        # Set default filename with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filepath = f"lca_results_{timestamp}.csv"
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def _parse_carbon_value_to_kg(self, carbon_str):
        """Parse carbon value from string and convert to kg (e.g. '4.13 t CO₂-eq' -> '4130.0 kg CO₂-eq')"""
        try:
            # Remove CO₂-eq suffix
            value_str = carbon_str.replace('CO₂-eq', '').replace('CO₂e', '').strip()
            
            # Check for tons
            if 't' in value_str:
                value = float(value_str.replace('t', '').strip())
                return f"{value * 1000:.1f} kg CO₂-eq"  # Convert to kg
            else:
                # Already in kg, just clean up formatting
                value = float(value_str.replace('kg', '').strip())
                return f"{value:.1f} kg CO₂-eq"
        except:
            return carbon_str  # Return original if parsing fails

    def execute(self, context):
        props = context.scene.ifclca_props
        
        if not props.results_text:
            self.report({'ERROR'}, "No results to export")
            return {'CANCELLED'}
        
        try:
            import csv
            import re
            
            # Parse results
            lines = props.results_text.split('\n')
            materials_data = []
            
            i = 0
            while i < len(lines):
                line = lines[i]
                if line and not line.startswith(' ') and not line.startswith('=') and not line.startswith('-') and ':' in line:
                    material_name = line.rstrip(':')
                    material_info = {'Material': material_name}
                    
                    i += 1
                    while i < len(lines) and lines[i].startswith('  '):
                        info_line = lines[i].strip()
                        if ':' in info_line:
                            key, value = info_line.split(':', 1)
                            material_info[key.strip()] = value.strip()
                        i += 1
                    
                    if 'Carbon' in material_info:
                        materials_data.append(material_info)
                    continue
                i += 1
            
            # Write CSV
            with open(self.filepath, 'w', newline='', encoding='utf-8') as csvfile:
                # Write header
                csvfile.write(f"LCA Results Export\n")
                csvfile.write(f"Project: {context.scene.name}\n")
                csvfile.write(f"Total Embodied Carbon: {props.total_carbon:.1f} kg CO₂-eq\n")
                csvfile.write(f"\n")
                
                # Write material data
                if materials_data:
                    fieldnames = ['Material', 'IFC Material', 'Elements', 'Volume', 'Mass', 'Carbon']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for mat in materials_data:
                        # Convert carbon values to kg if they're in tonnes
                        carbon_value = mat.get('Carbon', '')
                        if carbon_value:
                            carbon_value = self._parse_carbon_value_to_kg(carbon_value)
                        
                        row = {
                            'Material': mat.get('Material', ''),
                            'IFC Material': mat.get('IFC Material', ''),
                            'Elements': mat.get('Elements', ''),
                            'Volume': mat.get('Volume', ''),
                            'Mass': mat.get('Mass', ''),
                            'Carbon': carbon_value
                        }
                        writer.writerow(row)
            
            self.report({'INFO'}, f"Results exported to {self.filepath}")
            logger.info(f"Exported LCA results to {self.filepath}")
            return {'FINISHED'}
            
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'CANCELLED'}


class IFCLCA_OT_ViewWebResults(Operator):
    """Open analysis results in a web browser"""
    bl_idname = "ifclca.view_web_results"
    bl_label = "View in Browser"
    bl_description = "View analysis results in an interactive web page"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global _ifc_file, _web_server
        props = context.scene.ifclca_props
        if not props.results_json:
            self.report({'ERROR'}, "No results available")
            return {'CANCELLED'}
        try:
            from . import web_interface
        except ImportError:
            import web_interface

        # Parse results
        detailed_results = json.loads(props.results_json)
        
        # Debug logging
        logger.info(f"Launching web interface with {len(detailed_results)} materials")
        logger.debug(f"Sample data: {list(detailed_results.keys())[:3]}")
        
        # Launch browser with detailed results and IFC file
        server = web_interface.launch_results_browser(
            results=detailed_results,  # For backward compatibility
            detailed_results=detailed_results,
            ifc_file=_ifc_file
        )
        # Store server globally to keep alive
        _web_server = server
        self.report({'INFO'}, "Opening results in web browser...")
        return {'FINISHED'}


class IFCLCA_OT_SearchOkobaudat(Operator):
    """Search Ökobaudat API for materials"""
    bl_idname = "ifclca.search_okobaudat"
    bl_label = "Search Ökobaudat"
    bl_description = "Search Ökobaudat API for materials"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    search_query: StringProperty(
        name="Search Query",
        description="Search for materials by name",
        default=""
    )
    
    def execute(self, context):
        props = context.scene.ifclca_props
        
        if props.database_type != 'OKOBAUDAT_API':
            return {'CANCELLED'}
        
        # Check if requests is available
        from .database_reader import HAS_REQUESTS
        if not HAS_REQUESTS:
            self.report({'ERROR'}, "The 'requests' module could not be loaded. Ökobaudat API functionality is disabled.")
            return {'CANCELLED'}
        
        # Clear existing materials
        context.scene.ifclca_material_database.clear()
        
        try:
            # Check cache first for this query
            cached_results = _okobaudat_cache.get_query_results(self.search_query)
            
            if cached_results:
                # Use cached results
                logger.info(f"Using cached results for query: {self.search_query}")
                all_materials = cached_results
            else:
                # Get API reader
                db_reader = get_extended_database_reader('OKOBAUDAT_API', props.okobaudat_api_key)
                
                # Perform search
                if self.search_query:
                    db_reader.load_materials(search_query=self.search_query, limit=50)
                else:
                    db_reader.load_materials(limit=20)  # Load some default materials
                
                # Get all materials
                all_materials = db_reader.get_all_materials()
                
                # Cache the query results
                _okobaudat_cache.set_query_results(self.search_query, all_materials)
            
            valid_count = 0
            for mat in all_materials:
                item = context.scene.ifclca_material_database.add()
                item.material_id = mat.get('id', '')
                item.name = mat.get('name', '')
                item.category = mat.get('category', 'Uncategorized')
                
                # Check if we have cached data for this material
                cached_data = _okobaudat_cache.get(item.material_id)
                if cached_data:
                    item.gwp = safe_float(cached_data.get('carbon_per_unit'))
                    item.density = safe_float(cached_data.get('density'))
                else:
                    item.gwp = safe_float(mat.get('gwp'))
                    item.density = safe_float(mat.get('density'))
                    
                valid_count += 1
            
            # Force UI refresh
            for area in context.screen.areas:
                area.tag_redraw()
            
            self.report({'INFO'}, f"Found {valid_count} materials")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Search failed: {str(e)}")
            return {'CANCELLED'}


class IFCLCA_OT_FetchMaterialData(Operator):
    """Fetch detailed data for selected material"""
    bl_idname = "ifclca.fetch_material_data"
    bl_label = "Fetch Material Data"
    bl_description = "Fetch environmental data for the selected material"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    material_index: IntProperty()
    
    def execute(self, context):
        props = context.scene.ifclca_props
        db = context.scene.ifclca_material_database
        
        if self.material_index < 0 or self.material_index >= len(db):
            return {'CANCELLED'}
        
        item = db[self.material_index]
        
        # Check cache first
        cached_data = _okobaudat_cache.get(item.material_id)
        if cached_data:
            # Use cached data
            item.gwp = safe_float(cached_data.get('carbon_per_unit'))
            item.density = safe_float(cached_data.get('density'))
            logger.info(f"  ✓ Using cached data - GWP: {item.gwp:.2f} kg CO₂/kg")
            
            # Force UI refresh
            for area in context.screen.areas:
                area.tag_redraw()
            return {'FINISHED'}
        
        # Only fetch if we don't have data yet
        if item.gwp > 0:
            return {'FINISHED'}
        
        try:
            # Get API reader
            db_reader = get_extended_database_reader('OKOBAUDAT_API', props.okobaudat_api_key)
            
            # Fetch full data
            logger.info(f"Fetching data for: {item.name[:50]}...")
            full_data = db_reader.get_full_material_data(item.material_id)
            
            # Cache the data
            _okobaudat_cache.set(item.material_id, full_data)
            
            # Update the item with full data
            item.gwp = safe_float(full_data.get('carbon_per_unit'))
            item.density = safe_float(full_data.get('density'))
            
            if item.gwp > 0:
                logger.info(f"  ✓ GWP: {item.gwp:.2f} kg CO₂/kg")
            else:
                logger.warning(f"  ⚠ No GWP data found")
            
            # Force UI refresh
            for area in context.screen.areas:
                area.tag_redraw()
            
            return {'FINISHED'}
            
        except Exception as e:
            logger.error(f"Failed to fetch material data: {str(e)}")
            self.report({'ERROR'}, f"Failed to fetch data: {str(e)}")
            return {'CANCELLED'}


class IFCLCA_OT_PreloadVisibleMaterials(Operator):
    """Preload data for visible materials"""
    bl_idname = "ifclca.preload_visible_materials"
    bl_label = "Preload Visible Materials"
    bl_description = "Preload environmental data for visible materials"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    start_index: IntProperty()
    end_index: IntProperty()
    
    def execute(self, context):
        props = context.scene.ifclca_props
        db = context.scene.ifclca_material_database
        
        if props.database_type != 'OKOBAUDAT_API':
            return {'FINISHED'}
        
        # Limit to valid range
        start = max(0, self.start_index)
        end = min(len(db), self.end_index)
        
        # Add buffer for smooth scrolling (preload 5 items above and below)
        buffer = 5
        start = max(0, start - buffer)
        end = min(len(db), end + buffer)
        
        try:
            # Get API reader
            db_reader = get_extended_database_reader('OKOBAUDAT_API', props.okobaudat_api_key)
            
            # Preload data for visible range
            preloaded = 0
            for i in range(start, end):
                item = db[i]
                
                # Skip if already has data or is cached
                if item.gwp > 0 or _okobaudat_cache.has(item.material_id):
                    continue
                
                # Fetch and cache data
                try:
                    full_data = db_reader.get_full_material_data(item.material_id)
                    _okobaudat_cache.set(item.material_id, full_data)
                    
                    # Update item
                    item.gwp = safe_float(full_data.get('carbon_per_unit'))
                    item.density = safe_float(full_data.get('density'))
                    preloaded += 1
                    
                except Exception as e:
                    logger.debug(f"Failed to preload {item.name}: {str(e)}")
            
            if preloaded > 0:
                logger.info(f"Preloaded {preloaded} materials")
                # Force UI refresh
                for area in context.screen.areas:
                    area.tag_redraw()
            
            return {'FINISHED'}
            
        except Exception as e:
            logger.error(f"Preload failed: {str(e)}")
            return {'CANCELLED'}


class IFCLCA_OT_ClearMaterialCache(Operator):
    """Clear cached material data"""
    bl_idname = "ifclca.clear_material_cache"
    bl_label = "Clear Material Cache"
    bl_description = "Clear all cached Ökobaudat material data"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        cache_size = len(_okobaudat_cache.cache)
        _okobaudat_cache.clear()
        
        self.report({'INFO'}, f"Cleared {cache_size} cached materials")
        logger.info(f"Cleared material cache ({cache_size} items)")
        
        # Force UI refresh
        for area in context.screen.areas:
            area.tag_redraw()
        
        return {'FINISHED'}


# List of classes to register
classes = [
    IFCLCA_OT_LoadIFC,
    IFCLCA_OT_UseActiveIFC,
    IFCLCA_OT_SortMaterialDatabase,
    IFCLCA_OT_BrowseMaterials,
    IFCLCA_OT_RunAnalysis,
    IFCLCA_OT_ClearResults,
    IFCLCA_OT_AutoMapMaterials,
    IFCLCA_OT_ExportResults,
    IFCLCA_OT_ViewWebResults,
    IFCLCA_OT_SearchOkobaudat,
    IFCLCA_OT_FetchMaterialData,
    IFCLCA_OT_PreloadVisibleMaterials,
    IFCLCA_OT_ClearMaterialCache
]
