# IfcLCA Blender Add-on

A Blender add-on that integrates life cycle assessment (LCA) capabilities for IFC building models, using environmental impact databases like Swiss KBOB and German ÖKOBAUDAT.

## Features

- **IFC Model Integration**: Load IFC files directly or use active Bonsai IFC models
- **Material Mapping**: Map IFC materials to environmental impact database entries
- **Embodied Carbon Calculation**: Calculate total embodied carbon (GWP) for building models
- **Multiple Database Support**: Built-in KBOB data and support for ÖKOBAUDAT CSV import
- **Intuitive UI**: Clean interface in Blender's 3D View sidebar


## Installation

1. Download or clone this repository
2. In Blender, go to Edit > Preferences > Add-ons
3. Click "Install..." and select the `IfcLCA-blend` folder (or zip it first)
4. Enable the "IfcLCA Integration" add-on
5. The IfcLCA tab will appear in the 3D View sidebar (press N to toggle)

## Usage

### 1. Select LCA Database

In the IfcLCA panel, choose your preferred database:
- **KBOB 2022**: Swiss database with built-in data for common materials
- **ÖKOBAUDAT**: German database (requires CSV download)

### 2. Load IFC Model

Two options:
- **Load IFC File**: Browse and select an IFC file
- **Use Active IFC**: Use the IFC currently loaded in Bonsai (if available)

### 3. Map Materials

After loading, all materials found in the IFC will be listed:
1. Click the eyedropper icon next to each material
2. Select the corresponding database entry from the dropdown
3. Use "Auto-Map Materials" to attempt automatic matching by name

### 4. Run Analysis

Click "Calculate Embodied Carbon" to:
- Process all mapped materials
- Extract element volumes from IFC BaseQuantities
- Calculate mass using material densities
- Compute total embodied carbon using emission factors
- Display results by material and total

## Database Configuration

### KBOB (Swiss)

The add-on includes a subset of KBOB 2022 data. For custom KBOB data:
1. Create a JSON file with the structure shown in `assets/kbob_sample.json`
2. Set the path in Settings > KBOB Data Path

### ÖKOBAUDAT (German)

1. Download the ÖKOBAUDAT CSV from [oekobaudat.de](https://www.oekobaudat.de/)
2. In Settings, set the ÖKOBAUDAT CSV Path
3. The add-on will parse the CSV on first use

Expected CSV columns:
- ID: Unique identifier
- Name: Material name
- Category: Material category
- Density: kg/m³
- GWP100: Global Warming Potential (kgCO₂e/kg or kgCO₂e/m³)
- Unit: Reference unit

## Technical Details

### Architecture

- **`__init__.py`**: Add-on registration and bl_info
- **`properties.py`**: Data structures and settings
- **`operators.py`**: Core functionality (load, map, analyze)
- **`panels.py`**: UI panels for 3D View sidebar
- **`database_reader.py`**: Database loading and querying
- **`logic.py`**: IFC analysis and LCA calculations

### IFC Integration

The add-on uses IfcOpenShell to:
- Parse IFC files
- Extract material assignments
- Retrieve element quantities (BaseQuantities)
- Support both standalone use and Bonsai integration

### Calculation Method

For each mapped material:
1. Find all IFC elements using that material
2. Get element volume from BaseQuantities (e.g., Qto_WallBaseQuantities.GrossVolume)
3. Calculate mass: volume × density
4. Calculate carbon: mass × emission factor
5. Sum all materials for total

## Contributing

This add-on is designed for potential inclusion in the [ifcopenshell/bonsai](https://github.com/ifcopenshell/bonsai) project. Contributions should follow:

- Clear code documentation
- Blender API best practices
- Separation of UI and logic
- PEP 8 style guidelines

## License

AGPL v3 (compatible with IfcOpenShell/Bonsai GPL v3)

## Requirements

- Blender 3.6+
- IfcOpenShell (included with Bonsai or install separately)
- Optional: Bonsai add-on for enhanced integration

## Future Enhancements

- Additional environmental indicators beyond GWP100
- Export results to IFC properties
- Visualization of carbon hotspots
- Support for more databases (ICE, ecoinvent)
- Quantity takeoff improvements
- Uncertainty analysis

## Troubleshooting

**"No volume found" warnings**: Ensure your IFC model includes BaseQuantities. If not, future versions will support geometric volume calculation.

**Materials not mapping**: Check that material names in IFC match database entries, or use manual mapping.

**ÖKOBAUDAT not loading**: Verify CSV format matches expected columns and encoding is UTF-8. 