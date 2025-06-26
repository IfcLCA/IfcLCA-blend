import json
import csv
import os
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

# Try to import requests from our bundled libs
try:
    from .libs import HAS_REQUESTS
    if HAS_REQUESTS:
        from .libs import _temp_libs_dir
        import requests
    else:
        HAS_REQUESTS = False
except ImportError:
    # Fallback to system requests if available
    try:
        import requests
        HAS_REQUESTS = True
    except ImportError:
        HAS_REQUESTS = False

if not HAS_REQUESTS:
    print("Warning: 'requests' module not available. Ökobaudat API functionality will be disabled.")

class CarbonDatabaseReader:
    """Base class for reading LCA databases"""
    
    def __init__(self):
        self.data = {}
        self.materials_list = []
    
    def get_material_data(self, material_id: str) -> Dict[str, Any]:
        """Get material data by ID"""
        return self.data.get(material_id, {})
    
    def get_materials_list(self) -> List[Tuple[str, str, str]]:
        """Get list of all materials as (id, name, category) tuples"""
        return self.materials_list
    
    def search_materials(self, query: str) -> List[Tuple[str, str, str]]:
        """Search materials by name or category"""
        query_lower = query.lower()
        return [
            (id, name, cat) for id, name, cat in self.materials_list
            if query_lower in name.lower() or query_lower in cat.lower()
        ]


class KBOBDatabaseReader(CarbonDatabaseReader):
    """Reader for KBOB database (Swiss)"""
    
    def __init__(self, data_path: str = None):
        super().__init__()
        if data_path and os.path.exists(data_path):
            self.load_from_json(data_path)
        else:
            # Try to find indicatorsKBOB_v6.json in various locations
            possible_paths = [
                # In the assets directory (preferred location)
                os.path.join(os.path.dirname(__file__), '..', 'assets', 'indicatorsKBOB_v6.json'),
                # In the parent directory (IfcLCA-blend root)
                os.path.join(os.path.dirname(__file__), '..', 'indicatorsKBOB_v6.json'),
                # In the same directory as database_reader.py
                os.path.join(os.path.dirname(__file__), 'indicatorsKBOB_v6.json'),
                # Current working directory
                'indicatorsKBOB_v6.json',
                # In case it's run from the project root
                'IfcLCA-blend/indicatorsKBOB_v6.json',
                # In case it's run from the project root with assets
                'IfcLCA-blend/assets/indicatorsKBOB_v6.json'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    self.load_from_json(path)
                    print(f"Loaded KBOB database from: {path}")
                    break
            else:
                print("Warning: indicatorsKBOB_v6.json not found. Using empty database.")
                self.data = {}
                self.materials_list = []
    
    def determine_category(self, name: str, kbob_id: float) -> str:
        """Determine material category based on name or KBOB ID"""
        name_lower = name.lower()
        
        # Category mapping based on KBOB ID ranges and material names
        if kbob_id < 1:
            return "Foundation/Excavation"
        elif 1 <= kbob_id < 2:
            return "Concrete"
        elif 2 <= kbob_id < 3:
            return "Masonry"
        elif 3 <= kbob_id < 4:
            return "Mineral/Stone"
        elif 4 <= kbob_id < 5:
            return "Mortar/Plaster"
        elif 5 <= kbob_id < 6:
            return "Facade/Windows"
        elif 6 <= kbob_id < 7:
            return "Metal"
        elif 7 <= kbob_id < 8:
            return "Wood"
        elif 8 <= kbob_id < 9:
            return "Sealants/Adhesives"
        elif 9 <= kbob_id < 10:
            return "Membranes/Foils"
        elif 10 <= kbob_id < 11:
            return "Insulation"
        elif 11 <= kbob_id < 12:
            return "Flooring"
        elif 12 <= kbob_id < 13:
            return "Doors"
        elif 13 <= kbob_id < 14:
            return "Plastics/Pipes"
        elif 14 <= kbob_id < 15:
            return "Coatings"
        elif 15 <= kbob_id < 21:
            return "Other Materials"
        elif 21 <= kbob_id:
            return "Kitchen/Interior"
        else:
            return "Uncategorized"
    
    def load_from_json(self, filepath: str):
        """Load KBOB data from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        self.data = {}
        
        for item in raw_data:
            try:
                # Extract fields
                kbob_id = item.get('KBOB_ID')
                if kbob_id is None:
                    continue
                
                # Convert KBOB_ID to string if it's not already
                kbob_id_str = str(kbob_id)
                
                name = item.get('Name', f'Material {kbob_id}')
                gwp = item.get('GWP', 0)  # Global Warming Potential
                penre = item.get('PENRE', 0)  # Primary Energy Non-Renewable
                ubp = item.get('UBP', None)  # Environmental Impact Points (optional)
                
                # Handle density/weight
                kg_unit = item.get('kg/unit', '-')
                density = None
                
                if kg_unit != '-' and kg_unit is not None:
                    try:
                        density = float(kg_unit)
                    except (ValueError, TypeError):
                        density = None
                
                # Check for min/max density
                min_density = item.get('min density')
                max_density = item.get('max density')
                
                if density is None and min_density is not None and max_density is not None:
                    # Use average of min and max
                    density = (min_density + max_density) / 2
                
                # Create material ID
                material_id = f"KBOB_{kbob_id_str}"
                
                # Determine category - convert ID to float for comparison
                try:
                    # Try to convert to float for category determination
                    kbob_id_float = float(kbob_id)
                except (ValueError, TypeError):
                    # If it's a string ID like "01.002.01", try to extract main number
                    try:
                        kbob_id_float = float(kbob_id_str.split('.')[0])
                    except:
                        kbob_id_float = 99  # Default to "Other Materials" category
                
                category = self.determine_category(name, kbob_id_float)
                
                # Store data
                self.data[material_id] = {
                    "name": name,
                    "category": category,
                    "density": density,
                    "carbon_per_unit": gwp if gwp else 0,  # GWP is in kg CO₂-eq/kg
                    "unit": "kg CO₂-eq/kg",
                    "kbob_id": kbob_id_str,
                    "penre": penre,
                    "ubp": ubp
                }
                
            except Exception as e:
                print(f"Error parsing KBOB item: {e}")
                continue
        
        # Build materials list
        self.materials_list = [
            (id, mat["name"], mat["category"])
            for id, mat in self.data.items()
        ]
        self.materials_list.sort(key=lambda x: (x[2], x[1]))  # Sort by category, then name
        
        print(f"Loaded {len(self.data)} materials from KBOB database")


class OkobaudatAPIReader(CarbonDatabaseReader):
    """Reader for ÖKOBAUDAT database via API"""
    
    def __init__(self, api_key: str = None):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://oekobaudat.de/OEKOBAU.DAT/resource"
        self.datastock_id = "cd2bda71-760b-4fcc-8a0b-3877c10000a8"  # Current datastock
        self.compliance_a2 = "c0016b33-8cf7-415c-ac6e-deba0d21440d"  # EN 15804+A2 UUID
        
        # Initialize with empty data - will be populated on demand
        self.data = {}
        self.materials_list = []
        self._cached = False
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request to the Ökobaudat API"""
        if not HAS_REQUESTS:
            print("Warning: 'requests' module not available. Ökobaudat API functionality will be disabled.")
            return {}
        
        # Check if online access is allowed (Blender 4.2+ requirement)
        try:
            import bpy
            if hasattr(bpy.app, 'online_access') and not bpy.app.online_access:
                print("Warning: Online access is disabled in Blender preferences. Ökobaudat API will not work.")
                print("Enable 'Allow Online Access' in Preferences > System to use this feature.")
                return {}
        except ImportError:
            # Not running in Blender, allow for testing
            pass
        
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error accessing Ökobaudat API: {e}")
            return {}
    
    def _transform_okobaudat_to_kbob_format(self, epd_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Ökobaudat EPD data to KBOB format for compatibility"""
        # Extract basic info
        material_id = epd_data.get('uuid', '')
        name = epd_data.get('name', 'Unknown Material')
        
        # Get the reference flow (first exchange with referenceFlow = true)
        exchanges = epd_data.get('exchanges', {})
        reference_exchange = None
        if isinstance(exchanges, dict) and 'exchange' in exchanges:
            exchange_list = exchanges['exchange']
            if isinstance(exchange_list, list):
                for exchange in exchange_list:
                    if exchange.get('referenceFlow'):
                        reference_exchange = exchange
                        break
        
        # Extract declared unit and reference amount from reference flow
        declared_unit = 'kg'  # default
        ref_flow_amount = 1.0
        grammage = None  # kg/m² for area-based materials
        conversion_factor_to_kg = None  # Some materials have this instead of ref_amount
        
        if reference_exchange:
            # Get flow properties
            flow_props = reference_exchange.get('flowProperties', [])
            if flow_props and isinstance(flow_props, list):
                # Find the reference flow property (not just the first one!)
                ref_prop = None
                mass_value = None  # Store mass value separately
                
                for prop in flow_props:
                    if prop.get('referenceFlowProperty'):
                        ref_prop = prop
                    # Also check for mass property
                    prop_names = prop.get('name', [])
                    if isinstance(prop_names, list):
                        for name_obj in prop_names:
                            if isinstance(name_obj, dict) and name_obj.get('value', '').lower() in ['mass', 'masse']:
                                mass_value = prop.get('meanValue', 0)
                
                if ref_prop:
                    declared_unit = ref_prop.get('referenceUnit', 'kg')
                    ref_flow_amount = ref_prop.get('meanValue', 1.0)
                else:
                    # Fallback to first property
                    ref_prop = flow_props[0] if flow_props else {}
                    declared_unit = ref_prop.get('referenceUnit', 'kg')
                    ref_flow_amount = ref_prop.get('meanValue', 1.0)
            
            # Extract material properties
            material_props = reference_exchange.get('materialProperties', [])
            density = None
            
            for prop in material_props:
                prop_name = prop.get('name', '').lower()
                prop_value = prop.get('value', '')
                
                # Extract density
                if 'density' in prop_name or 'rohdichte' in prop_name:
                    try:
                        density = float(prop_value)
                    except (ValueError, TypeError):
                        pass
                
                # Extract grammage (weight per area)
                elif 'grammage' in prop_name or 'flächengewicht' in prop_name:
                    try:
                        grammage = float(prop_value)
                    except (ValueError, TypeError):
                        pass
                
                # Extract conversion factor to 1 kg (important!)
                elif 'conversion factor to 1 kg' in prop_name:
                    try:
                        conversion_factor_to_kg = float(prop_value)
                    except (ValueError, TypeError):
                        pass
            
            # If we found mass value in flow properties and unit is volume-based, use it as density
            if mass_value and mass_value > 0 and declared_unit.lower() in ['m3', 'm³', 'cubic meter', 'cubic metre']:
                if not density or density == 0:
                    density = mass_value
                    logger.info(f"Using mass value {mass_value} as density for {name}")
        else:
            # Fallback: try old structure for density
            density = None
        
        # Extract environmental indicators - look for GWP in LCIA Results
        gwp = 0
        penre = 0
        
        # Check LCIA Results for environmental data
        lcia_results = epd_data.get('LCIAResults', {})
        if isinstance(lcia_results, dict) and 'LCIAResult' in lcia_results:
            results_list = lcia_results['LCIAResult']
            if isinstance(results_list, list):
                for result in results_list:
                    if isinstance(result, dict):
                        method_ref = result.get('referenceToLCIAMethodDataSet', {})
                        if isinstance(method_ref, dict):
                            short_desc = method_ref.get('shortDescription', [])
                            if isinstance(short_desc, list) and short_desc:
                                method_name = short_desc[0].get('value', '').lower()
                                
                                # Look for GWP total (preferred) or GWP fossil
                                if 'gwp-total' in method_name or 'global warming potential total' in method_name:
                                    # Extract A1-A3 value from anies array
                                    other_data = result.get('other', {})
                                    if isinstance(other_data, dict):
                                        anies = other_data.get('anies', [])
                                        if isinstance(anies, list):
                                            for item in anies:
                                                if isinstance(item, dict) and item.get('module') == 'A1-A3':
                                                    try:
                                                        gwp = float(item.get('value', 0))
                                                        break
                                                    except (ValueError, TypeError):
                                                        continue
                                    if gwp > 0:  # Found GWP total, use it
                                        break
        
        # Determine category based on material classification or name
        classification_info = epd_data.get('processInformation', {}).get('dataSetInformation', {}).get('classificationInformation', {})
        category = self._determine_category_from_classification(classification_info, name)
        
        # Convert GWP to per kg if needed (for consistency with KBOB)
        gwp_per_kg = gwp if gwp is not None else 0.0
        original_gwp = gwp_per_kg
        conversion_note = ""
        
        # Handle different declared units
        if declared_unit.lower() in ['qm', 'm2', 'm²', 'square meter', 'square metre']:
            # Area-based unit - use grammage if available
            if grammage and grammage > 0 and gwp_per_kg > 0:
                gwp_per_kg = gwp_per_kg / grammage
                conversion_note = f"Converted from {original_gwp:.3f} kg CO₂-eq/m² using grammage {grammage} kg/m²"
                logger.info(f"{name}: {conversion_note}")
            else:
                logger.warning(f"Cannot convert GWP from m² to kg - grammage missing: {name}")
                conversion_note = "Area-based unit (m²) - conversion requires grammage"
        
        elif declared_unit.lower() in ['m3', 'm³', 'cubic meter', 'cubic metre']:
            # Volume-based unit - use density if available
            if density and density > 0 and gwp_per_kg > 0:
                gwp_per_kg = gwp_per_kg / density
                conversion_note = f"Converted from {original_gwp:.3f} kg CO₂-eq/m³ using density {density} kg/m³"
                logger.info(f"{name}: {conversion_note}")
            else:
                logger.warning(f"Cannot convert GWP from m³ to kg - density missing: {name}")
                conversion_note = "Volume-based unit (m³) - conversion requires density"
        
        elif declared_unit.lower() in ['kg', 'kilogram']:
            # Check if we have a conversion factor that suggests this is not really per kg
            if conversion_factor_to_kg and conversion_factor_to_kg < 0.01:
                # This suggests the unit is not really kg but something else (likely m³)
                # The conversion factor tells us how many kg equals 1 declared unit
                # So if conversion_factor = 0.0004456676, then 1 unit = 0.0004456676 kg
                # Therefore 1 kg = 1/0.0004456676 units = 2243.825 units
                # This means the material is likely declared per m³ with that density
                
                # The GWP is given per declared unit, so we need to multiply by conversion factor
                gwp_per_kg = gwp_per_kg * conversion_factor_to_kg
                conversion_note = f"Converted using conversion factor {conversion_factor_to_kg:.6f} (likely m³ unit mislabeled as kg)"
                logger.info(f"{name}: {conversion_note}")
            else:
                # Already in kg - no conversion needed
                conversion_note = "Already in kg unit"
        
        else:
            # Other units - flag for manual review
            logger.warning(f"Unknown unit '{declared_unit}' for material: {name}")
            conversion_note = f"Unknown unit: {declared_unit}"
        
        # Build KBOB-compatible data structure
        return {
            "name": name,
            "category": category,
            "density": density if density is not None else 0.0,
            "carbon_per_unit": gwp_per_kg,  # Always in kg CO₂-eq/kg for consistency
            "unit": "kg CO₂-eq/kg",  # Standardized unit
            "okobaudat_id": material_id,
            "penre": penre if penre is not None else 0.0,
            "declared_unit": declared_unit,  # Keep original for reference
            "reference_flow_amount": ref_flow_amount if ref_flow_amount is not None else 1.0,
            "original_gwp": original_gwp,  # Keep original value for debugging
            "original_unit": f"kg CO₂-eq/{declared_unit}",  # Keep original unit for debugging
            "conversion_note": conversion_note,  # Explanation of conversion
            "grammage": grammage if grammage is not None else 0.0,  # Store grammage if available
            "conversion_factor_to_kg": conversion_factor_to_kg if conversion_factor_to_kg is not None else 1.0  # Store conversion factor if available
        }
    
    def _determine_category_from_classification(self, classification: Dict[str, Any], name: str) -> str:
        """Determine material category from Ökobaudat classification"""
        # Check classification codes
        classifications = classification.get('classification', [])
        if isinstance(classifications, list):
            for classif in classifications:
                if classif.get('name') == 'OEKOBAU.DAT':
                    classes = classif.get('class', [])
                    if isinstance(classes, list):
                        for cls in classes:
                            class_value = cls.get('value', '').lower()
                            # Map Ökobaudat categories to KBOB categories
                            if 'beton' in class_value or 'concrete' in class_value:
                                return "Concrete"
                            elif 'stahl' in class_value or 'steel' in class_value or 'metall' in class_value:
                                return "Metal"
                            elif 'holz' in class_value or 'wood' in class_value:
                                return "Wood"
                            elif 'dämmung' in class_value or 'dämmstoff' in class_value or 'insulation' in class_value:
                                return "Insulation"
                            elif 'glas' in class_value or 'glass' in class_value:
                                return "Facade/Windows"
                            elif 'ziegel' in class_value or 'mauerwerk' in class_value or 'brick' in class_value:
                                return "Masonry"
                            elif 'mineralische baustoffe' in class_value:
                                # Check subcategories
                                if 'betonfertigteile' in class_value or 'betonwaren' in class_value:
                                    return "Concrete"
        
        # Fallback to name-based detection
        name_lower = name.lower()
        if 'beton' in name_lower or 'concrete' in name_lower:
            return "Concrete"
        elif 'stahl' in name_lower or 'steel' in name_lower:
            return "Metal"
        elif 'holz' in name_lower or 'wood' in name_lower:
            return "Wood"
        elif 'dämmung' in name_lower or 'dämmstoff' in name_lower:
            return "Insulation"
        elif 'glas' in name_lower:
            return "Facade/Windows"
        elif 'ziegel' in name_lower or 'mauerwerk' in name_lower:
            return "Masonry"
        elif 'putz' in name_lower or 'mörtel' in name_lower:
            return "Mortar/Plaster"
        else:
            return "Other Materials"
    
    def load_materials(self, search_query: str = None, limit: int = 100):
        """Load materials from Ökobaudat API"""
        endpoint = f"datastocks/{self.datastock_id}/processes"
        
        params = {
            'format': 'json',
            'pageSize': limit,
            'search': 'true',
            'compliance': self.compliance_a2  # EN 15804+A2 only
        }
        
        if search_query:
            params['name'] = search_query
        
        response = self._make_request(endpoint, params)
        
        if not response:
            return
        
        # Clear existing data for new search
        self.data.clear()
        self.materials_list.clear()
        
        # Process each EPD
        epds = response.get('data', [])
        for epd_summary in epds:
            # Get full EPD data
            epd_id = epd_summary.get('uuid')
            if not epd_id:
                continue
            
            # For now, use summary data to avoid too many API calls
            # In production, you might want to fetch full details on demand
            material_id = f"OKOBAU_{epd_id}"
            name = epd_summary.get('name', 'Unknown')
            
            # Basic transformation without full data
            self.data[material_id] = {
                "name": name,
                "category": self._determine_category_from_classification({}, name),
                "density": 0.0,  # Would need full EPD data
                "carbon_per_unit": 0.0,  # Would need full EPD data
                "unit": "kg CO₂-eq/kg",
                "okobaudat_id": epd_id
            }
        
        # Build materials list
        self.materials_list = [
            (id, mat["name"], mat["category"])
            for id, mat in self.data.items()
        ]
        self.materials_list.sort(key=lambda x: (x[2], x[1]))
        self._cached = True
        
        print(f"Loaded {len(self.data)} materials from Ökobaudat API")
    
    def get_full_material_data(self, material_id: str) -> Dict[str, Any]:
        """Get full material data including environmental indicators"""
        # Extract Ökobaudat ID from our material ID
        if material_id.startswith("OKOBAU_"):
            okobau_id = material_id.replace("OKOBAU_", "")
        else:
            return self.data.get(material_id, {})
        
        # Check if we already have full data
        if material_id in self.data and self.data[material_id].get('carbon_per_unit', 0) > 0:
            return self.data[material_id]
        
        # Fetch full EPD data
        endpoint = f"datastocks/{self.datastock_id}/processes/{okobau_id}"
        params = {
            'format': 'json',
            'view': 'extended'
        }
        
        epd_data = self._make_request(endpoint, params)
        if epd_data:
            # Transform and cache the full data
            full_data = self._transform_okobaudat_to_kbob_format(epd_data)
            material_id = f"OKOBAU_{okobau_id}"
            self.data[material_id] = full_data
            return full_data
        
        return self.data.get(material_id, {})
    
    def get_material_data(self, material_id: str) -> Dict[str, Any]:
        """Get material data by ID - fetches full data if needed"""
        if not self._cached:
            self.load_materials()
        
        # For Ökobaudat materials, fetch full data on demand
        if material_id.startswith("OKOBAU_"):
            return self.get_full_material_data(material_id)
        
        return self.data.get(material_id, {})
    
    def get_all_materials(self) -> List[Dict[str, Any]]:
        """Get all materials in a format compatible with the UI"""
        if not self._cached:
            self.load_materials()
        
        materials = []
        for material_id, data in self.data.items():
            try:
                gwp_value = data.get('carbon_per_unit')
                density_value = data.get('density')
                
                # Safely convert to float, handling None
                gwp = float(gwp_value) if gwp_value is not None else 0.0
                density = float(density_value) if density_value is not None else 0.0
                
                materials.append({
                    'id': material_id,
                    'name': data['name'],
                    'category': data['category'],
                    'gwp': gwp,
                    'density': density
                })
            except (TypeError, ValueError) as e:
                print(f"Error processing material {material_id}: {e}")
                # Still add the material but with zero values
                materials.append({
                    'id': material_id,
                    'name': data.get('name', 'Unknown'),
                    'category': data.get('category', 'Unknown'),
                    'gwp': 0.0,
                    'density': 0.0
                })
        return materials
    
    def search_materials(self, query: str) -> List[Dict[str, str]]:
        """Search materials - triggers API search"""
        # Perform API search
        self.load_materials(search_query=query, limit=50)
        
        # Return results in expected format
        return [
            {
                'id': material_id,
                'name': data['name'],
                'category': data['category']
            }
            for material_id, data in self.data.items()
        ]


def get_extended_database_reader(database_type: str, data_path: str = None) -> CarbonDatabaseReader:
    """Get the appropriate database reader based on type"""
    if database_type == 'KBOB':
        # Use KBOB reader from ifclca_core
        return get_core_database_reader('KBOB', data_path)
    elif database_type == 'OKOBAUDAT_API':
        # Use extended API reader
        return OkobaudatAPIReader(api_key=data_path)
    elif database_type == 'CUSTOM':
        # Use custom reader from ifclca_core
        return get_core_database_reader('CUSTOM', data_path)
    else:
        raise ValueError(f"Unknown database type: {database_type}") 