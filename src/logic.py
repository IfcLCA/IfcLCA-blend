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

# Import from the bundled ifclca_core module
try:
    from .ifclca_core import IfcLCAAnalysis, IfcLCADBReader
except ImportError:
    # For standalone usage
    from ifclca_core import IfcLCAAnalysis, IfcLCADBReader

# For backward compatibility with IfcLCA-blend's interface
CarbonDatabaseReader = IfcLCADBReader


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
            # Get all material names for this element
            material_names = self._get_all_material_names(element)
            
            # Count each unique material once per element
            unique_materials = set(material_names)
            for material_name in unique_materials:
                if material_name:
                    materials_usage[material_name] = materials_usage.get(material_name, 0) + 1
        
        # Sort by usage count (descending)
        sorted_materials = sorted(materials_usage.items(), key=lambda x: x[1], reverse=True)
        return sorted_materials
    
    def _get_all_material_names(self, element) -> List[str]:
        """Extract all material names from an element, handling all IFC material types"""
        names = []
        
        # Method 1: Try ifcopenshell utility first (if available)
        if HAS_ELEMENT_UTIL:
            material = ifcopenshell.util.element.get_material(element)
            if material:
                names.extend(self._extract_material_names_from_object(material))
        
        # Method 2: Check HasAssociations for material relationships
        if hasattr(element, 'HasAssociations') and not names:
            for association in element.HasAssociations:
                if association.is_a('IfcRelAssociatesMaterial'):
                    relating_material = association.RelatingMaterial
                    if relating_material:
                        names.extend(self._extract_material_names_from_object(relating_material))
        
        return names
    
    def _extract_material_names_from_object(self, material) -> List[str]:
        """Extract material names from various IFC material objects"""
        names = []
        
        if not material:
            return names
        
        # Handle IfcMaterial (simple case)
        if material.is_a('IfcMaterial'):
            if hasattr(material, 'Name') and material.Name:
                names.append(material.Name)
        
        # Handle IfcMaterialLayerSet
        elif material.is_a('IfcMaterialLayerSet'):
            if hasattr(material, 'MaterialLayers'):
                for layer in material.MaterialLayers:
                    if hasattr(layer, 'Material') and layer.Material:
                        if hasattr(layer.Material, 'Name') and layer.Material.Name:
                            names.append(layer.Material.Name)
        
        # Handle IfcMaterialLayerSetUsage (references a layer set)
        elif material.is_a('IfcMaterialLayerSetUsage'):
            if hasattr(material, 'ForLayerSet') and material.ForLayerSet:
                # Recursively extract from the referenced layer set
                names.extend(self._extract_material_names_from_object(material.ForLayerSet))
        
        # Handle IfcMaterialList
        elif material.is_a('IfcMaterialList'):
            if hasattr(material, 'Materials'):
                for mat in material.Materials:
                    if hasattr(mat, 'Name') and mat.Name:
                        names.append(mat.Name)
        
        # Handle IfcMaterialConstituentSet
        elif material.is_a('IfcMaterialConstituentSet'):
            if hasattr(material, 'MaterialConstituents'):
                for constituent in material.MaterialConstituents:
                    if hasattr(constituent, 'Material') and constituent.Material:
                        if hasattr(constituent.Material, 'Name') and constituent.Material.Name:
                            names.append(constituent.Material.Name)
        
        # Handle IfcMaterialProfileSet
        elif material.is_a('IfcMaterialProfileSet'):
            if hasattr(material, 'MaterialProfiles'):
                for profile in material.MaterialProfiles:
                    if hasattr(profile, 'Material') and profile.Material:
                        if hasattr(profile.Material, 'Name') and profile.Material.Name:
                            names.append(profile.Material.Name)
        
        # Handle IfcMaterialProfileSetUsage
        elif material.is_a('IfcMaterialProfileSetUsage'):
            if hasattr(material, 'ForProfileSet') and material.ForProfileSet:
                # Recursively extract from the referenced profile set
                names.extend(self._extract_material_names_from_object(material.ForProfileSet))
        
        return names
    
    def _get_material_names(self, material) -> List[str]:
        """Legacy method - redirects to new comprehensive method"""
        return self._extract_material_names_from_object(material)
    
    def _get_material_name(self, material) -> Optional[str]:
        """Extract single material name (for backward compatibility)"""
        names = self._extract_material_names_from_object(material)
        return names[0] if names else None
    
    def get_element_name(self, element) -> str:
        """Extract element name from IFC element"""
        # Try different ways to get the element name
        
        # Method 1: Direct Name attribute
        if hasattr(element, 'Name') and element.Name:
            return element.Name
        
        # Method 2: Try using ifcopenshell utility if available
        if HAS_ELEMENT_UTIL:
            try:
                # Some versions have get_name
                if hasattr(ifcopenshell.util.element, 'get_name'):
                    name = ifcopenshell.util.element.get_name(element)
                    if name:
                        return name
            except:
                pass
        
        # Method 3: Check common property sets
        try:
            psets = ifcopenshell.util.element.get_psets(element)
            # Common property sets that might contain names
            for pset_name in ['Pset_General', 'Identity Data', 'Other']:
                if pset_name in psets:
                    pset = psets[pset_name]
                    for key in ['Name', 'Reference', 'Mark', 'Tag']:
                        if key in pset:
                            name = pset[key]
                            if name and isinstance(name, str):
                                return name
        except:
            pass
        
        # Method 4: Try GlobalId as last resort
        if hasattr(element, 'GlobalId') and element.GlobalId:
            return f"Element_{element.GlobalId[:8]}"
        
        # Final fallback: Use type and ID
        return f"{element.is_a()} #{element.id()}"
    
    def get_elements_by_material(self, material_name: str) -> List[Any]:
        """Get all elements using a specific material"""
        elements = []
        all_elements = self.ifc.by_type("IfcElement")
        
        for element in all_elements:
            material_names = self._get_all_material_names(element)
            if material_name in material_names:
                elements.append(element)
        
        return elements
    
    def get_elements_with_info_by_material(self, material_name: str) -> List[Dict[str, Any]]:
        """Get all elements using a specific material with detailed info"""
        elements_info = []
        all_elements = self.ifc.by_type("IfcElement")
        
        for element in all_elements:
            material_names = self._get_all_material_names(element)
            if material_name in material_names:
                element_info = {
                    'element': element,
                    'id': element.id(),
                    'name': self.get_element_name(element),
                    'type': element.is_a(),
                    'materials': material_names
                }
                elements_info.append(element_info)
        
        return elements_info


def run_lca_analysis(ifc_file, 
                    db_reader: IfcLCADBReader, 
                    mapping: Dict[str, str]) -> Tuple[Dict[str, float], Dict[str, Dict[str, Any]]]:
    """
    Run LCA analysis using IfcLCA-Py
    
    Returns:
        Tuple of (results by database ID, detailed results by material name)
    """
    # Use the full IfcLCA-Py implementation
    analysis = IfcLCAAnalysis(ifc_file, db_reader, mapping)
    results = analysis.run()
    detailed_results = analysis.get_detailed_results()
    
    return results, detailed_results


def format_results(results: Dict[str, float], 
                  detailed_results: Dict[str, Dict[str, Any]], 
                  db_reader: IfcLCADBReader) -> str:
    """Format results for display"""
    lines = []
    total_carbon = 0
    materials_with_impact = 0
    materials_without_volume = 0
    
    lines.append("=== Embodied Carbon Results ===\n")
    
    # Sort by carbon impact (descending) - handle both 'total_carbon' and 'gwp' keys
    sorted_materials = sorted(
        detailed_results.items(), 
        key=lambda x: x[1].get('gwp', x[1].get('total_carbon', 0)), 
        reverse=True
    )
    
    # First show materials with carbon impact
    for material_name, details in sorted_materials:
        # Handle both 'gwp' (from IfcLCA-Py) and 'total_carbon' keys
        carbon = details.get('gwp', details.get('total_carbon', 0))
        if carbon > 0:
            materials_with_impact += 1
            total_carbon += carbon
            
            # Get material info from database
            material_data = db_reader.get_material_data(details['database_id'])
            db_name = material_data.get('name', material_name)
            
            # Format carbon value
            if carbon >= 1000:
                carbon_str = f"{carbon/1000:.2f} t CO₂-eq"
            else:
                carbon_str = f"{carbon:.1f} kg CO₂-eq"
            
            lines.append(f"{db_name}:")
            lines.append(f"  IFC Material: {material_name}")
            # Handle both 'elements' and 'element_count' keys
            element_count = details.get('elements', details.get('element_count', 0))
            lines.append(f"  Elements: {element_count}")
            lines.append(f"  Volume: {details['total_volume']:.2f} m³")
            lines.append(f"  Mass: {details['total_mass']:.0f} kg")
            lines.append(f"  Carbon: {carbon_str}")
            
            # Add other environmental indicators if available
            if 'penr' in details and details['penr'] > 0:
                lines.append(f"  Primary Energy (non-renewable): {details['penr']:.0f} MJ")
            if 'ubp' in details and details['ubp'] > 0:
                lines.append(f"  Environmental Impact Points: {details['ubp']:.0f} UBP")
            
            lines.append("")
    
    # Show summary of materials without volume
    materials_no_volume = []
    for material_name, details in sorted_materials:
        carbon = details.get('gwp', details.get('total_carbon', 0))
        element_count = details.get('elements', details.get('element_count', 0))
        if carbon == 0 and element_count > 0:
            materials_no_volume.append(material_name)
            materials_without_volume += 1
    
    if materials_no_volume:
        lines.append("\n--- Materials without volume data ---")
        for mat in materials_no_volume[:5]:  # Show first 5
            details = detailed_results[mat]
            element_count = details.get('elements', details.get('element_count', 0))
            lines.append(f"• {mat}: {element_count} elements")
        if len(materials_no_volume) > 5:
            lines.append(f"  ... and {len(materials_no_volume) - 5} more")
        lines.append("")
    
    # Add summary
    lines.append("-" * 30)
    lines.append("SUMMARY:")
    lines.append(f"  Materials analyzed: {len(detailed_results)}")
    lines.append(f"  Materials with impact: {materials_with_impact}")
    lines.append(f"  Materials without volume: {materials_without_volume}")
    lines.append("")
    
    # Add total
    if total_carbon >= 1000:
        total_str = f"{total_carbon/1000:.2f} t CO₂-eq"
    else:
        total_str = f"{total_carbon:.1f} kg CO₂-eq"
    lines.append(f"TOTAL EMBODIED CARBON: {total_str}")
    
    # Add note if no impact calculated
    if total_carbon == 0:
        lines.append("\n⚠️  No carbon impact calculated. Possible reasons:")
        lines.append("  • Elements don't have volume/quantity data")
        lines.append("  • Materials not mapped to database entries")
        lines.append("  • Database entries missing carbon data")
        lines.append("\nTip: Check console output for detailed debugging info")
    
    return "\n".join(lines) 