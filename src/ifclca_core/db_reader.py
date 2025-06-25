"""
Database Readers for Environmental Impact Data

Supports multiple LCA databases including:
- KBOB (Swiss) - JSON format
- ÖKOBAUDAT (German) - CSV format
- Custom JSON databases

Environmental indicators supported:
- GWP: Global Warming Potential (kg CO2-eq)
- PEnr: Primary Energy non-renewable (MJ)
- UBP: Environmental Impact Points (Swiss method)
"""

import json
import csv
import os
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod


class IfcLCADBReader(ABC):
    """Abstract base class for LCA database readers."""
    
    def __init__(self):
        self.db = {}
        self.materials_index = {}
        
    @abstractmethod
    def load(self, db_path: str) -> None:
        """Load database from file."""
        pass
    
    def get_material_data(self, material_id: str) -> Dict[str, Any]:
        """
        Get material data by ID.
        
        Returns dictionary with keys:
        - name: Material name
        - category: Material category
        - density: Density in kg/m³
        - gwp: Global Warming Potential in kg CO2-eq per kg
        - penr: Primary Energy non-renewable in MJ per kg
        - ubp: Environmental Impact Points per kg
        - unit: Reference unit (typically kg)
        """
        return self.db.get(material_id, {})
    
    def search_materials(self, query: str) -> List[Dict[str, Any]]:
        """Search materials by name or category."""
        results = []
        query_lower = query.lower()
        
        for mat_id, mat_data in self.db.items():
            name = mat_data.get('name', '').lower()
            category = mat_data.get('category', '').lower()
            
            if query_lower in name or query_lower in category:
                results.append({
                    'id': mat_id,
                    'name': mat_data.get('name'),
                    'category': mat_data.get('category'),
                    'gwp': mat_data.get('gwp', 0)
                })
        
        return sorted(results, key=lambda x: x['name'])
    
    def get_all_materials(self) -> List[Dict[str, Any]]:
        """Get all materials in the database."""
        results = []
        for mat_id, mat_data in self.db.items():
            results.append({
                'id': mat_id,
                'name': mat_data.get('name'),
                'category': mat_data.get('category'),
                'gwp': mat_data.get('gwp', 0)
            })
        return sorted(results, key=lambda x: (x['category'], x['name']))
    
    def get_materials_list(self) -> List[Tuple[str, str, str]]:
        """Get list of all materials as (id, name, category) tuples for compatibility."""
        results = []
        for mat_id, mat_data in self.db.items():
            results.append((
                mat_id,
                mat_data.get('name', ''),
                mat_data.get('category', 'Uncategorized')
            ))
        return sorted(results, key=lambda x: (x[2], x[1]))


class KBOBReader(IfcLCADBReader):
    """Reader for KBOB (Swiss) environmental data in JSON format."""
    
    def __init__(self, db_path: Optional[str] = None):
        super().__init__()
        if db_path:
            self.load(db_path)
        else:
            self.load_default_data()
    
    def load(self, db_path: str) -> None:
        """Load KBOB data from JSON file."""
        with open(db_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Process and normalize the data
        for mat_id, mat_data in raw_data.items():
            self.db[mat_id] = self._normalize_material_data(mat_data)
    
    def load_default_data(self) -> None:
        """Load default KBOB 2022 data subset."""
        # Representative subset of KBOB 2022 data
        default_data = {
            "KBOB_CONCRETE_C25_30": {
                "name": "Concrete C25/30",
                "category": "Concrete",
                "density": 2400,
                "gwp": 0.0941,
                "penr": 0.951,
                "ubp": 118,
                "unit": "kg"
            },
            "KBOB_CONCRETE_C30_37": {
                "name": "Concrete C30/37",
                "category": "Concrete",
                "density": 2400,
                "gwp": 0.100,
                "penr": 1.01,
                "ubp": 125,
                "unit": "kg"
            },
            "KBOB_CONCRETE_C35_45": {
                "name": "Concrete C35/45",
                "category": "Concrete",
                "density": 2400,
                "gwp": 0.110,
                "penr": 1.12,
                "ubp": 138,
                "unit": "kg"
            },
            "KBOB_CONCRETE_RC": {
                "name": "Recycled Concrete",
                "category": "Concrete",
                "density": 2300,
                "gwp": 0.0823,
                "penr": 0.831,
                "ubp": 103,
                "unit": "kg"
            },
            "KBOB_STEEL_REINFORCING": {
                "name": "Reinforcing steel (92% recycled)",
                "category": "Metal",
                "density": 7850,
                "gwp": 0.750,
                "penr": 9.46,
                "ubp": 967,
                "unit": "kg"
            },
            "KBOB_STEEL_STRUCTURAL": {
                "name": "Structural steel sections",
                "category": "Metal",
                "density": 7850,
                "gwp": 1.44,
                "penr": 18.1,
                "ubp": 1850,
                "unit": "kg"
            },
            "KBOB_TIMBER_GLULAM": {
                "name": "Glulam timber",
                "category": "Wood",
                "density": 470,
                "gwp": -0.655,  # Negative due to carbon storage
                "penr": 8.66,
                "ubp": 548,
                "unit": "kg"
            },
            "KBOB_TIMBER_CLT": {
                "name": "Cross-laminated timber (CLT)",
                "category": "Wood",
                "density": 470,
                "gwp": -0.580,
                "penr": 7.89,
                "ubp": 499,
                "unit": "kg"
            },
            "KBOB_BRICK_CLAY": {
                "name": "Clay brick",
                "category": "Masonry",
                "density": 1800,
                "gwp": 0.160,
                "penr": 2.51,
                "ubp": 267,
                "unit": "kg"
            },
            "KBOB_INSULATION_MINERAL_WOOL": {
                "name": "Mineral wool insulation",
                "category": "Insulation",
                "density": 100,
                "gwp": 1.28,
                "penr": 21.5,
                "ubp": 1770,
                "unit": "kg"
            },
            "KBOB_INSULATION_EPS": {
                "name": "EPS insulation",
                "category": "Insulation",
                "density": 20,
                "gwp": 3.29,
                "penr": 88.6,
                "ubp": 4190,
                "unit": "kg"
            },
            "KBOB_INSULATION_XPS": {
                "name": "XPS insulation",
                "category": "Insulation",
                "density": 35,
                "gwp": 3.87,
                "penr": 95.4,
                "ubp": 4890,
                "unit": "kg"
            },
            "KBOB_GLASS_FLOAT": {
                "name": "Float glass",
                "category": "Glass",
                "density": 2500,
                "gwp": 0.790,
                "penr": 11.8,
                "ubp": 1000,
                "unit": "kg"
            },
            "KBOB_PLASTER": {
                "name": "Gypsum plaster",
                "category": "Finishes",
                "density": 1200,
                "gwp": 0.120,
                "penr": 1.86,
                "ubp": 197,
                "unit": "kg"
            }
        }
        
        for mat_id, mat_data in default_data.items():
            self.db[mat_id] = self._normalize_material_data(mat_data)
    
    def _normalize_material_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize material data to standard format."""
        # KBOB typically provides data per kg
        # Ensure backwards compatibility with carbon_per_unit
        normalized = {
            'name': data.get('name', ''),
            'category': data.get('category', 'Uncategorized'),
            'density': float(data.get('density', 0)),
            'gwp': float(data.get('gwp', 0)),
            'penr': float(data.get('penr', 0)),
            'ubp': float(data.get('ubp', 0)),
            'unit': data.get('unit', 'kg'),
            # Legacy support
            'carbon_per_unit': float(data.get('gwp', data.get('carbon_per_unit', 0)))
        }
        return normalized


class OkobaudatReader(IfcLCADBReader):
    """Reader for ÖKOBAUDAT (German) environmental data in CSV format."""
    
    def __init__(self, db_path: str):
        super().__init__()
        self.load(db_path)
    
    def load(self, db_path: str) -> None:
        """Load ÖKOBAUDAT data from CSV file."""
        if not os.path.exists(db_path):
            raise ValueError(f"CSV file not found: {db_path}")
            
        with open(db_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            for row in reader:
                try:
                    material_id = row.get('UUID', row.get('ID', '')).strip()
                    if not material_id:
                        continue
                    
                    # Extract and convert values
                    mat_data = self._parse_okobaudat_row(row)
                    if mat_data:
                        self.db[material_id] = mat_data
                        
                except (ValueError, KeyError) as e:
                    print(f"Warning: Error parsing ÖKOBAUDAT row: {e}")
                    continue
    
    def _parse_okobaudat_row(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse a row from ÖKOBAUDAT CSV."""
        # ÖKOBAUDAT has various column naming conventions
        # Try multiple possible column names
        
        name = (row.get('Name_de') or row.get('Name') or 
                row.get('Material') or '').strip()
        if not name:
            return None
        
        # Category might be in different columns
        category = (row.get('Category_de') or row.get('Category') or 
                   row.get('Kategorie') or 'Uncategorized').strip()
        
        # Density in kg/m³
        density = self._parse_float(
            row.get('Rohdichte') or row.get('Density') or '0'
        )
        
        # GWP (Global Warming Potential) in kg CO2-eq
        gwp = self._parse_float(
            row.get('GWP-total') or row.get('GWP100') or 
            row.get('Treibhauspotenzial') or '0'
        )
        
        # Primary Energy non-renewable in MJ
        penr = self._parse_float(
            row.get('PENRT') or row.get('PENR') or 
            row.get('PEne') or '0'
        )
        
        # Reference unit and quantity
        ref_unit = (row.get('Bezugseinheit') or row.get('Unit') or 'kg').lower()
        ref_quantity = self._parse_float(
            row.get('Bezugsgröße') or row.get('RefQuantity') or '1'
        )
        
        # Normalize to per kg if needed
        if 'm3' in ref_unit or 'm³' in ref_unit:
            if density > 0:
                gwp = gwp / density
                penr = penr / density
        elif ref_quantity != 1:
            gwp = gwp / ref_quantity
            penr = penr / ref_quantity
        
        return {
            'name': name,
            'category': category,
            'density': density,
            'gwp': gwp,
            'penr': penr,
            'ubp': 0,  # UBP not available in ÖKOBAUDAT
            'unit': 'kg',
            # Legacy support
            'carbon_per_unit': gwp
        }
    
    def _parse_float(self, value: str) -> float:
        """Parse float from string, handling German decimal notation."""
        if not value:
            return 0.0
        # Replace German decimal comma with dot
        value = value.replace(',', '.')
        try:
            return float(value)
        except ValueError:
            return 0.0


class CustomJSONReader(IfcLCADBReader):
    """Reader for custom JSON format databases."""
    
    def __init__(self, db_path: str):
        super().__init__()
        self.load(db_path)
    
    def load(self, db_path: str) -> None:
        """Load custom JSON database."""
        with open(db_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Expect JSON with material ID as key and properties as value
        for mat_id, mat_data in raw_data.items():
            self.db[mat_id] = {
                'name': mat_data.get('name', mat_id),
                'category': mat_data.get('category', 'Uncategorized'),
                'density': float(mat_data.get('density', 0)),
                'gwp': float(mat_data.get('gwp', mat_data.get('carbon_per_unit', 0))),
                'penr': float(mat_data.get('penr', 0)),
                'ubp': float(mat_data.get('ubp', 0)),
                'unit': mat_data.get('unit', 'kg'),
                # Legacy support
                'carbon_per_unit': float(mat_data.get('gwp', mat_data.get('carbon_per_unit', 0)))
            }


def get_database_reader(db_type: str, db_path: Optional[str] = None) -> IfcLCADBReader:
    """
    Factory function to create appropriate database reader.
    
    Args:
        db_type: Type of database ('KBOB', 'OKOBAUDAT', 'CUSTOM')
        db_path: Path to database file (optional for KBOB)
    
    Returns:
        Database reader instance
    """
    db_type = db_type.upper()
    
    if db_type == 'KBOB':
        return KBOBReader(db_path)
    elif db_type == 'OKOBAUDAT':
        if not db_path:
            raise ValueError("ÖKOBAUDAT requires a database file path")
        return OkobaudatReader(db_path)
    elif db_type == 'CUSTOM':
        if not db_path:
            raise ValueError("Custom database requires a file path")
        return CustomJSONReader(db_path)
    else:
        raise ValueError(f"Unknown database type: {db_type}")