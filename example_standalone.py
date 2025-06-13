#!/usr/bin/env python3
"""
Standalone example of using IfcLCA logic without Blender.
This demonstrates how the core functionality can be tested or integrated
into other applications.
"""

import os
import sys
import ifcopenshell

# Add the addon directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from database_reader import get_database_reader
from logic import IfcMaterialExtractor, SimplifiedIfcLCAAnalysis, format_results


def main():
    # 1. Load IFC file
    print("Loading IFC file...")
    ifc_path = "test/simple_building.ifc"
    
    if not os.path.exists(ifc_path):
        print(f"Error: Test file not found at {ifc_path}")
        return
    
    ifc = ifcopenshell.open(ifc_path)
    print(f"Loaded: {ifc.schema} file with {len(ifc.by_type('IfcElement'))} elements")
    
    # 2. Extract materials
    print("\nExtracting materials...")
    extractor = IfcMaterialExtractor(ifc)
    materials = extractor.get_all_materials()
    
    print("Found materials:")
    for mat_name, count in materials:
        print(f"  - {mat_name}: {count} elements")
    
    # 3. Setup database reader
    print("\nLoading KBOB database...")
    db_reader = get_database_reader('KBOB')
    
    # 4. Create material mapping
    # For this example, we'll map automatically based on name similarity
    mapping = {}
    
    # Manual mapping for the test file
    mapping_rules = {
        "Concrete C30/37": "KBOB_CONCRETE_C30_37",
        "Steel Reinforcement": "KBOB_STEEL_REINFORCING",
        "Brick": "KBOB_BRICK_CLAY"
    }
    
    for mat_name, count in materials:
        if mat_name in mapping_rules:
            mapping[mat_name] = mapping_rules[mat_name]
            db_entry = db_reader.get_material_data(mapping_rules[mat_name])
            print(f"\nMapped '{mat_name}' to '{db_entry['name']}'")
    
    # 5. Run analysis
    print("\nRunning LCA analysis...")
    analysis = SimplifiedIfcLCAAnalysis(ifc, db_reader, mapping)
    results = analysis.run()
    detailed_results = analysis.get_detailed_results()
    
    # 6. Display results
    print("\n" + "="*50)
    formatted_results = format_results(results, detailed_results, db_reader)
    print(formatted_results)
    
    # 7. Additional statistics
    print("\n" + "="*50)
    print("Analysis Summary:")
    print(f"  Materials analyzed: {len(detailed_results)}")
    print(f"  Total elements: {sum(r['element_count'] for r in detailed_results.values())}")
    print(f"  Total volume: {sum(r['total_volume'] for r in detailed_results.values()):.2f} m³")
    print(f"  Total mass: {sum(r['total_mass'] for r in detailed_results.values()):.0f} kg")
    
    # 8. Export results (example)
    print("\nResults could be exported to:")
    print("  - CSV file for further analysis")
    print("  - JSON for web integration")
    print("  - IFC properties for BIM roundtrip")


if __name__ == "__main__":
    main() 