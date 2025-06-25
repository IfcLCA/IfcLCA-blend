# Material Search in IfcLCA

The IfcLCA addon features an advanced material search system for mapping IFC materials to environmental database entries.

## Features

### 🔍 Fuzzy Search
- **Partial matching**: Type any part of a material name
- **Smart ranking**: Results are sorted by relevance
- **Category search**: Search by material category as well as name
- **Typo-tolerant**: Finds matches even with minor typos

### 📊 Rich Information Display
- **Environmental data**: See GWP and density directly in search results
- **Categorized results**: Materials grouped by type
- **Clear descriptions**: Each material shows its key properties

### ⚡ Fast & Accessible
- **Instant search**: Results update as you type
- **Keyboard friendly**: Navigate with arrow keys
- **Limited results**: Shows top 50 matches to keep UI responsive

## How to Use

1. **Open Material Mapping**
   - Load your IFC file
   - In the Material Mapping panel, click the search icon (🔍) next to any material

2. **Search for Materials**
   - Type in the search box to filter materials
   - Examples:
     - `beton` - finds all concrete materials
     - `holz` - finds wood materials
     - `dämmung` - finds insulation materials
     - `stahl` - finds steel materials

3. **Select Material**
   - Browse the categorized results
   - Click on a material to map it
   - The mapping is saved immediately

## Search Examples

### Concrete Materials
- Search: `beton` or `concrete`
- Finds: Hochbaubeton, Magerbeton, Betonfertigteil, etc.

### Steel Materials
- Search: `stahl` or `steel`
- Finds: Armierungsstahl, Stahlblech, Chromstahl, etc.

### Insulation
- Search: `dämmung` or `isolation`
- Finds: Glaswolle, Steinwolle, EPS, XPS, etc.

### Wood Materials
- Search: `holz` or `timber`
- Finds: Massivholz, Brettschichtholz, Spanplatte, etc.

## Tips

- **Use German terms** for KBOB database (Swiss/German materials)
- **Start broad**: Type 2-3 letters to see categories
- **Check categories**: Materials are organized by type
- **Look at GWP**: Higher values mean more carbon impact

## Troubleshooting

### No Results Found
- Check spelling or try partial words
- Use German terms for KBOB materials
- Try searching by category (e.g., "Metal", "Wood")

### Wrong Material Selected
- Click the edit icon (✏️) next to a mapped material to change it
- Use the search again to find the correct material

### Database Not Loading
- Ensure the KBOB database file exists in `assets/indicatorsKBOB_v6.json`
- Check the Blender console for error messages
- Reload the addon if necessary 