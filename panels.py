try:
    import bpy
    from bpy.types import Panel, UIList
except ImportError:
    # For testing
    from unittest.mock import MagicMock
    Panel = type
    UIList = type

# Try to import Bonsai to check if available
try:
    from bonsai.bim import tool
    HAS_BONSAI = True
except ImportError:
    HAS_BONSAI = False


class IFCLCA_UL_MaterialMappingList(UIList):
    """UI List for material mappings"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        props = context.scene.ifclca_props
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            
            # Material name
            row.label(text=item.ifc_material_name, icon='MATERIAL')
            
            # Mapping status/button
            if item.is_mapped:
                row.label(text=item.database_name, icon='CHECKMARK')
            else:
                row.label(text="Not mapped", icon='ERROR')
            
            # Map button
            op = row.operator("ifclca.map_material", text="", icon='EYEDROPPER')
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
        
        # IFC loading options
        if not props.ifc_loaded:
            col.operator("ifclca.load_ifc", icon='FILE_FOLDER')
            if HAS_BONSAI:
                col.operator("ifclca.use_active_ifc", icon='FILE_REFRESH')
        else:
            # Show loaded file info
            box = col.box()
            box.label(text="IFC File Loaded", icon='CHECKMARK')
            if props.ifc_file_path != "Active Bonsai IFC":
                box.label(text=f"File: {props.ifc_file_path.split('/')[-1]}")
            
            # Reload options
            row = box.row()
            row.operator("ifclca.load_ifc", text="Load Different IFC", icon='FILE_FOLDER')
            if HAS_BONSAI:
                row.operator("ifclca.use_active_ifc", text="Refresh", icon='FILE_REFRESH')


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
            
            # Total in large text
            if props.total_carbon > 0:
                total_box = box.box()
                if props.total_carbon >= 1000:
                    total_text = f"Total: {props.total_carbon/1000:.2f} t CO₂e"
                else:
                    total_text = f"Total: {props.total_carbon:.1f} kg CO₂e"
                total_box.label(text=total_text, icon='WORLD')
            
            # Detailed results (scrollable text)
            results_lines = props.results_text.split('\n')
            for i, line in enumerate(results_lines[:20]):  # Limit lines shown
                if line.strip():
                    if line.startswith("==="):
                        box.separator()
                    elif line.startswith("---"):
                        box.separator()
                    elif line.startswith("TOTAL:"):
                        row = box.row()
                        row.alert = True
                        row.label(text=line)
                    else:
                        box.label(text=line)
            
            if len(results_lines) > 20:
                box.label(text="... (see console for full results)")
            
            # Clear button
            box.operator("ifclca.clear_results", icon='X')


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
        
        # Link to full preferences
        col.separator()
        col.operator("preferences.addon_show", text="Open Add-on Preferences").module = "ifclca_integration"


# List of classes to register
classes = [
    IFCLCA_UL_MaterialMappingList,
    IFCLCA_PT_MainPanel,
    IFCLCA_PT_IFCPanel,
    IFCLCA_PT_MaterialMappingPanel,
    IFCLCA_PT_AnalysisPanel,
    IFCLCA_PT_PreferencesPanel
] 