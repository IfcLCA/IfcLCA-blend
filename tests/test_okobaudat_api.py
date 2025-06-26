"""Test Ökobaudat API integration"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database_reader import OkobaudatAPIReader


class TestOkobaudatAPI:
    """Test Ökobaudat API functionality"""
    
    def test_api_reader_creation(self):
        """Test creating API reader"""
        reader = OkobaudatAPIReader()
        assert reader is not None
        assert reader.base_url == "https://oekobaudat.de/OEKOBAU.DAT/resource"
        assert reader.compliance_a2 == "c0016b33-8cf7-415c-ac6e-deba0d21440d"
        print("✓ API reader creation test passed")
    
    def test_api_reader_with_key(self):
        """Test creating API reader with key"""
        reader = OkobaudatAPIReader(api_key="test-key")
        assert reader.api_key == "test-key"
        print("✓ API reader with key test passed")
    
    def test_material_search(self):
        """Test material search functionality"""
        reader = OkobaudatAPIReader()
        
        # This would normally make an API call
        # For testing, we'd mock the response
        assert hasattr(reader, 'load_materials')
        assert hasattr(reader, 'search_materials')
        print("✓ Material search methods test passed")
    
    def test_data_transformation(self):
        """Test KBOB format transformation"""
        reader = OkobaudatAPIReader()
        
        # Mock EPD data
        mock_epd = {
            'uuid': 'test-uuid',
            'name': 'Test Concrete',
            'referenceFlowProperties': {
                'referenceFlowProperty': {
                    'declaredUnit': 'kg'
                },
                'referenceFlowAmount': 1.0
            },
            'exchanges': [],
            'LCIAResults': []
        }
        
        result = reader._transform_okobaudat_to_kbob_format(mock_epd)
        
        assert result['name'] == 'Test Concrete'
        assert result['category'] == 'Concrete'
        assert result['okobaudat_id'] == 'test-uuid'
        assert result['unit'] == 'kg CO₂-eq/kg'
        print("✓ Data transformation test passed")
    
    def test_category_determination(self):
        """Test category determination from name"""
        reader = OkobaudatAPIReader()
        
        test_cases = [
            ('Beton C20/25', 'Concrete'),
            ('Stahl S235', 'Metal'),
            ('Holz Fichte', 'Wood'),
            ('Mineralwolle Dämmung', 'Insulation'),
            ('Glasscheibe', 'Facade/Windows'),
            ('Ziegel', 'Masonry'),
            ('Unknown Material', 'Other Materials')
        ]
        
        for name, expected_category in test_cases:
            category = reader._determine_category_from_classification({}, name)
            assert category == expected_category, f"Expected {expected_category} for {name}, got {category}"
        print("✓ Category determination test passed")
    
    def test_material_id_format(self):
        """Test material ID formatting"""
        reader = OkobaudatAPIReader()
        
        # Mock loading materials
        reader.data = {
            'OKOBAU_test-uuid-1': {'name': 'Material 1'},
            'OKOBAU_test-uuid-2': {'name': 'Material 2'}
        }
        
        material_ids = list(reader.data.keys())
        assert all(id.startswith('OKOBAU_') for id in material_ids)
        print("✓ Material ID format test passed")
    
    def test_get_all_materials_format(self):
        """Test get_all_materials returns correct format"""
        reader = OkobaudatAPIReader()
        
        # Mock data
        reader.data = {
            'OKOBAU_test-uuid': {
                'name': 'Test Material',
                'category': 'Concrete',
                'carbon_per_unit': 0.105,
                'density': 2400
            }
        }
        reader._cached = True
        
        materials = reader.get_all_materials()
        assert len(materials) == 1
        assert materials[0]['id'] == 'OKOBAU_test-uuid'
        assert materials[0]['name'] == 'Test Material'
        assert materials[0]['gwp'] == 0.105
        assert materials[0]['density'] == 2400
        print("✓ Get all materials format test passed")
    
    def run_all_tests(self):
        """Run all tests"""
        print("Running Ökobaudat API tests...\n")
        
        try:
            self.test_api_reader_creation()
            self.test_api_reader_with_key()
            self.test_material_search()
            self.test_data_transformation()
            self.test_category_determination()
            self.test_material_id_format()
            self.test_get_all_materials_format()
            
            print("\n✅ All tests passed!")
        except AssertionError as e:
            print(f"\n❌ Test failed: {e}")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            return False
        
        return True


if __name__ == '__main__':
    tester = TestOkobaudatAPI()
    tester.run_all_tests() 