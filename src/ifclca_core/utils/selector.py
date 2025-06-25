"""
IFC Element Selector Utilities

Provides flexible filtering of IFC elements based on various criteria including
IFC class types, material assignments, property values, and spatial containment.
"""

import ifcopenshell
import ifcopenshell.util.element
from typing import List, Dict, Any, Union, Optional


def filter_elements(ifc_file: ifcopenshell.file, query: Union[str, Dict[str, Any]]) -> List[ifcopenshell.entity_instance]:
    """
    Filters elements from the IFC file based on the provided query.
    
    Args:
        ifc_file: The IFC file object.
        query: Query can be either:
            - A string in format "IfcClass:MaterialName" (e.g., "IfcWall:Concrete*")
            - A dictionary with filtering criteria:
                {
                    'ifc_class': 'IfcWall',  # IFC entity type
                    'material': 'Concrete',   # Material name (supports wildcards)
                    'property_set': 'Pset_WallCommon',  # Property set name
                    'property': {'IsExternal': True},   # Property name and value
                    'building_storey': 'Ground Floor'    # Spatial containment
                }
    
    Returns:
        List of filtered IFC elements matching the criteria.
    """
    if isinstance(query, str):
        # Parse string query format
        query = _parse_string_query(query)
    
    # Start with all elements of the specified IFC class
    ifc_class = query.get('ifc_class', 'IfcElement')
    elements = list(ifc_file.by_type(ifc_class))
    
    # Filter by material if specified
    if 'material' in query:
        elements = _filter_by_material(ifc_file, elements, query['material'])
    
    # Filter by property set and properties
    if 'property_set' in query or 'property' in query:
        elements = _filter_by_properties(ifc_file, elements, 
                                       query.get('property_set'),
                                       query.get('property', {}))
    
    # Filter by spatial containment
    if 'building_storey' in query:
        elements = _filter_by_storey(ifc_file, elements, query['building_storey'])
    
    # Filter by custom function if provided
    if 'custom_filter' in query and callable(query['custom_filter']):
        elements = [e for e in elements if query['custom_filter'](e)]
    
    return elements


def _parse_string_query(query_str: str) -> Dict[str, Any]:
    """Parse a string query into a dictionary format."""
    parts = query_str.split(':')
    result = {}
    
    if len(parts) >= 1 and parts[0].startswith('Ifc'):
        result['ifc_class'] = parts[0]
    
    if len(parts) >= 2:
        result['material'] = parts[1]
    
    return result


def _filter_by_material(ifc_file: ifcopenshell.file, 
                       elements: List[ifcopenshell.entity_instance], 
                       material_pattern: str) -> List[ifcopenshell.entity_instance]:
    """Filter elements by material name pattern (supports * wildcard)."""
    filtered = []
    
    for element in elements:
        material = ifcopenshell.util.element.get_material(element)
        if not material:
            continue
            
        material_names = _get_material_names(material)
        
        # Check if any material name matches the pattern
        for name in material_names:
            if _matches_pattern(name, material_pattern):
                filtered.append(element)
                break
    
    return filtered


def _get_material_names(material) -> List[str]:
    """Extract all material names from various material assignment types."""
    names = []
    
    if hasattr(material, 'Name'):
        names.append(material.Name or '')
    
    # Handle IfcMaterialLayerSet
    if hasattr(material, 'MaterialLayers'):
        for layer in material.MaterialLayers:
            if hasattr(layer, 'Material') and hasattr(layer.Material, 'Name'):
                names.append(layer.Material.Name or '')
    
    # Handle IfcMaterialLayerSetUsage
    if hasattr(material, 'ForLayerSet'):
        names.extend(_get_material_names(material.ForLayerSet))
    
    # Handle IfcMaterialConstituentSet
    if hasattr(material, 'MaterialConstituents'):
        for constituent in material.MaterialConstituents:
            if hasattr(constituent, 'Material') and hasattr(constituent.Material, 'Name'):
                names.append(constituent.Material.Name or '')
    
    # Handle IfcMaterialList
    if hasattr(material, 'Materials'):
        for mat in material.Materials:
            if hasattr(mat, 'Name'):
                names.append(mat.Name or '')
    
    return names


def _matches_pattern(text: str, pattern: str) -> bool:
    """Check if text matches pattern (supports * wildcard)."""
    if '*' not in pattern:
        return text == pattern
    
    # Simple wildcard matching
    pattern_parts = pattern.split('*')
    if pattern.startswith('*'):
        return text.endswith(pattern_parts[-1])
    elif pattern.endswith('*'):
        return text.startswith(pattern_parts[0])
    else:
        # Handle patterns like "Concrete*C30"
        return text.startswith(pattern_parts[0]) and text.endswith(pattern_parts[-1])


def _filter_by_properties(ifc_file: ifcopenshell.file,
                         elements: List[ifcopenshell.entity_instance],
                         property_set_name: Optional[str],
                         properties: Dict[str, Any]) -> List[ifcopenshell.entity_instance]:
    """Filter elements by property set and property values."""
    filtered = []
    
    for element in elements:
        # Get all property sets for the element
        psets = ifcopenshell.util.element.get_psets(element)
        
        # If specific property set is requested
        if property_set_name:
            if property_set_name not in psets:
                continue
            pset = psets[property_set_name]
        else:
            # Merge all property sets
            pset = {}
            for ps in psets.values():
                pset.update(ps)
        
        # Check if all required properties match
        match = True
        for prop_name, prop_value in properties.items():
            if prop_name not in pset or pset[prop_name] != prop_value:
                match = False
                break
        
        if match:
            filtered.append(element)
    
    return filtered


def _filter_by_storey(ifc_file: ifcopenshell.file,
                     elements: List[ifcopenshell.entity_instance],
                     storey_name: str) -> List[ifcopenshell.entity_instance]:
    """Filter elements by building storey containment."""
    filtered = []
    
    # Find the building storey
    storeys = [s for s in ifc_file.by_type('IfcBuildingStorey') 
               if s.Name == storey_name]
    
    if not storeys:
        return []
    
    target_storey = storeys[0]
    
    # Get all elements contained in this storey
    for rel in ifc_file.by_type('IfcRelContainedInSpatialStructure'):
        if rel.RelatingStructure == target_storey:
            for element in rel.RelatedElements:
                if element in elements:
                    filtered.append(element)
    
    return filtered


def get_element_materials(element: ifcopenshell.entity_instance) -> List[Dict[str, Any]]:
    """
    Get detailed material information for an element.
    
    Returns:
        List of dictionaries containing material info with keys:
        - name: Material name
        - layer_thickness: Thickness if from layer (in project units)
        - fraction: Fraction if from constituent (0-1)
        - material_entity: The IfcMaterial entity
    """
    materials = []
    material = ifcopenshell.util.element.get_material(element)
    
    if not material:
        return materials
    
    # Handle different material assignment types
    if material.is_a('IfcMaterial'):
        materials.append({
            'name': material.Name or 'Unnamed',
            'layer_thickness': None,
            'fraction': 1.0,
            'material_entity': material
        })
    
    elif material.is_a('IfcMaterialLayerSetUsage'):
        layer_set = material.ForLayerSet
        for layer in layer_set.MaterialLayers:
            if layer.Material:
                materials.append({
                    'name': layer.Material.Name or 'Unnamed',
                    'layer_thickness': layer.LayerThickness,
                    'fraction': None,
                    'material_entity': layer.Material
                })
    
    elif material.is_a('IfcMaterialLayerSet'):
        for layer in material.MaterialLayers:
            if layer.Material:
                materials.append({
                    'name': layer.Material.Name or 'Unnamed',
                    'layer_thickness': layer.LayerThickness,
                    'fraction': None,
                    'material_entity': layer.Material
                })
    
    elif material.is_a('IfcMaterialConstituentSet'):
        total_fraction = sum(c.Fraction or 0 for c in material.MaterialConstituents)
        for constituent in material.MaterialConstituents:
            if constituent.Material:
                fraction = constituent.Fraction if constituent.Fraction else (1.0 / len(material.MaterialConstituents))
                if total_fraction > 0:
                    fraction = fraction / total_fraction  # Normalize
                materials.append({
                    'name': constituent.Material.Name or 'Unnamed',
                    'layer_thickness': None,
                    'fraction': fraction,
                    'material_entity': constituent.Material
                })
    
    elif material.is_a('IfcMaterialList'):
        # Equal distribution if no other info
        fraction = 1.0 / len(material.Materials) if material.Materials else 0
        for mat in material.Materials:
            materials.append({
                'name': mat.Name or 'Unnamed',
                'layer_thickness': None,
                'fraction': fraction,
                'material_entity': mat
            })
    
    return materials