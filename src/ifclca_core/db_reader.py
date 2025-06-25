"""
Database Readers for Environmental Impact Data

Supports multiple LCA databases including:
- KBOB (Swiss) - JSON format
- ÖKOBAUDAT (German) - CSV format
- Custom JSON databases

Environmental indicators supported:
- GWP: Global Warming Potential (kg CO2-eq)
- PEnr: Primary Energy non-renewable (MJ or kWh)
- UBP: Environmental Impact Points (Swiss method)
"""

import json
import csv
import os
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


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
                'gwp': mat_data.get('gwp', 0),
                'density': mat_data.get('density', 0),
                'penr': mat_data.get('penr', 0),
                'ubp': mat_data.get('ubp')
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
            self.load_default_kbob_json()
    
    def load(self, db_path: str) -> None:
        """Load KBOB data from JSON file."""
        with open(db_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Handle both old format (dict) and new format (array)
        if isinstance(raw_data, dict):
            # Old format: direct material ID mapping
            for mat_id, mat_data in raw_data.items():
                self.db[mat_id] = self._normalize_material_data(mat_data)
        elif isinstance(raw_data, list):
            # New format: array of materials from indicatorsKBOB_v6.json
            self._load_kbob_v6_format(raw_data)
    
    def load_default_kbob_json(self) -> None:
        """Load default KBOB data from indicatorsKBOB_v6.json."""
        # Try to find indicatorsKBOB_v6.json
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'indicatorsKBOB_v6.json'),
            os.path.join(os.path.dirname(__file__), '..', 'assets', 'indicatorsKBOB_v6.json'),
            os.path.join(os.path.dirname(__file__), 'indicatorsKBOB_v6.json'),
            'assets/indicatorsKBOB_v6.json',
            'indicatorsKBOB_v6.json'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        raw_data = json.load(f)
                    self._load_kbob_v6_format(raw_data)
                    print(f"Loaded KBOB database from: {path}")
                    return
                except Exception as e:
                    print(f"Error loading KBOB from {path}: {e}")
                    continue
        
        print("Warning: indicatorsKBOB_v6.json not found. Using minimal fallback data.")
        # Minimal fallback if JSON not found
        self.db = {
            "KBOB_FALLBACK": {
                "name": "Database not loaded",
                "category": "Error",
                "density": 0,
                "gwp": 0,
                "penr": 0,
                "ubp": 0,
                "unit": "kg"
            }
        }
    
    def _load_kbob_v6_format(self, raw_data: List[Dict[str, Any]]) -> None:
        """Load KBOB data from v6 JSON format."""
        valid_count = 0
        skipped_count = 0
        
        for item in raw_data:
            try:
                # Extract and validate data using the new method
                material_data = self._extract_kbob_data(item)
                
                if material_data:  # Only add if validation passed
                    # Create material ID
                    kbob_id_str = str(material_data['id'])
                    material_id = f"KBOB_{kbob_id_str}"
                    
                    # Store in database
                    self.db[material_id] = material_data
                    valid_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                logger.error(f"Error parsing KBOB item: {e}")
                skipped_count += 1
                continue
        
        logger.info(f"Loaded {valid_count} valid KBOB materials, skipped {skipped_count} invalid entries")
    
    def _determine_category(self, name: str, kbob_id: Any) -> str:
        """Determine material category based on name or KBOB ID."""
        # Try to get numeric value for categorization
        try:
            if isinstance(kbob_id, str):
                # Handle string IDs like "01.002.01"
                kbob_id_float = float(kbob_id.split('.')[0])
            else:
                kbob_id_float = float(kbob_id)
        except:
            kbob_id_float = 99  # Default
        
        # Category mapping based on KBOB ID ranges
        if kbob_id_float < 1:
            return "Foundation/Excavation"
        elif 1 <= kbob_id_float < 2:
            return "Concrete"
        elif 2 <= kbob_id_float < 3:
            return "Masonry"
        elif 3 <= kbob_id_float < 4:
            return "Mineral/Stone"
        elif 4 <= kbob_id_float < 5:
            return "Mortar/Plaster"
        elif 5 <= kbob_id_float < 6:
            return "Facade/Windows"
        elif 6 <= kbob_id_float < 7:
            return "Metal"
        elif 7 <= kbob_id_float < 8:
            return "Wood"
        elif 8 <= kbob_id_float < 9:
            return "Sealants/Adhesives"
        elif 9 <= kbob_id_float < 10:
            return "Membranes/Foils"
        elif 10 <= kbob_id_float < 11:
            return "Insulation"
        elif 11 <= kbob_id_float < 12:
            return "Flooring"
        elif 12 <= kbob_id_float < 13:
            return "Doors"
        elif 13 <= kbob_id_float < 14:
            return "Plastics/Pipes"
        elif 14 <= kbob_id_float < 15:
            return "Coatings"
        elif 15 <= kbob_id_float < 21:
            return "Other Materials"
        elif 21 <= kbob_id_float:
            return "Kitchen/Interior"
        else:
            return "Uncategorized"
    
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

    def _extract_kbob_data(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize KBOB data from JSON item."""
        kbob_id = str(item.get('KBOB_ID', ''))
        name = item.get('Name', f'Material {kbob_id}')
        
        # Validate name - skip corrupted entries
        if not name or len(name) < 2:
            # logger.warning(f"Skipping KBOB entry {kbob_id}: invalid name")
            return None
            
        # Check for corrupted characters
        weird_char_count = sum(1 for char in name if ord(char) < 32 or char in '¤¶`^')
        if weird_char_count > len(name) * 0.2:  # More than 20% weird chars
            # logger.warning(f"Skipping KBOB entry {kbob_id}: corrupted name '{name}'")
            return None
            
        # Check for specific weird patterns
        if any(pattern in name for pattern in ['*a', '+I', '\\+I']):
            # logger.warning(f"Skipping KBOB entry {kbob_id}: suspicious pattern in name '{name}'")
            return None
            
        # Must have at least one letter
        if not any(c.isalpha() for c in name):
            # logger.warning(f"Skipping KBOB entry {kbob_id}: no letters in name '{name}'")
            return None
        
        gwp = item.get('GWP', 0)
        penre = item.get('PENRE', 0)
        ubp = item.get('UBP')
        
        # Extract density from kg/unit field
        density = 0
        kg_unit = item.get('kg/unit', '-')
        
        if kg_unit != '-' and kg_unit is not None:
            try:
                density = float(kg_unit)
            except (ValueError, TypeError):
                density = 0
        
        # Check for min/max density if kg/unit not available
        if density == 0:
            min_density = item.get('min density')
            max_density = item.get('max density')
            if min_density is not None and max_density is not None:
                try:
                    density = (float(min_density) + float(max_density)) / 2
                except (ValueError, TypeError):
                    density = 0
        
        # Determine category based on ID ranges
        category = self._determine_category(name, kbob_id)
        
        return {
            'id': kbob_id,
            'name': name,
            'category': category,
            'gwp': gwp / 1000 if gwp else 0,  # Convert g to kg
            'carbon_per_unit': gwp / 1000 if gwp else 0,  # For compatibility
            'penr': penre,
            'unit': 'kg',
            'ubp': ubp,
            'density': density  # Now properly extracted from the data
        }


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