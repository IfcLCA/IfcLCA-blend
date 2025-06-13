"""
Tests for IfcLCA-blend database reader

Tests database loading and material search functionality
"""

import pytest
import os
import json
import tempfile
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.mock_bpy import setup_mock_modules, cleanup_mock_modules


class TestBlendDatabaseReader:
    """Test Blender addon database reader"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and cleanup mock modules"""
        setup_mock_modules()
        yield
        cleanup_mock_modules()
    
    def test_load_kbob_database(self):
        """Test loading KBOB database"""
        from database_reader import KBOBDatabaseReader
        
        reader = KBOBDatabaseReader()
        
        assert reader.data is not None
        assert len(reader.data) > 0
        assert len(reader.materials_list) > 0
        
        # Check some materials loaded
        material_names = [name for _, name, _ in reader.materials_list]
        assert any('Concrete' in name for name in material_names)
        assert any('steel' in name for name in material_names)
    
    def test_load_custom_kbob_file(self):
        """Test loading custom KBOB JSON file"""
        from database_reader import KBOBDatabaseReader
        
        # Create temporary custom database
        custom_data = {
            "TEST_MAT_1": {
                "name": "Test Material 1",
                "category": "Test",
                "density": 1000,
                "carbon_per_unit": 0.5,
                "unit": "kgCO2e/kg"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_data, f)
            temp_path = f.name
        
        try:
            reader = KBOBDatabaseReader(temp_path)
            
            assert len(reader.data) == 1
            assert len(reader.materials_list) == 1
            assert reader.materials_list[0][1] == 'Test Material 1'
            assert reader.materials_list[0][0] == 'TEST_MAT_1'
        finally:
            os.unlink(temp_path)
    
    def test_load_okobaudat_csv(self):
        """Test loading ÖKOBAUDAT CSV file"""
        from database_reader import OkobaudatDatabaseReader
        
        # Create temporary CSV file with the expected format
        csv_content = """ID,Name,Category,Density,GWP100,Unit
1.1.01,Beton C20/25,Beton,2300,0.0896,kg
1.2.01,Bewehrungsstahl,Stahl,7850,0.769,kg"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            reader = OkobaudatDatabaseReader(temp_path)
            
            assert len(reader.data) == 2
            assert len(reader.materials_list) == 2
            
            # Check materials
            concrete_data = reader.data.get('1.1.01')
            assert concrete_data is not None
            assert concrete_data['density'] == 2300
            assert concrete_data['carbon_per_unit'] == pytest.approx(0.0896)
        finally:
            os.unlink(temp_path)
    
    def test_search_materials(self):
        """Test material search functionality"""
        from database_reader import KBOBDatabaseReader
        
        reader = KBOBDatabaseReader()
        
        # Search for concrete
        results = reader.search_materials('concrete')
        assert len(results) > 0
        assert all('concrete' in name.lower() for _, name, _ in results)
        
        # Search for steel
        results = reader.search_materials('steel')
        assert len(results) > 0
        
        # Empty search returns all
        results = reader.search_materials('')
        assert len(results) == len(reader.materials_list)
    
    def test_get_material_by_id(self):
        """Test getting material by ID"""
        from database_reader import KBOBDatabaseReader
        
        reader = KBOBDatabaseReader()
        
        # Get specific material
        material = reader.get_material_data('KBOB_CONCRETE_C30_37')
        assert material is not None
        assert material['name'] == 'Concrete C30/37'
        assert material['category'] == 'Concrete'
        
        # Non-existent ID
        material = reader.get_material_data('INVALID_ID')
        assert material == {}
    
    def test_missing_database_file(self):
        """Test handling missing database file"""
        from database_reader import OkobaudatDatabaseReader
        
        # Invalid file path should raise ValueError
        with pytest.raises(ValueError, match="ÖKOBAUDAT CSV file not found"):
            OkobaudatDatabaseReader('/non/existent/file.csv')
    
    def test_database_categories(self):
        """Test getting material categories"""
        from database_reader import KBOBDatabaseReader
        
        reader = KBOBDatabaseReader()
        
        # Get unique categories
        categories = set(cat for _, _, cat in reader.materials_list)
        
        assert 'Concrete' in categories
        assert 'Metal' in categories
        assert 'Wood' in categories
        assert len(categories) >= 4  # At least 4 categories in KBOB


class TestDatabaseIntegration:
    """Test database integration with properties"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and cleanup mock modules"""
        bpy, bonsai, ifc = setup_mock_modules()
        self.bpy = bpy
        yield
        cleanup_mock_modules()
    
    def test_database_with_properties(self):
        """Test database reader with Blender properties"""
        from database_reader import get_database_reader
        
        # Get appropriate reader based on type
        reader = get_database_reader('KBOB')
        
        assert reader is not None
        # Check it's an instance of the expected class
        from database_reader import KBOBDatabaseReader
        assert isinstance(reader, KBOBDatabaseReader)
        assert hasattr(reader, 'get_material_data')
        assert len(reader.materials_list) > 0
    
    def test_okobaudat_with_file_property(self):
        """Test ÖKOBAUDAT loading from property"""
        from database_reader import get_database_reader
        
        # Create temp CSV
        csv_content = """ID,Name,Category,Density,GWP100,Unit
1,Test,TestCat,1000,0.5,kg"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            # Should work with file path
            reader = get_database_reader('OKOBAUDAT', temp_path)
            assert reader is not None
            assert len(reader.materials_list) == 1
            
            # Should raise without file path
            with pytest.raises(ValueError):
                get_database_reader('OKOBAUDAT')
        finally:
            os.unlink(temp_path) 