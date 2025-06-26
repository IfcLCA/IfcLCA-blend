import json
import csv
import os
from typing import Dict, Any, List, Tuple

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


class OkobaudatDatabaseReader(CarbonDatabaseReader):
    """Reader for ÖKOBAUDAT database (German)"""
    
    def __init__(self, csv_path: str):
        super().__init__()
        if csv_path and os.path.exists(csv_path):
            self.load_from_csv(csv_path)
        else:
            raise ValueError(f"ÖKOBAUDAT CSV file not found at: {csv_path}")
    
    def load_from_csv(self, filepath: str):
        """Load ÖKOBAUDAT data from CSV file"""
        # Note: This is a simplified parser. Real ÖKOBAUDAT CSV has complex structure
        # For now, we'll assume a simplified format with columns:
        # ID, Name, Category, Density, GWP100, Unit
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    material_id = row.get('ID', '').strip()
                    if not material_id:
                        continue
                    
                    # Parse density and GWP values
                    density = float(row.get('Density', '0').replace(',', '.'))
                    gwp = float(row.get('GWP100', '0').replace(',', '.'))
                    
                    # Determine if GWP is per kg or per m³
                    unit = row.get('Unit', 'kg').lower()
                    if 'm3' in unit or 'm³' in unit:
                        # Convert to per kg
                        if density > 0:
                            gwp = gwp / density
                        carbon_unit = "kg CO₂-eq/kg"
                    else:
                        carbon_unit = "kg CO₂-eq/kg"
                    
                    self.data[material_id] = {
                        "name": row.get('Name', material_id),
                        "category": row.get('Category', 'Uncategorized'),
                        "density": density,
                        "carbon_per_unit": gwp,
                        "unit": carbon_unit
                    }
                except (ValueError, KeyError) as e:
                    print(f"Error parsing ÖKOBAUDAT row: {e}")
                    continue
        
        # Build materials list
        self.materials_list = [
            (id, mat["name"], mat["category"])
            for id, mat in self.data.items()
        ]
        self.materials_list.sort(key=lambda x: (x[2], x[1]))


def get_database_reader(database_type: str, data_path: str = None) -> CarbonDatabaseReader:
    """Factory function to get appropriate database reader"""
    if database_type == 'KBOB':
        return KBOBDatabaseReader(data_path)
    elif database_type == 'OKOBAUDAT':
        if not data_path:
            raise ValueError("ÖKOBAUDAT requires a CSV file path")
        return OkobaudatDatabaseReader(data_path)
    else:
        raise ValueError(f"Unknown database type: {database_type}") 