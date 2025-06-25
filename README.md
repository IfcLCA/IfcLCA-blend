# IfcLCA-blend

IfcLCA-blend is a Blender addon for performing Life Cycle Assessment (LCA) calculations on IFC building models. It integrates with BlenderBIM to provide environmental impact analysis directly within the Blender environment.

## Features

- Load IFC models and analyze building elements
- Assign materials from environmental databases (KBOB, ÖKOBAUDAT)
- Calculate carbon footprint and other environmental indicators
- Web-based visualization interface
- Export results for further analysis

## Installation

1. Install [BlenderBIM](https://blenderbim.org/) addon first
2. Download the IfcLCA-blend addon
3. In Blender: Edit → Preferences → Add-ons → Install
4. Select the downloaded zip file
5. Enable the "IfcLCA" addon

## Project Structure

```
IfcLCA-blend/
├── src/               # Core addon source code
├── assets/            # Database files and web interface
│   ├── indicatorsKBOB_v6.json  # Swiss KBOB database (314+ materials)
│   ├── okobaudat_sample.csv    # German database format
│   └── web/                    # Web visualization interface
├── examples/          # Example scripts
│   └── explore_kbob_database.py  # Database exploration example
├── samples/           # Sample IFC files
│   └── simple_building.ifc      # Basic test model
└── tests/            # Unit tests

## Quick Start

1. Import an IFC file using BlenderBIM
2. Open the IfcLCA panel in Blender's sidebar
3. Select environmental database (KBOB or ÖKOBAUDAT)
4. Assign materials to building elements
5. Calculate environmental impacts
6. View results in the web interface

## Environmental Databases

### KBOB (Swiss)
- 314+ construction materials
- Indicators: GWP, PENRE, UBP
- Pre-loaded from `assets/indicatorsKBOB_v6.json`

### ÖKOBAUDAT (German)
- Import from CSV format
- See `assets/okobaudat_sample.csv` for format

## Examples

See the `examples/` directory for standalone scripts:
- `explore_kbob_database.py` - Browse and search the KBOB database

## Testing

Run tests with pytest:
```bash
cd IfcLCA-blend
python -m pytest tests/
```

## License

Licensed under GNU General Public License v3.0 - see LICENSE file for details.

## Contributing

Contributions welcome! Please feel free to submit issues and pull requests. 