# IfcLCA-blend

**Early Prototype** - A Blender addon for IFC-based Life Cycle Assessment (LCA) calculations.

⚠️ **Current Status**: This is an initial prototype using mock carbon data for development and testing purposes.

## What It Does

This Blender addon allows you to:
- Load IFC building models in Blender
- Extract material information from IFC elements
- Map materials to environmental databases (KBOB, CSV)
- Calculate basic embodied carbon estimates
- View results in an interactive web interface

## Current Limitations

- **Mock Data**: Uses placeholder carbon values for development
- **Prototype Stage**: Basic functionality, not production-ready
- **Limited Database Support**: Basic KBOB and CSV parsing
- **No Real LCA**: Simplified calculations for proof-of-concept

## Repository Structure

```
IfcLCA-blend/
├── src/                    # Python source code
├── tests/                  # Unit tests
├── tools/                  # Build and packaging scripts
├── assets/                 # Web interface and sample files
├── samples/               # Example IFC files
├── .github/               # GitHub configuration
└── LICENSE                # MIT License
```

## Installation (For Testing)

1. Download or build the addon zip
2. In Blender: Edit > Preferences > Add-ons > Install
3. Enable "Import-Export: IfcLCA"

## Usage

1. Open an IFC file in Blender (use BlenderBIM addon)
2. Go to Scene Properties panel
3. Find "IFC LCA" section
4. Load a database file (sample files in assets/)
5. Map materials and run analysis
6. View results in web browser

## Building

```bash
# Package for distribution
./tools/package.sh
```

## Development Status

This is an **early prototype** created to explore:
- IFC material extraction workflows
- Blender addon architecture
- Web-based results visualization
- Database integration patterns

Not suitable for real LCA calculations yet.

## Dependencies

- Blender 3.0+
- IfcOpenShell (for IFC processing)
- IfcLCA-Py (separate library, in development)

## License

MIT License - see [LICENSE](LICENSE) 