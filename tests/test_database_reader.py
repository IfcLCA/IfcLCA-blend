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
        # Should load from JSON file if available
        if len(reader.data) > 0:
            assert len(reader.materials_list) > 0
            
            # Check some materials loaded
            material_names = [name for _, name, _ in reader.materials_list]
            # KBOB has concrete materials (Beton in German)
            assert any('beton' in name.lower() or 'concrete' in name.lower() for name in material_names)
    
    def test_load_custom_kbob_file(self):
        """Test loading custom KBOB JSON file"""
        from database_reader import KBOBDatabaseReader
        
        # Create temporary custom database in KBOB JSON format
        custom_data = [
            {
                "KBOB_ID": 99.001,
                "Name": "Test Material 1",
                "GWP": 0.5,  # in kg CO₂-eq/kg
                "PENRE": 1000,
                "kg/unit": 1000
            },
            {
                "KBOB_ID": 1.999,
                "Name": "Test Concrete",
                "GWP": 0.1,  # in kg CO₂-eq/kg
                "PENRE": 200,
                "kg/unit": 2400,
                "UBP": 150
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_data, f)
            temp_path = f.name
        
        try:
            reader = KBOBDatabaseReader(temp_path)
            
            assert len(reader.data) == 2
            assert len(reader.materials_list) == 2
            
            # Check materials
            test_mat = reader.get_material_data('KBOB_99.001')
            assert test_mat['name'] == 'Test Material 1'
            assert test_mat['carbon_per_unit'] == pytest.approx(0.5)  # 0.5 kg CO₂-eq/kg
            assert test_mat['density'] == 1000
            assert test_mat['category'] == 'Other Materials'
            
            concrete_mat = reader.get_material_data('KBOB_1.999')
            assert concrete_mat['name'] == 'Test Concrete'
            assert concrete_mat['carbon_per_unit'] == pytest.approx(0.1)  # 0.1 kg CO₂-eq/kg
            assert concrete_mat['category'] == 'Concrete'
        finally:
            os.unlink(temp_path)
    
    # NOTE: OkobaudatDatabaseReader has been removed in favor of OkobaudatAPIReader
    # The following tests are commented out as they reference the removed class
    '''
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
    '''
    
    def test_search_materials(self):
        """Test material search functionality"""
        from database_reader import KBOBDatabaseReader
        
        reader = KBOBDatabaseReader()
        
        # If database loaded successfully
        if len(reader.materials_list) > 0:
            # Search for beton (concrete in German)
            results = reader.search_materials('beton')
            if len(results) > 0:
                assert all('beton' in name.lower() for _, name, _ in results)
            
            # Search by category
            results = reader.search_materials('concrete')
            # Should find by category if not by name
            
            # Empty search returns all
            results = reader.search_materials('')
            assert len(results) == len(reader.materials_list)
    
    def test_get_material_by_id(self):
        """Test getting material by ID"""
        from database_reader import KBOBDatabaseReader
        
        reader = KBOBDatabaseReader()
        
        # If database loaded successfully
        if len(reader.data) > 0:
            # Get first material from the list
            first_id = reader.materials_list[0][0] if reader.materials_list else None
            if first_id:
                material = reader.get_material_data(first_id)
                assert material is not None
                assert 'name' in material
                assert 'category' in material
        
        # Non-existent ID
        material = reader.get_material_data('INVALID_ID')
        assert material == {}
    
    '''
    def test_missing_database_file(self):
        """Test handling missing database file"""
        from database_reader import OkobaudatDatabaseReader
        
        # Invalid file path should raise ValueError
        with pytest.raises(ValueError, match="ÖKOBAUDAT CSV file not found"):
            OkobaudatDatabaseReader('/non/existent/file.csv')
    '''
    
    def test_database_categories(self):
        """Test getting material categories"""
        from database_reader import KBOBDatabaseReader
        
        reader = KBOBDatabaseReader()
        
        # If database loaded successfully
        if len(reader.materials_list) > 0:
            # Get unique categories
            categories = set(cat for _, _, cat in reader.materials_list)
            
            # Check expected categories based on KBOB structure
            expected_categories = {'Concrete', 'Metal', 'Wood', 'Insulation', 'Masonry'}
            assert len(categories.intersection(expected_categories)) >= 1
    
    def test_kbob_json_parsing(self):
        """Test parsing of KBOB JSON with special cases"""
        from database_reader import KBOBDatabaseReader
        
        # Create test data with various edge cases
        test_data = [
            {
                "KBOB_ID": 0.001,
                "Name": "Foundation material",
                "GWP": 0.1,  # 0.1 kg CO₂-eq/kg
                "kg/unit": "-"  # No density
            },
            {
                "KBOB_ID": 10.001,
                "Name": "Insulation with range",
                "GWP": 1.1,  # 1.1 kg CO₂-eq/kg
                "PENRE": 7800,
                "min density": 20,
                "max density": 100  # Density range
            },
            {
                "KBOB_ID": 5.001,
                "Name": "Window material",
                "GWP": 0,  # Zero GWP
                "kg/unit": 2500
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            reader = KBOBDatabaseReader(temp_path)
            
            # Check foundation material without density
            foundation = reader.get_material_data('KBOB_0.001')
            assert foundation['density'] is None
            assert foundation['category'] == 'Foundation/Excavation'
            
            # Check material with density range
            insulation = reader.get_material_data('KBOB_10.001')
            assert insulation['density'] == 60  # Average of 20 and 100
            assert insulation['carbon_per_unit'] == pytest.approx(1.1)  # 1.1 kg CO₂-eq/kg
            
            # Check material with zero GWP
            window = reader.get_material_data('KBOB_5.001')
            assert window['carbon_per_unit'] == 0
            assert window['category'] == 'Facade/Windows'
        finally:
            os.unlink(temp_path)


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
        from database_reader import get_extended_database_reader
        
        # Get appropriate reader based on type
        reader = get_extended_database_reader('KBOB')
        
        assert reader is not None
        # Check it's an instance of the expected class
        from database_reader import KBOBDatabaseReader
        assert isinstance(reader, KBOBDatabaseReader)
        assert hasattr(reader, 'get_material_data')
        # Materials list may be empty if JSON not found
        assert hasattr(reader, 'materials_list')
    
    '''
    # This test is also removed as it references the old OKOBAUDAT database type and get_database_reader
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
    '''

    # NOTE: OkobaudatDatabaseReader has been removed in favor of OkobaudatAPIReader
    # The old tests are kept commented for reference
    '''
    def test_okobaudat_reader_init(self, temp_csv_okobaudat):
        """Test ÖKOBAUDAT reader initialization"""
        from database_reader import OkobaudatDatabaseReader
        
        reader = OkobaudatDatabaseReader(temp_csv_okobaudat)
        assert len(reader.data) == 1
        assert 'OKOBAUDAT_001' in reader.data
    ''' 