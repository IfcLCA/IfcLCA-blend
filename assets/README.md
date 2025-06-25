# IfcLCA Assets

This directory contains data files and web interface assets for the IfcLCA-blend addon.

## Environmental Databases

### indicatorsKBOB_v6.json
The complete KBOB (Koordinationskonferenz der Bau- und Liegenschaftsorgane der öffentlichen Bauherren) database from Switzerland.

- **Materials**: 314+ construction materials
- **Indicators**: 
  - GWP (Global Warming Potential) in g CO₂-eq/kg
  - PENRE (Primary Energy Non-Renewable) in MJ/kg
  - UBP (Environmental Impact Points) where available
- **Categories**: Concrete, Metal, Wood, Insulation, etc.
- **Format**: JSON array with material properties

### okobaudat_sample.csv
Sample format for ÖKOBAUDAT (German environmental database).

- **Format**: CSV with columns for ID, Name, Category, Density, GWP100, Unit
- **Usage**: Template for importing German environmental data

## Web Interface

### web/
Contains the web-based visualization interface for LCA results:

- `index.html` - Main interface page
- `js/` - JavaScript files for data visualization and interaction
- `css/` - Styling for the web interface

The web interface allows users to:
- View material assignments and carbon calculations
- Explore results by building element
- Generate charts and reports
- Export data for further analysis 