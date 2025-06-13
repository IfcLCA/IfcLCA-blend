from typing import Dict, List, Tuple, Optional, Any

try:
    import ifcopenshell
    # These utils might not be available in all versions
    try:
        import ifcopenshell.util.element
        HAS_ELEMENT_UTIL = True
    except ImportError:
        HAS_ELEMENT_UTIL = False
        # Create a mock for testing
        if not hasattr(ifcopenshell, 'util'):
            ifcopenshell.util = type('util', (), {})()
        ifcopenshell.util.element = type('element', (), {
            'get_material': lambda elem: None,
            'get_pset': lambda elem, name: {},
            'get_psets': lambda elem: {}
        })()
except ImportError as e:
    print(f"DEBUG: ImportError in logic.py: {e}")
    ifcopenshell = None
    HAS_ELEMENT_UTIL = False

# Try to import from the IfcLCA-Py package if available
try:
    from IfcLCA.analysis import IfcLCAAnalysis
    HAS_IFCLCA_PY = True
except ImportError:
    HAS_IFCLCA_PY = False

# Import our database reader
try:
    from .database_reader import CarbonDatabaseReader
except ImportError:
    # For testing, use absolute import
    from database_reader import CarbonDatabaseReader


class IfcMaterialExtractor:
    """Extract materials from IFC file"""
    
    def __init__(self, ifc_file):
        self.ifc = ifc_file
        
    def get_all_materials(self) -> List[Tuple[str, int]]:
        """Get all materials used in the model with element count"""
        materials_usage = {}
        
        # Get all elements that might have materials
        elements = self.ifc.by_type("IfcElement")
        
        for element in elements:
            # Try to get material for this element
            material = ifcopenshell.util.element.get_material(element)
            
            if material:
                material_names = self._get_material_names(material)
                # Get unique materials for this element
                unique_materials = set(material_names)
                # Count each material once per element
                for material_name in unique_materials:
                    if material_name:
                        materials_usage[material_name] = materials_usage.get(material_name, 0) + 1
        
        # Sort by usage count (descending)
        sorted_materials = sorted(materials_usage.items(), key=lambda x: x[1], reverse=True)
        return sorted_materials
    
    def _get_material_names(self, material) -> List[str]:
        """Extract material names from various material types"""
        names = []
        
        # Direct material name
        if hasattr(material, 'Name'):
            names.append(material.Name)
        # Check for MaterialLayers (IfcMaterialLayerSet)
        if hasattr(material, 'MaterialLayers'):
            # IfcMaterialLayerSet - get all layer materials
            layers = getattr(material, 'MaterialLayers', [])
            if isinstance(layers, list):
                for layer in layers:
                    if hasattr(layer, 'Material') and hasattr(layer.Material, 'Name'):
                        names.append(layer.Material.Name)
        # Check for Materials list
        if hasattr(material, 'Materials'):
            # IfcMaterialList or similar - get all materials
            materials = getattr(material, 'Materials', [])
            if isinstance(materials, list):
                for mat in materials:
                    if hasattr(mat, 'Name'):
                        names.append(mat.Name)
        # Check for single Material property
        if not names and hasattr(material, 'Material') and hasattr(material.Material, 'Name'):
            names.append(material.Material.Name)
            
        return names
    
    def _get_material_name(self, material) -> Optional[str]:
        """Extract single material name (for backward compatibility)"""
        names = self._get_material_names(material)
        return names[0] if names else None
    
    def get_elements_by_material(self, material_name: str) -> List[Any]:
        """Get all elements using a specific material"""
        elements = []
        all_elements = self.ifc.by_type("IfcElement")
        
        for element in all_elements:
            material = ifcopenshell.util.element.get_material(element)
            if material and self._get_material_name(material) == material_name:
                elements.append(element)
        
        return elements


class SimplifiedIfcLCAAnalysis:
    """Simplified LCA analysis for when IfcLCA-Py is not available"""
    
    def __init__(self, ifc_file, db_reader: CarbonDatabaseReader, mapping: Dict[str, str]):
        self.ifc_file = ifc_file
        self.db_reader = db_reader
        self.mapping = mapping
        self.material_extractor = IfcMaterialExtractor(ifc_file)
        
    def run(self) -> Dict[str, float]:
        """Run the LCA analysis"""
        results = {}
        detailed_results = {}
        
        for material_name, database_id in self.mapping.items():
            if not database_id:  # Skip unmapped materials
                continue
                
            # Get all elements with this material
            elements = self.material_extractor.get_elements_by_material(material_name)
            
            # Get material data from database
            material_data = self.db_reader.get_material_data(database_id)
            if not material_data:
                print(f"Warning: No data found for {database_id}")
                continue
            
            density = material_data.get('density', 0)
            carbon_per_unit = material_data.get('carbon_per_unit', 0)
            
            total_volume = 0
            total_carbon = 0
            
            for element in elements:
                # Try to get volume from BaseQuantities
                volume = self._get_element_volume(element)
                if volume > 0:
                    total_volume += volume
                    mass = volume * density  # kg
                    carbon = mass * carbon_per_unit  # kgCO2e
                    total_carbon += carbon
            
            results[database_id] = total_carbon
            detailed_results[material_name] = {
                'database_id': database_id,
                'element_count': len(elements),
                'total_volume': total_volume,
                'total_mass': total_volume * density,
                'total_carbon': total_carbon,
                'density': density,
                'carbon_per_unit': carbon_per_unit
            }
        
        # Store detailed results for reporting
        self.detailed_results = detailed_results
        
        return results
    
    def _get_element_volume(self, element) -> float:
        """Get element volume from BaseQuantities or compute it"""
        # Try different quantity sets
        quantity_names = [
            "Qto_WallBaseQuantities.GrossVolume",
            "Qto_SlabBaseQuantities.GrossVolume", 
            "Qto_BeamBaseQuantities.GrossVolume",
            "Qto_ColumnBaseQuantities.GrossVolume",
            "BaseQuantities.GrossVolume",
            "BaseQuantities.NetVolume"
        ]
        
        for qname in quantity_names:
            try:
                pset = ifcopenshell.util.element.get_pset(element, qname)
                if pset and isinstance(pset, dict):
                    # Look for volume properties
                    for key in ['GrossVolume', 'NetVolume', 'Volume']:
                        if key in pset:
                            value = pset[key]
                            if isinstance(value, dict) and 'value' in value:
                                return float(value['value'])
                            elif isinstance(value, (int, float)):
                                return float(value)
            except:
                continue
        
        # If no quantities found, return 0 (could implement geometry calculation here)
        return 0.0
    
    def get_detailed_results(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed results by material"""
        return getattr(self, 'detailed_results', {})


def run_lca_analysis(ifc_file, 
                    db_reader: CarbonDatabaseReader, 
                    mapping: Dict[str, str]) -> Tuple[Dict[str, float], Dict[str, Dict[str, Any]]]:
    """
    Run LCA analysis using either IfcLCA-Py or simplified implementation
    
    Returns:
        Tuple of (results by database ID, detailed results by material name)
    """
    if HAS_IFCLCA_PY:
        # Use the full IfcLCA-Py implementation
        analysis = IfcLCAAnalysis(ifc_file, db_reader, mapping)
        results = analysis.run()
        # TODO: Get detailed results from IfcLCA-Py if available
        detailed_results = {}
    else:
        # Use simplified implementation
        analysis = SimplifiedIfcLCAAnalysis(ifc_file, db_reader, mapping)
        results = analysis.run()
        detailed_results = analysis.get_detailed_results()
    
    return results, detailed_results


def format_results(results: Dict[str, float], 
                  detailed_results: Dict[str, Dict[str, Any]], 
                  db_reader: CarbonDatabaseReader) -> str:
    """Format results for display"""
    lines = []
    total_carbon = 0
    
    lines.append("=== Embodied Carbon Results ===\n")
    
    # Sort by carbon impact (descending)
    sorted_materials = sorted(
        detailed_results.items(), 
        key=lambda x: x[1]['total_carbon'], 
        reverse=True
    )
    
    for material_name, details in sorted_materials:
        carbon = details['total_carbon']
        if carbon == 0:
            continue
            
        total_carbon += carbon
        
        # Get material info from database
        material_data = db_reader.get_material_data(details['database_id'])
        db_name = material_data.get('name', material_name)
        
        # Format carbon value
        if carbon >= 1000:
            carbon_str = f"{carbon/1000:.2f} t CO₂e"
        else:
            carbon_str = f"{carbon:.1f} kg CO₂e"
        
        lines.append(f"{db_name}:")
        lines.append(f"  Elements: {details['element_count']}")
        lines.append(f"  Volume: {details['total_volume']:.2f} m³")
        lines.append(f"  Mass: {details['total_mass']:.0f} kg")
        lines.append(f"  Carbon: {carbon_str}")
        lines.append("")
    
    # Add total
    lines.append("-" * 30)
    if total_carbon >= 1000:
        total_str = f"{total_carbon/1000:.2f} t CO₂e"
    else:
        total_str = f"{total_carbon:.1f} kg CO₂e"
    lines.append(f"TOTAL: {total_str}")
    
    return "\n".join(lines) 