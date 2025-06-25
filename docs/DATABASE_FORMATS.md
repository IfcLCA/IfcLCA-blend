# Database Formats

The IfcLCA-blend addon supports multiple environmental database formats for Life Cycle Assessment calculations.

## KBOB Database (Swiss)

The KBOB database is loaded from `assets/indicatorsKBOB_v6.json` and contains 314+ construction materials with environmental impact data.

### Data Structure

Each material entry includes:
- **KBOB_ID**: Unique identifier (e.g., "1.001", "02.002.01")
- **Name**: Material name in German
- **GWP**: Global Warming Potential in g CO₂-eq/kg (converted to kg internally)
- **PENRE**: Primary Energy Non-Renewable in MJ/kg
- **UBP**: Environmental Impact Points (Swiss method)
- **kg/unit**: Density in kg/m³ (for 237 materials)
- **min/max density**: Alternative density range (averaged if kg/unit not available)

### Density Extraction

The addon automatically extracts density information:
- Primary source: `kg/unit` field (when not "-")
- Secondary source: Average of `min density` and `max density` fields
- 237 materials have density data (bulk materials)
- 77 materials have no density (surface treatments, coatings)

### Categories

Materials are automatically categorized based on KBOB_ID ranges:
- 0.xxx: Foundation/Excavation
- 1.xxx: Concrete
- 2.xxx: Masonry
- 3.xxx: Mineral/Stone
- 4.xxx: Mortar/Plaster
- 5.xxx: Facade/Windows
- 6.xxx: Metal
- 7.xxx: Wood
- 8.xxx: Sealants/Adhesives
- 9.xxx: Membranes/Foils
- 10.xxx: Insulation
- 11.xxx: Flooring
- 12.xxx: Doors
- 13.xxx: Plastics/Pipes
- 14.xxx: Coatings
- 15.xxx: Other Materials
- 21.xxx: Kitchen/Interior

## ÖKOBAUDAT Database (German)

Loaded from CSV files with flexible column naming support.

### Supported Columns
- **Name**: Name_de, Name, Material
- **Category**: Category_de, Category, Kategorie
- **Density**: Rohdichte, Density (kg/m³)
- **GWP**: GWP-total, GWP100, Treibhauspotenzial
- **PENR**: PENRT, PENR, PEne

### Unit Normalization
The reader automatically normalizes values to per-kg basis:
- If reference unit is m³, values are divided by density
- If reference quantity ≠ 1, values are divided by quantity

## Custom JSON Format

For custom databases, use this structure:

```json
{
  "MATERIAL_ID": {
    "name": "Material Name",
    "category": "Category",
    "density": 2300,  // kg/m³
    "gwp": 0.1,      // kg CO₂-eq/kg
    "penr": 0.5,     // MJ/kg
    "ubp": 150,      // Environmental points/kg
    "unit": "kg"
  }
}
```

## Data Quality

The addon includes automatic filtering to remove corrupted entries:
- Entries with <2 characters are skipped
- Entries with >20% special characters are filtered
- Entries without alphabetic characters are excluded
- This ensures clean, usable material lists in the UI 