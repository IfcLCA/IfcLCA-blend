# IfcLCA Sample Files

This directory contains sample IFC files for testing the IfcLCA-blend addon.

## Available Samples

### simple_building.ifc
A basic building model designed to test core LCA functionality.

**Contents:**
- Foundation elements (concrete)
- Structural columns and beams (concrete/steel)
- Floor slabs
- Basic walls

**Usage:**
1. Import into Blender using the BlenderBIM addon
2. Run the IfcLCA analysis
3. Assign materials from the KBOB database
4. Calculate environmental impacts

**Properties:**
- IFC version: IFC4
- Size: ~3KB
- Elements: Basic structural components

## Creating Test Models

When creating new test IFC files:
1. Keep models simple and focused on specific test cases
2. Include clear element types and materials
3. Use standard IFC classifications
4. Document the purpose and contents

## Notes

These sample files are intentionally simple to:
- Facilitate quick testing
- Demonstrate basic functionality
- Serve as templates for more complex models
- Help with debugging and development 