try:
    import bpy
    from bpy.types import Operator
    from bpy.props import StringProperty, EnumProperty
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

try:
    import ifcopenshell
except ImportError:
    ifcopenshell = None

# Import our modules
try:
    from .database_reader import get_database_reader
    from .logic import IfcMaterialExtractor, run_lca_analysis, format_results
except ImportError:
    # For testing, use absolute imports
    from database_reader import get_database_reader
    from logic import IfcMaterialExtractor, run_lca_analysis, format_results

# Try to import Bonsai tools if available
try:
    from bonsai.bim import tool
    HAS_BONSAI = True
except ImportError:
    HAS_BONSAI = False

# Global storage for IFC file (could also use Bonsai's IfcStore)
_ifc_file = None


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
        
        try:
            # Load the IFC file
            print(f"Loading IFC file: {self.filepath}")
            _ifc_file = ifcopenshell.open(self.filepath)
            
            # Update properties
            props.ifc_file_path = self.filepath
            props.ifc_loaded = True
            
            # Clear existing material mappings
            props.material_mappings.clear()
            
            # Extract materials from the IFC file
            extractor = IfcMaterialExtractor(_ifc_file)
            materials = extractor.get_all_materials()
            
            # Create material mapping entries
            for material_name, count in materials:
                item = props.material_mappings.add()
                item.ifc_material_name = material_name
                item.database_id = ""
                item.database_name = ""
                item.is_mapped = False
            
            self.report({'INFO'}, f"Loaded IFC file with {len(materials)} materials")
            return {'FINISHED'}
            
        except Exception as e:
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
            self.report({'ERROR'}, "Bonsai is not available")
            return {'CANCELLED'}
        
        try:
            # Get IFC file from Bonsai
            ifc = tool.Ifc.get()
            if not ifc:
                self.report({'ERROR'}, "No IFC file is currently loaded in Bonsai")
                return {'CANCELLED'}
            
            _ifc_file = ifc
            
            # Update properties
            props.ifc_file_path = "Active Bonsai IFC"
            props.ifc_loaded = True
            
            # Clear existing material mappings
            props.material_mappings.clear()
            
            # Extract materials from the IFC file
            extractor = IfcMaterialExtractor(_ifc_file)
            materials = extractor.get_all_materials()
            
            # Create material mapping entries
            for material_name, count in materials:
                item = props.material_mappings.add()
                item.ifc_material_name = material_name
                item.database_id = ""
                item.database_name = ""
                item.is_mapped = False
            
            self.report({'INFO'}, f"Using active IFC with {len(materials)} materials")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to get active IFC: {str(e)}")
            return {'CANCELLED'}


class IFCLCA_OT_MapMaterial(Operator):
    """Map a material to an LCA database entry"""
    bl_idname = "ifclca.map_material"
    bl_label = "Map Material"
    bl_description = "Map this material to an LCA database entry"
    bl_options = {'REGISTER', 'UNDO'}
    
    material_index: StringProperty()
    
    def get_database_items(self, context):
        """Get database entries for enum property"""
        props = context.scene.ifclca_props
        items = [('', "Not mapped", "No mapping selected")]
        
        try:
            # Get appropriate database reader
            if props.database_type == 'KBOB':
                db_reader = get_database_reader('KBOB', props.kbob_data_path)
            elif props.database_type == 'OKOBAUDAT':
                if not props.okobaudat_csv_path:
                    return items
                db_reader = get_database_reader('OKOBAUDAT', props.okobaudat_csv_path)
            else:
                return items
            
            # Get materials list
            materials = db_reader.get_materials_list()
            
            # Group by category
            current_category = None
            for mat_id, mat_name, mat_category in materials:
                # Add category separator
                if mat_category != current_category:
                    current_category = mat_category
                    # Use a special ID that won't be selected
                    items.append((f'__category__{mat_category}', f"--- {mat_category} ---", ""))
                
                # Add material
                items.append((mat_id, mat_name, f"Category: {mat_category}"))
                
        except Exception as e:
            print(f"Error loading database: {e}")
        
        return items
    
    database_entry: EnumProperty(
        name="Database Entry",
        description="Select the corresponding database entry",
        items=get_database_items
    )
    
    def invoke(self, context, event):
        # Show dropdown menu
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "database_entry")
    
    def execute(self, context):
        props = context.scene.ifclca_props
        
        try:
            idx = int(self.material_index)
            mapping = props.material_mappings[idx]
            
            # Don't allow selecting category separators
            if self.database_entry.startswith('__category__'):
                return {'CANCELLED'}
            
            # Update mapping
            if self.database_entry:
                mapping.database_id = self.database_entry
                
                # Get database reader to fetch the name
                if props.database_type == 'KBOB':
                    db_reader = get_database_reader('KBOB', props.kbob_data_path)
                elif props.database_type == 'OKOBAUDAT':
                    db_reader = get_database_reader('OKOBAUDAT', props.okobaudat_csv_path)
                else:
                    return {'CANCELLED'}
                
                material_data = db_reader.get_material_data(self.database_entry)
                mapping.database_name = material_data.get('name', self.database_entry)
                mapping.is_mapped = True
            else:
                mapping.database_id = ""
                mapping.database_name = ""
                mapping.is_mapped = False
            
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
                db_reader = get_database_reader('KBOB', props.kbob_data_path)
            elif props.database_type == 'OKOBAUDAT':
                if not props.okobaudat_csv_path:
                    self.report({'ERROR'}, "Please set ÖKOBAUDAT CSV path in preferences")
                    return {'CANCELLED'}
                db_reader = get_database_reader('OKOBAUDAT', props.okobaudat_csv_path)
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
            
            # Format and store results
            results_text = format_results(results, detailed_results, db_reader)
            props.results_text = results_text
            
            # Calculate total
            total_carbon = sum(detailed_results[m]['total_carbon'] for m in detailed_results)
            props.total_carbon = total_carbon
            props.show_results = True
            
            # Report to console and info
            print("\n" + results_text)
            self.report({'INFO'}, f"Analysis complete. Total: {total_carbon:.1f} kg CO₂e")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
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
                db_reader = get_database_reader('KBOB', props.kbob_data_path)
            elif props.database_type == 'OKOBAUDAT':
                if not props.okobaudat_csv_path:
                    self.report({'ERROR'}, "Please set ÖKOBAUDAT CSV path in preferences")
                    return {'CANCELLED'}
                db_reader = get_database_reader('OKOBAUDAT', props.okobaudat_csv_path)
            else:
                self.report({'ERROR'}, "Invalid database type")
                return {'CANCELLED'}
            
            mapped_count = 0
            
            # Try to map each material
            for mat_mapping in props.material_mappings:
                if mat_mapping.is_mapped:
                    continue
                
                # Search for matching database entries
                matches = db_reader.search_materials(mat_mapping.ifc_material_name)
                
                if matches:
                    # Use first match
                    mat_id, mat_name, mat_category = matches[0]
                    mat_mapping.database_id = mat_id
                    mat_mapping.database_name = mat_name
                    mat_mapping.is_mapped = True
                    mapped_count += 1
            
            self.report({'INFO'}, f"Auto-mapped {mapped_count} materials")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Auto-mapping failed: {str(e)}")
            return {'CANCELLED'}


# List of classes to register
classes = [
    IFCLCA_OT_LoadIFC,
    IFCLCA_OT_UseActiveIFC,
    IFCLCA_OT_MapMaterial,
    IFCLCA_OT_RunAnalysis,
    IFCLCA_OT_ClearResults,
    IFCLCA_OT_AutoMapMaterials
] 