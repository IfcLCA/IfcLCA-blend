"""
Quick Start Script for IfcLCA with Bonsai/BlenderBIM

Run this in Blender's Python console to quickly load and analyze the active IFC.

Usage:
1. Load your IFC in Bonsai/BlenderBIM first
2. Run this script in Blender's Text Editor or Python Console
"""

import bpy
import sys

# Add the addon path if needed
addon_path = r'C:\Users\louistrue\Documents\GitHub\LCA\IfcLCA-blend'
if addon_path not in sys.path:
    sys.path.append(addon_path)

def quick_start():
    """Quick start function to load active IFC and prepare for analysis"""
    
    print("=== IfcLCA Quick Start ===")
    
    # Check if addon is enabled
    if 'IfcLCA-blend' not in bpy.context.preferences.addons:
        print("ERROR: IfcLCA addon not enabled!")
        print("Please enable it in Edit > Preferences > Add-ons")
        return False
    
    # Get the active IFC from Bonsai
    try:
        # Import Bonsai IfcStore
        from bonsai.bim.ifc import IfcStore
        
        ifc = IfcStore.get_file()
        if not ifc:
            print("ERROR: No IFC loaded in Bonsai/BlenderBIM!")
            print("Please load an IFC file first using Bonsai")
            return False
        
        print(f"✓ Found active IFC: {ifc.schema}")
        
        # Use the active IFC in IfcLCA
        print("Loading IFC into IfcLCA...")
        bpy.ops.ifclca.use_active_ifc()
        
        # Check results
        props = bpy.context.scene.ifclca_props
        if props.ifc_loaded:
            print(f"✓ IFC loaded successfully!")
            print(f"✓ Found {len(props.material_mappings)} materials")
            
            # Show material summary
            if props.material_mappings:
                print("\nMaterials found:")
                for i, mat in enumerate(props.material_mappings[:10]):
                    status = "✓" if mat.is_mapped else "✗"
                    print(f"  {status} {mat.ifc_material_name}")
                if len(props.material_mappings) > 10:
                    print(f"  ... and {len(props.material_mappings) - 10} more")
            
            print("\nNext steps:")
            print("1. Map materials in the Material Mapping panel")
            print("2. Or run: bpy.ops.ifclca.auto_map_materials()")
            print("3. Then run: bpy.ops.ifclca.run_analysis()")
            
            return True
        else:
            print("ERROR: Failed to load IFC")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def auto_analyze():
    """Automatically map materials and run analysis"""
    
    props = bpy.context.scene.ifclca_props
    if not props.ifc_loaded:
        print("ERROR: No IFC loaded. Run quick_start() first!")
        return False
    
    print("\n=== Auto Analysis ===")
    
    # Auto-map materials
    print("Auto-mapping materials...")
    bpy.ops.ifclca.auto_map_materials()
    
    # Check mapping results
    mapped = sum(1 for m in props.material_mappings if m.is_mapped)
    print(f"✓ Mapped {mapped}/{len(props.material_mappings)} materials")
    
    if mapped == 0:
        print("WARNING: No materials could be auto-mapped")
        print("Please map materials manually in the UI")
        return False
    
    # Run analysis
    print("Running LCA analysis...")
    bpy.ops.ifclca.run_analysis()
    
    if props.show_results:
        print(f"\n✓ Analysis complete!")
        print(f"Total embodied carbon: {props.total_carbon:.1f} kg CO₂e")
        print("\nSee the Analysis panel for detailed results")
        return True
    else:
        print("ERROR: Analysis failed")
        return False

def diagnose():
    """Run diagnostics on the current setup"""
    
    print("\n=== IfcLCA Diagnostics ===")
    
    # Check addon
    if 'IfcLCA-blend' in bpy.context.preferences.addons:
        print("✓ IfcLCA addon enabled")
    else:
        print("✗ IfcLCA addon not enabled")
    
    # Check Bonsai
    try:
        from bonsai.bim.ifc import IfcStore
        print("✓ Bonsai/BlenderBIM available")
        
        ifc = IfcStore.get_file()
        if ifc:
            print(f"✓ Active IFC found: {ifc.schema}")
            elements = ifc.by_type("IfcElement")
            print(f"  - Elements: {len(elements)}")
            materials = ifc.by_type("IfcMaterial")
            print(f"  - Materials: {len(materials)}")
        else:
            print("✗ No active IFC in Bonsai")
            
    except ImportError:
        print("✗ Bonsai/BlenderBIM not available")
    
    # Check IfcLCA state
    try:
        props = bpy.context.scene.ifclca_props
        print(f"\nIfcLCA state:")
        print(f"  - IFC loaded: {props.ifc_loaded}")
        print(f"  - Materials: {len(props.material_mappings)}")
        print(f"  - Database: {props.database_type}")
    except:
        print("✗ IfcLCA properties not available")

# Print usage instructions
print("""
IfcLCA Quick Start loaded!

Available functions:
  quick_start()  - Load active IFC from Bonsai
  auto_analyze() - Auto-map materials and run analysis
  diagnose()     - Check your setup

Example workflow:
  1. Load IFC in Bonsai/BlenderBIM
  2. Run: quick_start()
  3. Run: auto_analyze()
""")

# Auto-run quick start if IFC is detected
try:
    from bonsai.bim.ifc import IfcStore
    if IfcStore.get_file():
        print("\nActive IFC detected! Running quick_start()...\n")
        quick_start()
except:
    pass 