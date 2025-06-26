#!/usr/bin/env python3
"""
Example script to test KBOB JSON loading

This demonstrates how the KBOB database is loaded from indicatorsKBOB_v6.json
"""

import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database_reader import KBOBDatabaseReader

def main():
    """Test KBOB JSON loading"""
    
    # Load KBOB database
    print("Loading KBOB database from JSON...")
    reader = KBOBDatabaseReader()
    
    print(f"\nLoaded {len(reader.data)} materials from KBOB database")
    
    # Show some statistics
    categories = {}
    for _, _, category in reader.materials_list:
        categories[category] = categories.get(category, 0) + 1
    
    print("\nMaterials by category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count} materials")
    
    # Search for concrete materials
    print("\nSearching for 'beton' (concrete)...")
    results = reader.search_materials('beton')
    print(f"Found {len(results)} concrete materials")
    
    # Show first 5 concrete materials
    for i, (mat_id, name, category) in enumerate(results[:5]):
        material = reader.get_material_data(mat_id)
        print(f"\n{i+1}. {name}")
        print(f"   ID: {mat_id}")
        print(f"   Category: {category}")
        print(f"   GWP: {material['carbon_per_unit']:.3f} kg CO₂-eq/kg")
        if material['density']:
            print(f"   Density: {material['density']} kg/m³")
        else:
            print(f"   Density: Not specified")
        if material.get('penre'):
            print(f"   PENRE: {material['penre']} MJ/kg")
    
    # Show some insulation materials
    print("\n\nSearching for insulation materials...")
    insulation = [(id, name, cat) for id, name, cat in reader.materials_list 
                  if cat == 'Insulation']
    print(f"Found {len(insulation)} insulation materials")
    
    for i, (mat_id, name, category) in enumerate(insulation[:3]):
        material = reader.get_material_data(mat_id)
        print(f"\n{i+1}. {name}")
        print(f"   GWP: {material['carbon_per_unit']:.3f} kg CO₂-eq/kg")
        if material['density']:
            print(f"   Density: {material['density']} kg/m³")
    
    # Show materials with negative GWP (carbon storing)
    print("\n\nMaterials with negative GWP (carbon storing):")
    carbon_negative = []
    for mat_id, mat_data in reader.data.items():
        if mat_data['carbon_per_unit'] < 0:
            carbon_negative.append((mat_id, mat_data))
    
    print(f"Found {len(carbon_negative)} carbon-negative materials")
    for mat_id, mat_data in carbon_negative[:3]:
        print(f"\n- {mat_data['name']}")
        print(f"  GWP: {mat_data['carbon_per_unit']:.3f} kg CO₂-eq/kg")

if __name__ == '__main__':
    main() 