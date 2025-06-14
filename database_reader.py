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
            self.load_from_file(data_path)
        else:
            self.load_default_data()
    
    def load_default_data(self):
        """Load default KBOB data (subset for demo)"""
        # This is a representative subset of KBOB 2022 data
        # Units: density in kg/m³, carbon_per_unit in kg CO₂-eq/kg
        self.data = {
            "KBOB_CONCRETE_C25_30": {
                "name": "Concrete C25/30",
                "category": "Concrete",
                "density": 2400,
                "carbon_per_unit": 0.0941,
                "unit": "kg CO₂-eq/kg"
            },
            "KBOB_CONCRETE_C30_37": {
                "name": "Concrete C30/37",
                "category": "Concrete", 
                "density": 2400,
                "carbon_per_unit": 0.100,
                "unit": "kg CO₂-eq/kg"
            },
            "KBOB_CONCRETE_C35_45": {
                "name": "Concrete C35/45",
                "category": "Concrete",
                "density": 2400,
                "carbon_per_unit": 0.110,
                "unit": "kg CO₂-eq/kg"
            },
            "KBOB_STEEL_REINFORCING": {
                "name": "Reinforcing steel",
                "category": "Metal",
                "density": 7850,
                "carbon_per_unit": 0.750,
                "unit": "kg CO₂-eq/kg"
            },
            "KBOB_STEEL_STRUCTURAL": {
                "name": "Structural steel",
                "category": "Metal",
                "density": 7850,
                "carbon_per_unit": 1.44,
                "unit": "kg CO₂-eq/kg"
            },
            "KBOB_TIMBER_GLULAM": {
                "name": "Glulam timber",
                "category": "Wood",
                "density": 470,
                "carbon_per_unit": -0.655,  # Negative due to carbon storage
                "unit": "kg CO₂-eq/kg"
            },
            "KBOB_TIMBER_CLT": {
                "name": "Cross-laminated timber (CLT)",
                "category": "Wood",
                "density": 470,
                "carbon_per_unit": -0.580,
                "unit": "kg CO₂-eq/kg"
            },
            "KBOB_BRICK_CLAY": {
                "name": "Clay brick",
                "category": "Masonry",
                "density": 1800,
                "carbon_per_unit": 0.160,
                "unit": "kg CO₂-eq/kg"
            },
            "KBOB_INSULATION_MINERAL_WOOL": {
                "name": "Mineral wool insulation",
                "category": "Insulation",
                "density": 100,
                "carbon_per_unit": 1.28,
                "unit": "kg CO₂-eq/kg"
            },
            "KBOB_INSULATION_EPS": {
                "name": "EPS insulation",
                "category": "Insulation",
                "density": 20,
                "carbon_per_unit": 3.29,
                "unit": "kg CO₂-eq/kg"
            },
            "KBOB_GLASS_FLOAT": {
                "name": "Float glass",
                "category": "Glass",
                "density": 2500,
                "carbon_per_unit": 0.790,
                "unit": "kg CO₂-eq/kg"
            },
            "KBOB_PLASTER": {
                "name": "Gypsum plaster",
                "category": "Finishes",
                "density": 1200,
                "carbon_per_unit": 0.120,
                "unit": "kg CO₂-eq/kg"
            }
        }
        
        # Build materials list
        self.materials_list = [
            (id, mat["name"], mat["category"])
            for id, mat in self.data.items()
        ]
        self.materials_list.sort(key=lambda x: (x[2], x[1]))  # Sort by category, then name
    
    def load_from_file(self, filepath: str):
        """Load KBOB data from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        # Build materials list
        self.materials_list = [
            (id, mat.get("name", id), mat.get("category", "Uncategorized"))
            for id, mat in self.data.items()
        ]
        self.materials_list.sort(key=lambda x: (x[2], x[1]))


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