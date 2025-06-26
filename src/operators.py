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
    from .ifclca_core import get_database_reader
    from .logic import IfcMaterialExtractor, run_lca_analysis, format_results
except ImportError:
    # Fallback to absolute imports (for testing)
    from ifclca_core import get_database_reader
    from logic import IfcMaterialExtractor, run_lca_analysis, format_results

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


class IFCLCA_OT_BrowseMaterials(Operator):
    """Browse and select materials from database"""
    bl_idname = "ifclca.browse_materials"
    bl_label = "Browse Materials"
    bl_description = "Browse and select a material from the database"
    bl_options = {'REGISTER', 'UNDO'}
    
    material_index: StringProperty()
    
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
                db_reader = get_database_reader('KBOB', props.kbob_data_path)
            elif props.database_type == 'OKOBAUDAT':
                if not props.okobaudat_csv_path:
                    self.report({'ERROR'}, "No database loaded")
                    return {'CANCELLED'}
                db_reader = get_database_reader('OKOBAUDAT', props.okobaudat_csv_path)
            else:
                self.report({'ERROR'}, "No database selected")
                return {'CANCELLED'}
            
            # Get all materials
            all_materials = db_reader.get_all_materials()
            
            # Filter and add to collection
            valid_count = 0
            for mat in all_materials:
                name = mat.get('name', '')
                # Use the same validation
                if self.is_valid_material_name(name):
                    item = context.scene.ifclca_material_database.add()
                    item.material_id = mat.get('id', '')
                    item.name = name
                    item.category = mat.get('category', 'Uncategorized')
                    item.gwp = mat.get('gwp', 0)
                    item.density = mat.get('density', 0)
                    valid_count += 1
            
            logger.info(f"Loaded {valid_count} materials into browser")
            
            # Show the browser dialog
            return context.window_manager.invoke_props_dialog(self, width=800)
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load materials: {str(e)}")
            return {'CANCELLED'}
    
    def draw(self, context):
        layout = self.layout
        
        # Header
        row = layout.row()
        row.label(text="Select Material from Database", icon='VIEWZOOM')
        
        # Info about current selection
        db = context.scene.ifclca_material_database
        idx = context.scene.ifclca_material_database_index
        if 0 <= idx < len(db):
            box = layout.box()
            box.label(text=f"Selected: {db[idx].name}", icon='MATERIAL_DATA')
            if db[idx].gwp > 0:
                box.label(text=f"GWP: {db[idx].gwp*1000:.3f} g CO₂/kg")
            if db[idx].density > 0:
                box.label(text=f"Density: {db[idx].density:.0f} kg/m³")
        
        # Material list with search
        layout.template_list(
            "IFCLCA_UL_MaterialDatabaseList", "material_browser_list",
            context.scene, "ifclca_material_database",
            context.scene, "ifclca_material_database_index",
            rows=15,
            maxrows=15
        )
        
        # Help text
        box = layout.box()
        col = box.column(align=True)
        col.scale_y = 0.9
        col.label(text="Tips:", icon='INFO')
        col.label(text="• Use search box to filter materials")
        col.label(text="• Click column headers to sort")
        col.label(text="• Double-click to select")
    
    def execute(self, context):
        props = context.scene.ifclca_props
        db = context.scene.ifclca_material_database
        idx = context.scene.ifclca_material_database_index
        
        if idx < 0 or idx >= len(db):
            self.report({'WARNING'}, "No material selected")
            return {'CANCELLED'}
        
        try:
            # Get selected material
            selected = db[idx]
            mat_idx = int(self.material_index)
            mapping = props.material_mappings[mat_idx]
            
            # Update mapping
            mapping.database_id = selected.material_id
            mapping.database_name = selected.name
            mapping.is_mapped = True
            
            self.report({'INFO'}, f"Mapped to: {mapping.database_name}")
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
        global _ifc_file
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
        # Store server on context to keep alive
        context.scene.ifclca_web_server = server
        self.report({'INFO'}, "Opening results in web browser...")
        return {'FINISHED'}


# List of classes to register
classes = [
    IFCLCA_OT_LoadIFC,
    IFCLCA_OT_UseActiveIFC,
    IFCLCA_OT_BrowseMaterials,
    IFCLCA_OT_RunAnalysis,
    IFCLCA_OT_ClearResults,
    IFCLCA_OT_AutoMapMaterials,
    IFCLCA_OT_ExportResults,
    IFCLCA_OT_ViewWebResults
]
