#!/usr/bin/env python3
"""
Standalone example of using IfcLCA logic without Blender.
This demonstrates how the core functionality can be tested or integrated
into other applications.
"""

import os
import sys
import json
import ifcopenshell

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from bundled ifclca_core module
from ifclca_core import get_database_reader
from logic import IfcMaterialExtractor, run_lca_analysis, format_results
from web_interface import launch_results_browser


def main():
    # Example IFC file path
    ifc_path = "test/simple_building.ifc"
    
    if not os.path.exists(ifc_path):
        print(f"Error: IFC file not found at {ifc_path}")
        return
    
    # Load IFC file
    ifc_file = ifcopenshell.open(ifc_path)
    print(f"Loaded IFC file: {ifc_path}")
    
    # Create material extractor
    extractor = IfcMaterialExtractor(ifc_file)
    materials = extractor.get_all_materials()
    
    print(f"\nFound {len(materials)} materials:")
    for mat_name, count in materials:
        print(f"  - {mat_name}: {count} elements")
    
    # Load KBOB database
    db_reader = get_database_reader('KBOB', 'assets/kbob_sample.json')
    
    # Create mapping (example mappings)
    mapping = {
        'Concrete, normal': 'M-10001',  # Map to concrete in KBOB
        'Steel': 'M-10022',              # Map to steel in KBOB
    }
    
    print("\nMaterial mappings:")
    for ifc_mat, db_id in mapping.items():
        if db_id:
            mat_data = db_reader.get_material_data(db_id)
            if mat_data:
                print(f"  {ifc_mat} -> {mat_data['name']}")
    
    # Run analysis
    print("\nRunning LCA analysis...")
    results, detailed_results = run_lca_analysis(ifc_file, db_reader, mapping)
    
    # Print formatted results
    results_text = format_results(results, detailed_results, db_reader)
    print("\n" + results_text)
    
    # Launch interactive web interface
    print("\nLaunching interactive web interface...")
    print("Opening in your default web browser...")
    
    # Launch the web interface with detailed results
    server = launch_results_browser(
        results=detailed_results,  # For backward compatibility
        detailed_results=detailed_results,
        ifc_file=ifc_file
    )
    
    # Keep the server running
    print("\nWeb interface is running at http://localhost:{}".format(server.server_address[1]))
    print("Press Ctrl+C to stop the server...")
    
    try:
        # Keep the script running
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down web server...")
        server.shutdown()
        print("Done.")


if __name__ == "__main__":
    main() 