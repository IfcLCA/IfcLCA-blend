import http.server
import socketserver
import threading
import webbrowser
import json
from pathlib import Path
import urllib.parse

WEB_DIR = Path(__file__).parent / 'assets' / 'web'

# Ensure the directory exists
if not WEB_DIR.exists():
    print(f"WARNING: Web directory not found at {WEB_DIR}")
    # Try alternative paths
    alt_paths = [
        Path(__file__).parent.parent / 'assets' / 'web',
        Path(__file__).parent / 'web',
        Path('assets') / 'web'
    ]
    for alt_path in alt_paths:
        if alt_path.exists():
            WEB_DIR = alt_path
            print(f"Using alternative web directory: {WEB_DIR}")
            break

class ResultsHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, results=None, detailed_results=None, ifc_file=None, **kwargs):
        self.results = results or {}
        self.detailed_results = detailed_results or {}
        self.ifc_file = ifc_file
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        # Debug logging
        print(f"Request path: {parsed_path.path}")
        print(f"Handler has IFC file: {hasattr(self, 'ifc_file') and self.ifc_file is not None}")
        
        if parsed_path.path == '/results':
            # Use detailed results if available, otherwise fall back to simple results
            data_to_send = self.detailed_results if self.detailed_results else self.results
            print(f"Sending /results data: {len(data_to_send)} materials")
            self.send_json_response(data_to_send)
        
        elif parsed_path.path == '/api/detailed_results':
            # Detailed results with all information
            print(f"Sending detailed results: {len(self.detailed_results)} materials")
            self.send_json_response(self.detailed_results)
        
        elif parsed_path.path == '/api/summary':
            # Summary statistics
            summary = self._calculate_summary()
            print(f"Sending summary: {summary}")
            self.send_json_response(summary)
        
        elif parsed_path.path == '/api/elements':
            # Get elements grouped by material
            print(f"API request for elements data. IFC file available: {self.ifc_file is not None}")
            elements_data = self._get_elements_data()
            print(f"Returning elements data with {len(elements_data)} materials")
            self.send_json_response(elements_data)
        
        elif parsed_path.path == '/api/debug':
            # Debug endpoint to check server state
            debug_info = {
                'has_ifc_file': self.ifc_file is not None,
                'ifc_file_type': str(type(self.ifc_file)) if self.ifc_file else None,
                'detailed_results_count': len(self.detailed_results) if self.detailed_results else 0,
                'detailed_results_keys': list(self.detailed_results.keys()) if self.detailed_results else []
            }
            self.send_json_response(debug_info)
        
        else:
            # Handle root path
            if parsed_path.path == '/' or parsed_path.path == '':
                self.path = '/index.html'
            
            # Serve static files
            print(f"Serving static file: {self.path}")
            super().do_GET()
    
    def send_json_response(self, data):
        """Send JSON response with proper headers"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def send_error_response(self, code, message):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        error_data = {'error': message, 'code': code}
        self.wfile.write(json.dumps(error_data).encode('utf-8'))
    
    def _calculate_summary(self):
        """Calculate summary statistics"""
        # Handle empty or None detailed_results
        if not self.detailed_results:
            return {
                'total_carbon': 0,
                'total_volume': 0,
                'total_mass': 0,
                'material_count': 0,
                'materials_with_impact': 0
            }
        
        total_carbon = sum(mat.get('total_carbon', 0) for mat in self.detailed_results.values())
        total_volume = sum(mat.get('total_volume', 0) for mat in self.detailed_results.values())
        total_mass = sum(mat.get('total_mass', 0) for mat in self.detailed_results.values())
        
        return {
            'total_carbon': total_carbon,
            'total_volume': total_volume,
            'total_mass': total_mass,
            'material_count': len(self.detailed_results),
            'materials_with_impact': sum(1 for mat in self.detailed_results.values() if mat.get('total_carbon', 0) > 0)
        }
    
    def _get_elements_data(self):
        """Get element-level data grouped by material"""
        elements_by_material = {}
        
        # Return empty object if no detailed results
        if not self.detailed_results:
            print("No detailed results available for elements data")
            return elements_by_material
        
        if self.ifc_file:
            try:
                # Import the material extractor from logic
                try:
                    from .logic import IfcMaterialExtractor
                except ImportError:
                    from .logic import IfcMaterialExtractor
                
                print(f"IFC file type: {type(self.ifc_file)}")
                print(f"Has by_type method: {hasattr(self.ifc_file, 'by_type')}")
                
                # Create material extractor
                extractor = IfcMaterialExtractor(self.ifc_file)
                
                # Initialize all materials first
                for material_name, details in self.detailed_results.items():
                    elements_by_material[material_name] = {
                        'material_info': details,
                        'elements': []
                    }
                
                # Get elements for each material
                print(f"Processing elements for {len(self.detailed_results)} materials...")
                
                for material_name in self.detailed_results.keys():
                    # Get all elements with this material using the new method
                    elements_info = extractor.get_elements_with_info_by_material(material_name)
                    
                    for elem_info in elements_info:
                        element = elem_info['element']
                        elem_data = {
                            'id': elem_info['id'],
                            'type': elem_info['type'],
                            'name': elem_info['name'],  # This now uses the proper extraction method
                            'volume': self._get_element_volume(element)
                        }
                        elements_by_material[material_name]['elements'].append(elem_data)
                    
                    if len(elements_info) > 0:
                        print(f"Material '{material_name}': {len(elements_info)} elements")
                        # Show first few element names as example
                        for i, elem in enumerate(elements_by_material[material_name]['elements'][:3]):
                            print(f"  - {elem['name']} ({elem['type']})")
                        if len(elements_info) > 3:
                            print(f"  ... and {len(elements_info) - 3} more")
                
                # Log summary
                total_matched = sum(len(data['elements']) for data in elements_by_material.values())
                all_elements = self.ifc_file.by_type("IfcElement")
                print(f"Total elements matched to materials: {total_matched}/{len(all_elements)}")
                            
            except Exception as e:
                print(f"Error getting elements data: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("No IFC file provided for elements data")
        
        return elements_by_material
    
    def _get_element_volume(self, element):
        """Get element volume from quantities or properties"""
        try:
            import ifcopenshell.util.element
            
            # Get all property and quantity sets
            psets = ifcopenshell.util.element.get_psets(element, qtos_only=False)
            
            # First try to find volume in quantity sets (qtos)
            volume_keys = ['GrossVolume', 'NetVolume', 'Volume', 'GrossFootprintArea', 'NetFootprintArea']
            height_keys = ['Height', 'OverallHeight', 'NominalHeight']
            
            found_volume = None
            found_area = None
            found_height = None
            
            for pset_name, pset_data in psets.items():
                # Look for direct volume
                for key in volume_keys:
                    if key in pset_data and not found_volume:
                        value = pset_data[key]
                        if isinstance(value, dict) and 'value' in value:
                            val = float(value['value'])
                            if val > 0 and 'area' not in key.lower():
                                found_volume = val
                            elif 'area' in key.lower():
                                found_area = val
                        elif isinstance(value, (int, float)) and value > 0:
                            if 'area' not in key.lower():
                                found_volume = float(value)
                            else:
                                found_area = float(value)
                
                # Look for height (for area-based calculations)
                for key in height_keys:
                    if key in pset_data and not found_height:
                        value = pset_data[key]
                        if isinstance(value, dict) and 'value' in value:
                            found_height = float(value['value'])
                        elif isinstance(value, (int, float)) and value > 0:
                            found_height = float(value)
            
            # Return direct volume if found
            if found_volume:
                return found_volume
            
            # Try to calculate from area and height
            if found_area and found_height:
                return found_area * found_height
            
            # Try geometry-based calculation as last resort
            try:
                import ifcopenshell.util.shape
                # This requires more setup but would be more accurate
                # For now, return 0 to avoid errors
                pass
            except:
                pass
                
        except Exception as e:
            print(f"Error getting volume for element {element.id()}: {e}")
            
        return 0.0

def start_server(results, detailed_results=None, ifc_file=None, port=0):
    """Start the web server with results data"""
    print(f"Starting server with IFC file: {ifc_file is not None}")
    if ifc_file:
        print(f"IFC file type: {type(ifc_file)}")
    
    # Create a custom handler class that includes the data
    class CustomHandler(ResultsHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, 
                           results=results, 
                           detailed_results=detailed_results,
                           ifc_file=ifc_file,
                           **kwargs)
    
    httpd = socketserver.TCPServer(('localhost', port), CustomHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd

def launch_results_browser(results, detailed_results=None, ifc_file=None):
    """Launch browser with results visualization"""
    print(f"Launching web interface...")
    print(f"Web directory: {WEB_DIR}")
    print(f"Results: {len(results) if results else 0} materials")
    print(f"Detailed results: {len(detailed_results) if detailed_results else 0} materials")
    
    server = start_server(results, detailed_results, ifc_file)
    port = server.server_address[1]
    url = f'http://localhost:{port}/index.html'
    
    print(f"Web interface running at: {url}")
    print(f"Alternative views:")
    print(f"  - http://localhost:{port}/index_simple.html (clean material-only view - RECOMMENDED)")
    print(f"  - http://localhost:{port}/simple.html (redirects to index_simple.html)")
    print(f"  - http://localhost:{port}/test.html (Chart.js test)")
    print(f"Data endpoints:")
    print(f"  - http://localhost:{port}/results (material analysis data)")
    
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
    
    return server
