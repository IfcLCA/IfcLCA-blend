# IfcLCA Add-on Quick Start Guide

This guide will help you test the IfcLCA add-on with a sample IFC file.

## 1. Installation

1. Download the `IfcLCA-blend` folder
2. Zip the folder (right-click > Compress/Zip)
3. In Blender: Edit > Preferences > Add-ons > Install
4. Select the zip file and enable "IfcLCA Integration"

## 2. Test with Sample File

### Load Test IFC

1. Open Blender's 3D View sidebar (press N)
2. Click the "IfcLCA" tab
3. Click "Load IFC File"
4. Navigate to `IfcLCA-blend/test/simple_building.ifc`
5. Click "Load IFC File" button

You should see 3 materials loaded:
- Concrete C30/37
- Steel Reinforcement  
- Brick

### Map Materials

1. Click the eyedropper icon next to "Concrete C30/37"
2. Select "--- Concrete ---" then "Concrete C30/37"
3. Click OK

4. Click the eyedropper next to "Steel Reinforcement"
5. Select "--- Metal ---" then "Reinforcing steel"
6. Click OK

### Run Analysis

1. Click "Calculate Embodied Carbon"
2. View results in the panel

Expected results:
- Concrete C30/37: ~9.4 t CO₂e (wall + slab)
- Reinforcing steel: ~3.8 t CO₂e (slab + column)
- Total: ~13.2 t CO₂e

## 3. Using Your Own IFC

Requirements:
- IFC must have material assignments
- Elements should have BaseQuantities (especially GrossVolume)
- IFC2x3 or IFC4 schema

Tips:
- Export from BIM software with quantities enabled
- Use "Auto-Map Materials" for quick mapping
- Check console for detailed logs

## 4. Using ÖKOBAUDAT

1. Download ÖKOBAUDAT CSV from [oekobaudat.de](https://www.oekobaudat.de/)
2. In Settings panel, set "ÖKOBAUDAT CSV Path"
3. Select "ÖKOBAUDAT" in database dropdown
4. Re-map materials using German database entries

## 5. Troubleshooting

**No materials found**: Check that your IFC has IfcMaterial definitions

**Zero volumes**: Ensure IFC has BaseQuantities or geometry

**Import errors**: Install IfcOpenShell if not using Bonsai

## Example Calculation

For the test file:
- Wall: 3.6 m³ × 2400 kg/m³ × 0.100 kgCO₂/kg = 864 kg CO₂
- Slab: 22 m³ × 2400 kg/m³ × 0.100 kgCO₂/kg = 5,280 kg CO₂  
- Steel: 4.5 m³ × 7850 kg/m³ × 0.750 kgCO₂/kg = 26,494 kg CO₂

This demonstrates the calculation methodology used by the add-on. 