"""
IFC Life Cycle Assessment Analysis

Core module for performing LCA calculations on IFC building models.
Supports multiple environmental indicators and handles various IFC
quantity representations.
"""

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.unit
from typing import Dict, List, Any, Optional, Tuple
from .utils import selector
from .db_reader import IfcLCADBReader


class IfcLCAAnalysis:
    """
    Main class for performing Life Cycle Assessment on IFC models.
    
    Attributes:
        ifc_file: The IFC file to analyze
        db_reader: Database reader for environmental data
        mapping: Dictionary mapping material queries to database IDs
        results: Analysis results by environmental indicator
    """
    
    def __init__(self, ifc_file: ifcopenshell.file, 
                 db_reader: IfcLCADBReader, 
                 mapping: Dict[str, str]):
        """
        Initialize LCA analysis.
        
        Args:
            ifc_file: IFC file object
            db_reader: Environmental database reader
            mapping: Material mapping {query: database_id}
                     Query can be:
                     - Material name (e.g., "Concrete C30/37")
                     - IFC query string (e.g., "IfcWall:Concrete*")
                     - Complex query dict
        """
        self.ifc_file = ifc_file
        self.db_reader = db_reader
        self.mapping = mapping
        self.results = {}
        self.detailed_results = {}
        self._unit_scale = self._get_unit_scale()
    
    def run(self) -> Dict[str, float]:
        """
        Run the LCA analysis.
        
        Returns:
            Dictionary with total impacts by database material ID:
            {material_id: total_gwp_in_kg_co2}
        """
        # Initialize result structures
        self.results = {
            'gwp': {},    # Global Warming Potential
            'penr': {},   # Primary Energy non-renewable
            'ubp': {},    # Environmental Impact Points
            'total': {}   # Legacy total (GWP)
        }
        self.detailed_results = {}
        
        # Process each material mapping
        for mapping_query, database_id in self.mapping.items():
            if not database_id:  # Skip unmapped
                continue
                
            # Get material data from database
            material_data = self.db_reader.get_material_data(database_id)
            if not material_data:
                print(f"Warning: No data found for material ID: {database_id}")
                continue
            
            # Find elements matching the query
            elements = self._get_elements_for_query(mapping_query)
            if not elements:
                print(f"Warning: No elements found for query: {mapping_query}")
                continue
            
            # Calculate impacts for these elements
            impacts = self._calculate_impacts_for_elements(
                elements, material_data, mapping_query
            )
            
            # Store results
            self._store_results(database_id, impacts, material_data)
        
        # Return legacy format (total GWP by material)
        return self.results['total']
    
    def get_results_by_indicator(self) -> Dict[str, Dict[str, float]]:
        """
        Get results organized by environmental indicator.
        
        Returns:
            {
                'gwp': {material_id: value},
                'penr': {material_id: value},
                'ubp': {material_id: value}
            }
        """
        return {
            'gwp': self.results['gwp'],
            'penr': self.results['penr'],
            'ubp': self.results['ubp']
        }
    
    def get_detailed_results(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed results including quantities and element counts.
        
        Returns:
            {
                query: {
                    'database_id': str,
                    'material_name': str,
                    'elements': int,
                    'total_volume': float,
                    'total_mass': float,
                    'gwp': float,
                    'penr': float,
                    'ubp': float
                }
            }
        """
        return self.detailed_results
    
    def _get_unit_scale(self) -> float:
        """Get scale factor to convert project units to meters."""
        units = self.ifc_file.by_type("IfcUnitAssignment")
        if not units:
            return 1.0
            
        unit_assignment = units[0]
        for unit in unit_assignment.Units:
            if hasattr(unit, 'UnitType') and unit.UnitType == 'LENGTHUNIT':
                if hasattr(unit, 'Prefix'):
                    # Handle SI units with prefix
                    prefix_scales = {
                        'MILLI': 0.001,
                        'CENTI': 0.01,
                        'DECI': 0.1,
                        None: 1.0
                    }
                    return prefix_scales.get(unit.Prefix, 1.0)
        return 1.0
    
    def _get_elements_for_query(self, query: str) -> List[ifcopenshell.entity_instance]:
        """Get elements matching a query string."""
        # If query looks like a material name, search for it
        if not query.startswith('Ifc') and ':' not in query:
            # Direct material name - find all elements with this material
            return self._get_elements_by_material_name(query)
        else:
            # Use selector for complex queries
            return selector.filter_elements(self.ifc_file, query)
    
    def _get_elements_by_material_name(self, material_name: str) -> List[ifcopenshell.entity_instance]:
        """Get all elements that use a specific material name."""
        elements = []
        
        for element in self.ifc_file.by_type('IfcElement'):
            materials = selector.get_element_materials(element)
            for mat_info in materials:
                if mat_info['name'] == material_name:
                    elements.append(element)
                    break
        
        return elements
    
    def _calculate_impacts_for_elements(self, 
                                      elements: List[ifcopenshell.entity_instance],
                                      material_data: Dict[str, Any],
                                      query: str) -> Dict[str, float]:
        """Calculate environmental impacts for a set of elements."""
        total_volume = 0.0
        total_mass = 0.0
        element_details = []
        
        density = material_data.get('density', 0)
        
        for element in elements:
            # Get element quantity (volume)
            volume = self._get_element_volume(element)
            
            if volume > 0:
                # Check if this element has layered materials
                material_fraction = self._get_material_fraction(element, query)
                effective_volume = volume * material_fraction
                
                mass = effective_volume * density
                total_volume += effective_volume
                total_mass += mass
                
                element_details.append({
                    'element': element,
                    'volume': effective_volume,
                    'mass': mass,
                    'fraction': material_fraction
                })
        
        # Calculate impacts
        gwp = total_mass * material_data.get('gwp', material_data.get('carbon_per_unit', 0))
        penr = total_mass * material_data.get('penr', 0)
        ubp = total_mass * material_data.get('ubp', 0)
        
        return {
            'elements': len(elements),
            'total_volume': total_volume,
            'total_mass': total_mass,
            'gwp': gwp,
            'penr': penr,
            'ubp': ubp,
            'element_details': element_details
        }
    
    def _get_element_volume(self, element: ifcopenshell.entity_instance) -> float:
        """Extract volume from element quantities."""
        # Try base quantities first
        quantity_sets = [
            "BaseQuantities",
            f"Qto_{element.is_a()}BaseQuantities",
            f"Qto_{element.is_a()[3:]}BaseQuantities"  # Remove 'Ifc' prefix
        ]
        
        for qset_name in quantity_sets:
            quantities = ifcopenshell.util.element.get_psets(element, qtos_only=True)
            
            for qset_key, qset_values in quantities.items():
                if qset_name in qset_key or qset_key == qset_name:
                    # Look for volume properties
                    for prop_name in ['GrossVolume', 'NetVolume', 'Volume']:
                        if prop_name in qset_values:
                            value = qset_values[prop_name]
                            if isinstance(value, (int, float)):
                                # BaseQuantities volumes are already in m³
                                # No need to apply unit scaling
                                return float(value)
        
        # Fallback: try to compute from geometry (not implemented in base)
        return 0.0
    
    def _get_material_fraction(self, element: ifcopenshell.entity_instance, query: str) -> float:
        """
        Get the fraction of element volume occupied by the queried material.
        Important for layered constructions.
        """
        materials = selector.get_element_materials(element)
        if not materials:
            return 1.0
        
        # If query is a material name, find its fraction
        if not query.startswith('Ifc') and ':' not in query:
            total_thickness = 0.0
            material_thickness = 0.0
            
            for mat_info in materials:
                if mat_info['layer_thickness'] is not None:
                    thickness = mat_info['layer_thickness'] * self._unit_scale
                    total_thickness += thickness
                    if mat_info['name'] == query:
                        material_thickness += thickness
                elif mat_info['fraction'] is not None:
                    if mat_info['name'] == query:
                        return mat_info['fraction']
            
            if total_thickness > 0:
                return material_thickness / total_thickness
        
        # Default to full volume
        return 1.0
    
    def _store_results(self, database_id: str, impacts: Dict[str, Any], material_data: Dict[str, Any]):
        """Store analysis results."""
        # Store by indicator
        self.results['gwp'][database_id] = impacts['gwp']
        self.results['penr'][database_id] = impacts['penr']
        self.results['ubp'][database_id] = impacts['ubp']
        self.results['total'][database_id] = impacts['gwp']  # Legacy
        
        # Store detailed results
        query = self._find_query_for_database_id(database_id)
        if query:
            self.detailed_results[query] = {
                'database_id': database_id,
                'material_name': material_data.get('name', database_id),
                'elements': impacts['elements'],
                'total_volume': impacts['total_volume'],
                'total_mass': impacts['total_mass'],
                'gwp': impacts['gwp'],
                'penr': impacts['penr'],
                'ubp': impacts['ubp']
            }
    
    def _find_query_for_database_id(self, database_id: str) -> Optional[str]:
        """Find the original query for a database ID."""
        for query, db_id in self.mapping.items():
            if db_id == database_id:
                return query
        return None
    
    def generate_summary(self) -> str:
        """Generate a text summary of the analysis results."""
        lines = ["=== IFC LCA Analysis Results ===\n"]
        
        # Summary by material
        lines.append("Material Breakdown:")
        for query, details in self.detailed_results.items():
            lines.append(f"\n{details['material_name']} ({query}):")
            lines.append(f"  Elements: {details['elements']}")
            lines.append(f"  Volume: {details['total_volume']:.2f} m³")
            lines.append(f"  Mass: {details['total_mass']:.0f} kg")
            lines.append(f"  GWP: {details['gwp']:.1f} kg CO₂-eq")
            if details['penr'] > 0:
                lines.append(f"  PEnr: {details['penr']:.0f} MJ")
            if details['ubp'] > 0:
                lines.append(f"  UBP: {details['ubp']:.0f} points")
        
        # Totals
        total_gwp = sum(self.results['gwp'].values())
        total_penr = sum(self.results['penr'].values())
        total_ubp = sum(self.results['ubp'].values())
        
        lines.append("\n" + "="*30)
        lines.append("TOTALS:")
        lines.append(f"  GWP: {total_gwp:.1f} kg CO₂-eq")
        if total_penr > 0:
            lines.append(f"  PEnr: {total_penr:.0f} MJ")
        if total_ubp > 0:
            lines.append(f"  UBP: {total_ubp:.0f} points")
        
        return "\n".join(lines)