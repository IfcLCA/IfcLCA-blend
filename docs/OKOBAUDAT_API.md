# Ökobaudat API Integration

This document describes how to use the Ökobaudat API integration in IfcLCA-blend.

## Overview

The Ökobaudat API integration allows you to access the German environmental database directly from Blender without downloading CSV files. The integration automatically filters results for EN 15804+A2 compliance.

## Features

- Direct API access to Ökobaudat database
- Real-time material search
- EN 15804+A2 compliant data only
- Automatic data transformation to match KBOB format
- Optional API key support
- Full environmental indicators (GWP, PENRE)
- **Bundled dependencies** - no additional installation required

## Setup

1. In Blender, go to the IfcLCA panel in the 3D View sidebar
2. Select "ÖKOBAUDAT API" from the database dropdown
3. (Optional) Enter your API key if you have one
4. The integration is ready to use!

**Note:** The addon includes all necessary dependencies bundled, so no additional installation is required.

## Using the API

### Searching for Materials

1. Load your IFC file as usual
2. In the Material Mapping panel, click "Select Material" for any unmapped material
3. In the Material Database Browser:
   - Use the Ökobaudat search box to search for materials
   - Click "Search" to query the API
   - Results will be filtered for EN 15804+A2 compliance
   - Select a material from the results

### API Key

While an API key is optional, it's recommended for:
- Higher rate limits
- Access to extended data
- Better performance

To obtain an API key, visit: https://www.oekobaudat.de/

## Data Format

The API data is automatically transformed to match the KBOB format:

```python
{
    "name": "Material name",
    "category": "Material category",
    "density": 2400,  # kg/m³
    "carbon_per_unit": 0.105,  # kg CO₂-eq/kg
    "unit": "kg CO₂-eq/kg",
    "penre": 0.834,  # Primary Energy Non-Renewable
    "okobaudat_id": "uuid-string"
}
```

## Technical Details

### API Endpoints Used

- Base URL: `https://oekobaudat.de/OEKOBAU.DAT/resource`
- Datastock: `cd2bda71-760b-4fcc-8a0b-3877c10000a8`
- EN 15804+A2 compliance filter: `c0016b33-8cf7-415c-ac6e-deba0d21440d`

### API Calls

1. **Search materials**: 
   ```
   GET /datastocks/{id}/processes?search=true&compliance={A2_UUID}&name={query}
   ```

2. **Get full EPD data**:
   ```
   GET /datastocks/{id}/processes/{epd_id}?format=json&view=extended
   ```

## Example Code

```python
from database_reader import OkobaudatAPIReader

# Create reader with optional API key
reader = OkobaudatAPIReader(api_key="your-api-key")

# Search for concrete materials
reader.load_materials(search_query="Beton", limit=10)

# Get all results
materials = reader.get_all_materials()

# Get full data for a specific material
full_data = reader.get_full_material_data("OKOBAU_uuid")
```

## Troubleshooting

### No results found
- Try broader search terms
- Check your internet connection
- Verify API key if using one

### Slow performance
- Consider getting an API key
- Reduce search result limit
- Cache frequently used materials

### Data compatibility
- All data is automatically transformed to KBOB format
- Density might not be available for all materials
- GWP values are normalized to kg CO₂-eq/kg where possible

## References

- [Ökobaudat Website](https://www.oekobaudat.de/)
- [Developer Documentation](https://www.oekobaudat.de/anleitungen/softwareentwickler.html)
- [EN 15804+A2 Standard](https://www.en-standard.eu/) 