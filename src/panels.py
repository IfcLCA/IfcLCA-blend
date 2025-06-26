try:
    import bpy
    from bpy.types import Panel, UIList
except ImportError:
    # For testing
    from unittest.mock import MagicMock
    Panel = type
    UIList = type

import logging
logger = logging.getLogger('IfcLCA')

# Try to import Bonsai to check if available
try:
    from bonsai.bim.ifc import IfcStore
    HAS_BONSAI = True
except ImportError:
    HAS_BONSAI = False


class IFCLCA_UL_MaterialMappingList(UIList):
    """UI List for material mappings"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        props = context.scene.ifclca_props
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # Use split layout for better width utilization
            split = layout.split(factor=0.4)
            
            # Left side - IFC material name
            left = split.row()
            left.label(text=item.ifc_material_name, icon='MATERIAL')
            
            # Right side - mapping info and button
            right = split.row(align=True)
            
            if item.is_mapped:
                # Show mapped material name with icon
                right.label(text=item.database_name, icon='CHECKMARK')
                # Edit button
                op = right.operator("ifclca.browse_materials", text="Change", icon='GREASEPENCIL')
            else:
                # Show unmapped status
                right.label(text="Not mapped", icon='ERROR')
                # Map button
                op = right.operator("ifclca.browse_materials", text="Select Material", icon='VIEWZOOM')
            
            # Find the index of this item
            for idx, mapping in enumerate(active_data.material_mappings):
                if mapping == item:
                    op.material_index = str(idx)
                    break
            
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='MATERIAL')
            
    def filter_items(self, context, data, propname):
        """Filter and sort items"""
        props = context.scene.ifclca_props
        mappings = getattr(data, propname)
        
        # Initialize filter flags
        flt_flags = []
        flt_neworder = []
        
        # Filter based on mapped status if requested
        if props.filter_mapped:
            for item in mappings:
                if not item.is_mapped:
                    flt_flags.append(self.bitflag_filter_item)
                else:
                    flt_flags.append(0)
        else:
            flt_flags = [self.bitflag_filter_item] * len(mappings)
            
        return flt_flags, flt_neworder


class IFCLCA_UL_MaterialDatabaseList(UIList):
    """UI List for material database browser"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        """Draw each item in the list"""
        # Force filter UI to show
        self.use_filter_show = True
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            props = context.scene.ifclca_props
            
            # Use split for better layout
            split = layout.split(factor=0.3)
            
            # Category with optional impact indicators
            cat_row = split.row()
            
            # Calculate relative impact if indicators are enabled
            impact_icon = 'DOT'
            if props.show_impact_indicators and item.gwp > 0:
                # Get all items in the same category with GWP data
                all_items = context.scene.ifclca_material_database
                category_gwps = [mat.gwp for mat in all_items 
                               if mat.category == item.category and mat.gwp > 0]
                
                if category_gwps:
                    # Calculate percentile within category
                    sorted_gwps = sorted(category_gwps)
                    # Count how many materials have lower GWP
                    lower_count = sum(1 for gwp in category_gwps if gwp < item.gwp)
                    percentile = lower_count / len(category_gwps)
                    
                    # Assign icon based on relative performance in category
                    if percentile >= 0.75:  # Top 25% worst performers
                        cat_row.alert = True
                        impact_icon = 'ORPHAN_DATA'
                    elif percentile >= 0.5:  # 50-75th percentile
                        impact_icon = 'ERROR'
                    elif percentile >= 0.25:  # 25-50th percentile
                        impact_icon = 'INFO'
                    else:  # Bottom 25% best performers
                        impact_icon = 'CHECKMARK'
                else:
                    impact_icon = 'QUESTION'
            elif props.show_impact_indicators and item.gwp == 0:
                impact_icon = 'QUESTION'
            
            cat_row.label(text=item.category, icon=impact_icon)
            
            # Material name
            name_split = split.split(factor=0.5)
            name_row = name_split.row()
            name_row.label(text=item.name, icon='MATERIAL_DATA')
            
            # Environmental data with better formatting
            data_row = name_split.row(align=True)
            data_row.scale_x = 0.9
            
            if item.gwp > 0:
                # GWP is stored in kg CO₂-eq/kg
                gwp_text = f"{item.gwp:.3f} kg CO₂/kg"
                data_row.label(text=gwp_text)
            else:
                data_row.label(text="No GWP data")
                
            if item.density > 0:
                data_row.label(text=f"• {item.density:.0f} kg/m³")
                    
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='MATERIAL')
    
    def draw_filter(self, context, layout):
        """Draw filter UI - search only"""
        # Create a prominent search row
        row = layout.row(align=True)
        
        # Search icon and input field
        row.prop(self, "filter_name", text="", icon='VIEWZOOM')

    def filter_items(self, context, data, propname):
        """Filter items in the list and apply sorting"""
        # Get items collection
        items = getattr(data, propname)
        props = context.scene.ifclca_props
        
        # Initialize return values
        flt_flags = []
        flt_neworder = []
        
        # FILTERING
        if self.filter_name:
            # Custom filter for name OR category
            flt_flags = [self.bitflag_filter_item] * len(items)
            search_term = self.filter_name.lower()
            
            for i, item in enumerate(items):
                # Check both name and category
                found = (search_term in item.name.lower() or 
                        search_term in item.category.lower())
                
                # Clear flag if not found
                if not found:
                    flt_flags[i] &= ~self.bitflag_filter_item
        else:
            # No filter - show all items
            flt_flags = [self.bitflag_filter_item] * len(items)
            
        # SORTING
        if props.material_sort_column != 'NONE' and len(items) > 0:
            # Create list of (index, sort_value) tuples for sort_items_helper
            indexed_items = []
            
            for i, item in enumerate(items):
                if props.material_sort_column == 'CATEGORY':
                    # Sort by category, then by name for stability
                    sort_value = (item.category.lower(), item.name.lower())
                elif props.material_sort_column == 'NAME':
                    sort_value = item.name.lower()
                elif props.material_sort_column == 'GWP':
                    # For numerical sorting, ensure items with no data always appear at bottom
                    if item.gwp > 0:
                        sort_value = item.gwp
                    else:
                        # Use a very large number so items with no data always sort to the end
                        # regardless of whether we're sorting ascending or descending
                        sort_value = float('inf') if not props.material_sort_reverse else float('-inf')
                elif props.material_sort_column == 'DENSITY':
                    # For numerical sorting, ensure items with no data always appear at bottom  
                    if item.density > 0:
                        sort_value = item.density
                    else:
                        # Use a very large number so items with no data always sort to the end
                        # regardless of whether we're sorting ascending or descending
                        sort_value = float('inf') if not props.material_sort_reverse else float('-inf')
                else:
                    sort_value = i  # Default to original order
                    
                indexed_items.append((i, sort_value))
            
            # Sort the items using the helper function
            helper_funcs = bpy.types.UI_UL_list
            if props.material_sort_column in ['GWP', 'DENSITY']:
                # For numerical columns with tuple sorting:
                # When reverse=False: (True, low_value) comes before (True, high_value) comes before (False, any)
                # When reverse=True: (True, high_value) comes before (True, low_value) comes before (False, any)
                # The (False, any) items always come last regardless of reverse flag
                flt_neworder = helper_funcs.sort_items_helper(indexed_items, key=lambda x: x[1], reverse=props.material_sort_reverse)
            else:
                # Alphabetical sort - use sort_items_helper
                flt_neworder = helper_funcs.sort_items_helper(indexed_items, key=lambda x: x[1], reverse=props.material_sort_reverse)
            
        return flt_flags, flt_neworder


class IFCLCA_PT_MainPanel(Panel):
    """Main IfcLCA panel in 3D View sidebar"""
    bl_label = "IfcLCA"
    bl_idname = "IFCLCA_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "IfcLCA"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.ifclca_props
        
        # Header with database selection
        box = layout.box()
        col = box.column()
        col.label(text="LCA Database:", icon='FILE_TEXT')
        col.prop(props, "database_type", text="")
        
        # Show database path configuration based on selection
        if props.database_type == 'OKOBAUDAT':
            if not props.okobaudat_csv_path:
                col.label(text="Please set ÖKOBAUDAT path in preferences", icon='ERROR')
            else:
                col.label(text="ÖKOBAUDAT loaded", icon='CHECKMARK')
        elif props.database_type == 'KBOB':
            col.label(text="Using built-in KBOB data", icon='CHECKMARK')


class IFCLCA_PT_IFCPanel(Panel):
    """IFC file loading panel"""
    bl_label = "IFC Model"
    bl_idname = "IFCLCA_PT_ifc_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "IfcLCA"
    bl_parent_id = "IFCLCA_PT_main_panel"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.ifclca_props
        
        col = layout.column()
        
        # Check if Bonsai has an active IFC file
        bonsai_has_ifc = False
        if HAS_BONSAI:
            try:
                ifc = IfcStore.get_file()
                bonsai_has_ifc = ifc is not None
            except:
                bonsai_has_ifc = False
        
        # If Bonsai has IFC but we haven't loaded it yet
        if bonsai_has_ifc and not props.ifc_loaded:
            box = col.box()
            box.label(text="Bonsai IFC detected!", icon='INFO')
            row = box.row()
            row.scale_y = 1.5
            row.operator("ifclca.use_active_ifc", text="Use Active IFC", icon='FILE_REFRESH')
            col.separator()
            col.operator("ifclca.load_ifc", text="Load Different IFC", icon='FILE_FOLDER')
        
        # IFC loading options
        elif not props.ifc_loaded:
            col.operator("ifclca.load_ifc", icon='FILE_FOLDER')
            if HAS_BONSAI:
                col.operator("ifclca.use_active_ifc", icon='FILE_REFRESH')
        else:
            # Show loaded file info
            box = col.box()
            box.label(text="IFC File Loaded", icon='CHECKMARK')
            if props.ifc_file_path != "Active Bonsai IFC":
                box.label(text=f"File: {props.ifc_file_path.split('/')[-1]}")
            else:
                box.label(text="Using Bonsai IFC", icon='FILE_REFRESH')
            
            # Reload options
            row = box.row()
            row.operator("ifclca.load_ifc", text="Load Different IFC", icon='FILE_FOLDER')
            if HAS_BONSAI:
                row.operator("ifclca.use_active_ifc", text="Refresh from Bonsai", icon='FILE_REFRESH')


class IFCLCA_PT_MaterialMappingPanel(Panel):
    """Material mapping panel"""
    bl_label = "Material Mapping"
    bl_idname = "IFCLCA_PT_material_mapping_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "IfcLCA"
    bl_parent_id = "IFCLCA_PT_main_panel"
    
    @classmethod
    def poll(cls, context):
        return context.scene.ifclca_props.ifc_loaded
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.ifclca_props
        
        # Material count info
        total_materials = len(props.material_mappings)
        mapped_materials = sum(1 for m in props.material_mappings if m.is_mapped)
        
        col = layout.column()
        
        # Info box
        box = col.box()
        box.label(text=f"Materials: {mapped_materials}/{total_materials} mapped", 
                 icon='INFO' if mapped_materials < total_materials else 'CHECKMARK')
        
        # Tools row
        row = box.row(align=True)
        row.operator("ifclca.auto_map_materials", icon='AUTO')
        row.prop(props, "filter_mapped", text="Show Unmapped Only", toggle=True)
        
        # Material list
        col.template_list(
            "IFCLCA_UL_MaterialMappingList", "",
            props, "material_mappings",
            props, "active_mapping_index",
            rows=8
        )


class IFCLCA_PT_AnalysisPanel(Panel):
    """Analysis execution panel"""
    bl_label = "Analysis"
    bl_idname = "IFCLCA_PT_analysis_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "IfcLCA"
    bl_parent_id = "IFCLCA_PT_main_panel"
    
    @classmethod
    def poll(cls, context):
        props = context.scene.ifclca_props
        return props.ifc_loaded and any(m.is_mapped for m in props.material_mappings)
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.ifclca_props
        
        col = layout.column()
        
        # Run analysis button
        row = col.row()
        row.scale_y = 1.5
        row.operator("ifclca.run_analysis", icon='PLAY')
        
        # Results section
        if props.show_results and props.results_text:
            col.separator()
            
            box = col.box()
            box.label(text="Results", icon='GRAPH')
            
            # Total in large text with proper formatting
            if props.total_carbon > 0:
                # Main total box
                total_box = box.box()
                total_col = total_box.column()
                
                # Title
                header_row = total_col.row()
                header_row.label(text="Total Embodied Carbon", icon='WORLD')
                
                # Big total value
                total_row = total_col.row()
                total_row.scale_y = 2.0
                if props.total_carbon >= 1000:
                    total_text = f"{props.total_carbon/1000:.2f} t CO₂-eq"
                else:
                    total_text = f"{props.total_carbon:.1f} kg CO₂-eq"
                total_row.label(text=total_text)
                
                # Equivalent info
                total_col.separator()
                equiv_row = total_col.row()
                equiv_row.scale_y = 0.8
                # Car emissions equivalent (avg car emits ~4.6 t CO2/year)
                car_years = props.total_carbon / 4600
                if car_years >= 1:
                    equiv_row.label(text=f"≈ {car_years:.1f} car-years", icon='AUTO')
                else:
                    equiv_row.label(text=f"≈ {car_years*12:.0f} car-months", icon='AUTO')
            
            # Parse results for better display
            col.separator()
            
            # Material breakdown
            materials_box = col.box()
            materials_box.label(text="Material Breakdown", icon='MATERIAL')
            
            # Parse the results text to extract material data
            import re
            materials_data = []
            lines = props.results_text.split('\n')
            
            i = 0
            while i < len(lines):
                line = lines[i]
                # Look for material entries (they don't start with spaces)
                if line and not line.startswith(' ') and not line.startswith('=') and not line.startswith('-') and ':' in line:
                    material_name = line.rstrip(':')
                    material_info = {}
                    
                    # Parse the following indented lines
                    i += 1
                    while i < len(lines) and lines[i].startswith('  '):
                        info_line = lines[i].strip()
                        if ':' in info_line:
                            key, value = info_line.split(':', 1)
                            material_info[key.strip()] = value.strip()
                        i += 1
                    
                    if 'Carbon' in material_info:
                        materials_data.append({
                            'name': material_name,
                            'info': material_info
                        })
                    continue
                i += 1
            
            # Sort by carbon impact
            materials_data.sort(key=lambda x: self._parse_carbon_value(x['info'].get('Carbon', '0')), reverse=True)
            
            # Display top materials
            for idx, mat_data in enumerate(materials_data[:5]):  # Show top 5
                mat_box = materials_box.box()
                mat_col = mat_box.column()
                
                # Material header
                header_row = mat_col.row()
                header_row.label(text=mat_data['name'], icon='MATERIAL_DATA')
                carbon_text = mat_data['info'].get('Carbon', 'N/A')
                header_row.label(text=carbon_text)
                
                # Details row
                detail_row = mat_col.row()
                detail_row.scale_y = 0.8
                
                # Elements info
                if 'Elements' in mat_data['info']:
                    elem_col = detail_row.column()
                    elem_col.label(text=mat_data['info']['Elements'], icon='MESH_CUBE')
                
                # Volume info
                if 'Volume' in mat_data['info']:
                    vol_col = detail_row.column()
                    vol_col.label(text=mat_data['info']['Volume'], icon='SNAP_VOLUME')
                
                # Mass info
                if 'Mass' in mat_data['info']:
                    mass_col = detail_row.column()
                    mass_col.label(text=mat_data['info']['Mass'], icon='RIGID_BODY')
            
            if len(materials_data) > 5:
                materials_box.label(text=f"... and {len(materials_data) - 5} more materials")
            
            # Summary statistics
            col.separator()
            stats_box = col.box()
            stats_box.label(text="Analysis Summary", icon='INFO')
            
            # Extract summary from results
            summary_found = False
            for line in lines:
                if line.strip().startswith('Materials analyzed:'):
                    stats_box.label(text=line.strip())
                elif line.strip().startswith('Materials with impact:'):
                    stats_box.label(text=line.strip())
                elif line.strip().startswith('Materials without volume:'):
                    stats_box.label(text=line.strip())
                    summary_found = True
                    break
            
            # Action buttons
            col.separator()
            row = col.row(align=True)
            row.operator("ifclca.clear_results", text="Clear", icon='X')
            row.operator("ifclca.export_results", text="Export", icon='EXPORT')
            row.operator("ifclca.view_web_results", text="Web", icon='WORLD')
    
    def _parse_carbon_value(self, carbon_str):
        """Parse carbon value from string like '31.59 t CO₂-eq' or '669.7 kg CO₂-eq'"""
        try:
            # Remove CO₂-eq suffix
            value_str = carbon_str.replace('CO₂-eq', '').replace('CO₂e', '').strip()
            
            # Check for tons
            if 't' in value_str:
                value = float(value_str.replace('t', '').strip())
                return value * 1000  # Convert to kg
            else:
                # Assume kg
                value = float(value_str.replace('kg', '').strip())
                return value
        except:
            return 0


class IFCLCA_PT_PreferencesPanel(Panel):
    """Quick access to preferences"""
    bl_label = "Settings"
    bl_idname = "IFCLCA_PT_preferences_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "IfcLCA"
    bl_parent_id = "IFCLCA_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.ifclca_props
        
        col = layout.column()
        
        # Database paths
        if props.database_type == 'OKOBAUDAT':
            col.prop(props, "okobaudat_csv_path")
        elif props.database_type == 'KBOB':
            col.prop(props, "kbob_data_path")
        elif props.database_type == 'CUSTOM':
            col.prop(props, "custom_data_path")
        
        # UI settings
        col.separator()
        col.label(text="Display Options:", icon='PREFERENCES')
        col.prop(props, "show_impact_indicators")
        
        # Link to full preferences
        col.separator()
        col.operator("preferences.addon_show", text="Open Add-on Preferences").module = "ifclca_integration"


# List of classes to register
classes = [
    IFCLCA_UL_MaterialMappingList,
    IFCLCA_UL_MaterialDatabaseList,
    IFCLCA_PT_MainPanel,
    IFCLCA_PT_IFCPanel,
    IFCLCA_PT_MaterialMappingPanel,
    IFCLCA_PT_AnalysisPanel,
    IFCLCA_PT_PreferencesPanel
] 