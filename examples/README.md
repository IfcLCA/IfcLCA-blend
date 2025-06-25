# IfcLCA Examples

This directory contains example scripts demonstrating how to use the IfcLCA-blend addon components programmatically.

## Available Examples

### explore_kbob_database.py
Demonstrates how to load and explore the KBOB (Swiss) environmental database.

**Features:**
- Loading the KBOB database from JSON
- Browsing materials by category
- Searching for specific materials
- Displaying environmental indicators (GWP, PENRE, UBP)
- Finding materials with specific properties

**Usage:**
```bash
python3 explore_kbob_database.py
```

## Sample Data

The `samples/` directory contains example IFC files for testing:
- `simple_building.ifc` - A basic building model with concrete and steel elements

## Database Files

The environmental databases are stored in the `assets/` directory:
- `indicatorsKBOB_v6.json` - Full KBOB database with 314+ materials
- `okobaudat_sample.csv` - Sample ÖKOBAUDAT (German) database format

## Running Examples

All examples can be run standalone from the command line:

```bash
cd IfcLCA-blend
python3 examples/[example_name].py
```

The examples are designed to work independently of Blender for testing and development purposes. 