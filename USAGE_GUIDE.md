# IfcLCA Blender Add-on Usage Guide

## Installation & Setup

1. **Install the Add-on**
   - In Blender: Edit > Preferences > Add-ons > Install
   - Select the IfcLCA-blend folder or zip file
   - Enable the "IfcLCA Integration" add-on

2. **Restart Blender** after making any code changes to ensure properties are loaded

## Using with Bonsai/BlenderBIM

The add-on automatically detects if you have an IFC file loaded in Bonsai:

1. Load your IFC file in Bonsai first
2. Go to the IfcLCA panel in the 3D View sidebar
3. Click "Use Active IFC" to use the Bonsai-loaded file
4. The add-on will analyze the IFC structure and extract materials

## Debugging Empty IFC Files

### Enable Console Logging

In Blender's Python console:
```python
# Access the IfcLCA logger
bpy.ifclca_logger.setLevel(10)  # DEBUG level
bpy.ifclca_logger.info("Test message")

# Run diagnostic on loaded IFC
import sys
sys.path.append(r'C:\Users\louistrue\Documents\GitHub\LCA\IfcLCA-blend')
from ifc_diagnostic import diag_active
diag_active()  # Diagnose the active Bonsai IFC
```

### Common Issues & Solutions

1. **"IFC Model Empty"**
   - Check console output for element counts
   - Look for "No IfcElements found" warning
   - Verify IFC has geometric representations
   - Ensure elements are in spatial tree

2. **"Materials Not Found"**
   - Check if IFC has material definitions
   - Look for IfcMaterial, IfcMaterialLayerSet entities
   - Materials might be defined differently than expected

3. **"AttributeError: 'IfcLCAProperties' object has no attribute"**
   - Disable and re-enable the add-on
   - Restart Blender completely
   - Check that properties.py has all required properties

### Console Commands for Debugging

```python
# Check if IFC is loaded
import bpy
props = bpy.context.scene.ifclca_props
print(f"IFC Loaded: {props.ifc_loaded}")
print(f"Materials: {len(props.material_mappings)}")

# Force reload from Bonsai
bpy.ops.ifclca.use_active_ifc()

# Check material mappings
for mat in props.material_mappings:
    print(f"{mat.ifc_material_name}: {'Mapped' if mat.is_mapped else 'Not mapped'}")

# Run analysis with debug output
bpy.ifclca_logger.setLevel(10)
bpy.ops.ifclca.run_analysis()
```

### Diagnostic Script Usage

For detailed IFC file analysis:
```python
# Diagnose a specific file
from ifc_diagnostic import diagnose_ifc_file
diagnose_ifc_file(r"C:\path\to\your\file.ifc")

# Or diagnose active Bonsai IFC
from ifc_diagnostic import diag_active
diag_active()
```

## Workflow

1. **Load IFC** (from file or Bonsai)
2. **Check Materials** in Material Mapping panel
3. **Map Materials** to database entries (auto-map or manual)
4. **Run Analysis** to calculate embodied carbon
5. **View Results** in the Analysis panel

## Tips

- Use "Auto-Map Materials" for quick setup
- Filter to show only unmapped materials
- Check console for detailed logging
- Refresh from Bonsai if IFC changes
- Results show both total and per-material breakdown

## Troubleshooting Empty Results (0.0 kg CO₂e)

If your analysis returns 0.0 kg CO₂e, check:

1. **Enable Debug Logging**
   ```python
   bpy.ifclca_logger.setLevel(10)  # DEBUG level
   ```

2. **Common Issues:**
   - **No Volume Data**: Many IFC files lack quantity data
     - Check console for "No volume found" messages
     - Elements need BaseQuantities or dimensions
   - **Materials Not Mapped**: Auto-mapping may miss some materials
     - Check Material Mapping panel
     - Manually map unmatched materials
   - **Database Missing Data**: Some materials lack carbon data
     - Check if density and carbon values exist

3. **Verify IFC Has Quantities**
   ```python
   from bonsai.bim.ifc import IfcStore
   ifc = IfcStore.get_file()
   
   # Check if elements have quantities
   for element in ifc.by_type("IfcWall")[:5]:
       psets = ifcopenshell.util.element.get_psets(element)
       print(f"{element.Name}: {list(psets.keys())}")
   ```

4. **Manual Material Mapping**
   - Click the eyedropper icon next to unmapped materials
   - Search for appropriate database entries
   - Common mappings:
     - "Reinforced concrete" → "Concrete C25/30"
     - "Metal - steel" → "Structural steel"
     - "Wood" → "Glulam timber" 