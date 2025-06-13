# Contributing to Bonsai/IfcOpenShell

This document outlines how the IfcLCA add-on can be integrated into the [ifcopenshell/bonsai](https://github.com/ifcopenshell/bonsai) project.

## Integration Strategy

### 1. Module Structure

The add-on should be integrated as a new Bonsai module under `bonsai/bim/module/lca/`:

```
bonsai/bim/module/lca/
├── __init__.py
├── ui.py          # Panels from our panels.py
├── operator.py    # Operators from our operators.py  
├── prop.py        # Properties from our properties.py
├── tool.py        # Logic from our logic.py
└── data/          # Database files and readers
    ├── database_reader.py
    └── kbob_2022.json
```

### 2. Code Adaptations

#### Use Bonsai's Tool System

Replace direct IfcOpenShell usage with Bonsai tools:

```python
# Instead of:
ifc = ifcopenshell.open(filepath)

# Use:
ifc = tool.Ifc.get()
```

#### Follow Bonsai Naming Conventions

- Operators: `bim.lca_run_analysis` instead of `ifclca.run_analysis`
- Properties: Use Bonsai's property registration system
- UI: Integrate into existing BIM tab or create new LCA tab

#### Use Bonsai's Module Pattern

```python
# In tool.py
import bonsai.core.lca as core
import bonsai.tool as tool
import ifcopenshell.api

class Lca(tool.Ifc):
    @classmethod
    def run_analysis(cls, ifc_file, mapping, db_reader):
        return core.run_analysis(ifc_file, mapping, db_reader)
```

### 3. Dependencies

- Add IfcLCA-Py to Bonsai's requirements or vendor the needed components
- Ensure database files are included in distribution

### 4. Testing

Create tests under `test/bim/module/test_lca.py`:

```python
class TestLCA(NewFile):
    def test_run_analysis(self):
        # Create test IFC with known materials
        # Run analysis
        # Assert expected carbon values
```

### 5. Documentation

Add documentation to `docs/users/analysis_tools/lca.rst`:

- Overview of LCA functionality
- Step-by-step usage guide
- Database configuration
- Troubleshooting

## Pull Request Checklist

- [ ] Code follows Bonsai's style guide
- [ ] All operators use Bonsai's tool system
- [ ] UI integrates cleanly with existing panels
- [ ] Tests pass (`python -m pytest test/bim/module/test_lca.py`)
- [ ] Documentation added/updated
- [ ] License headers added (GPL v3)
- [ ] No external dependencies without discussion

## Licensing

This add-on is AGPL v3, which is compatible with Bonsai's GPL v3. We can relicense our contributions as GPL v3 for inclusion in Bonsai.

## Questions for Maintainers

1. **Module vs Standalone**: Should LCA be a core module or optional extension?
2. **Database Distribution**: How should we handle the KBOB/ÖKOBAUDAT data files?
3. **UI Location**: New tab or integrate into existing panels?
4. **Quantity Calculation**: Should we use Ifc5D integration for missing quantities?

## Contact

For questions about this integration:
- Open an issue in the IfcLCA repository
- Join the OSArch community discussion 