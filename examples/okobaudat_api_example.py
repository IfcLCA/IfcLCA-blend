"""
Example script demonstrating Ökobaudat API integration with IfcLCA

This script shows how to:
1. Connect to Ökobaudat API
2. Search for materials
3. Get environmental data (GWP, PENRE)
4. Use the data in LCA calculations
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database_reader import OkobaudatAPIReader


def main():
    """Example usage of Ökobaudat API"""
    
    # Create API reader (API key is optional)
    api_key = None  # Set your API key here if you have one
    reader = OkobaudatAPIReader(api_key=api_key)
    
    print("=== Ökobaudat API Example ===\n")
    
    # Example 1: Search for concrete materials
    print("1. Searching for concrete materials...")
    reader.load_materials(search_query="Beton", limit=10)
    
    concrete_materials = reader.get_all_materials()
    print(f"Found {len(concrete_materials)} concrete materials\n")
    
    # Display first few results
    for i, mat in enumerate(concrete_materials[:3]):
        print(f"Material {i+1}:")
        print(f"  ID: {mat['id']}")
        print(f"  Name: {mat['name']}")
        print(f"  Category: {mat['category']}")
        print(f"  GWP: {mat['gwp']} kg CO₂-eq/kg")
        print(f"  Density: {mat['density']} kg/m³")
        print()
    
    # Example 2: Get full material data
    if concrete_materials:
        print("\n2. Getting full data for first material...")
        first_material_id = concrete_materials[0]['id']
        full_data = reader.get_full_material_data(first_material_id)
        
        print(f"Full data for {full_data.get('name', 'Unknown')}:")
        print(f"  Carbon per unit: {full_data.get('carbon_per_unit', 0)}")
        print(f"  Unit: {full_data.get('unit', 'N/A')}")
        print(f"  PENRE: {full_data.get('penre', 0)}")
        print(f"  Declared unit: {full_data.get('declared_unit', 'N/A')}")
        print(f"  Reference flow: {full_data.get('reference_flow_amount', 0)}")
    
    # Example 3: Search for insulation materials
    print("\n3. Searching for insulation materials...")
    reader.load_materials(search_query="Dämmung", limit=5)
    
    insulation_materials = reader.get_all_materials()
    print(f"Found {len(insulation_materials)} insulation materials")
    
    # Example 4: Calculate embodied carbon for a simple element
    print("\n4. Example calculation:")
    if concrete_materials:
        # Assume we have a concrete wall: 10m³ volume
        volume_m3 = 10
        material = concrete_materials[0]
        
        # Get full material data for accurate calculation
        full_data = reader.get_full_material_data(material['id'])
        
        density = full_data.get('density', 2400)  # Default concrete density
        gwp_per_kg = full_data.get('carbon_per_unit', 0)
        
        if density and gwp_per_kg:
            mass_kg = volume_m3 * density
            total_gwp = mass_kg * gwp_per_kg
            
            print(f"Concrete wall calculation:")
            print(f"  Material: {material['name']}")
            print(f"  Volume: {volume_m3} m³")
            print(f"  Density: {density} kg/m³")
            print(f"  Mass: {mass_kg:.0f} kg")
            print(f"  GWP per kg: {gwp_per_kg:.4f} kg CO₂-eq/kg")
            print(f"  Total GWP: {total_gwp:.0f} kg CO₂-eq")
        else:
            print("Insufficient data for calculation")
    
    print("\n=== End of example ===")


if __name__ == "__main__":
    main() 