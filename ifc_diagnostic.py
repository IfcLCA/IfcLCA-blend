"""
IFC Diagnostic Script for Blender
Run this in Blender's Python console to diagnose IFC file issues.

Usage in Blender console:
import sys
sys.path.append(r'C:\path\to\your\IfcLCA-blend')
from ifc_diagnostic import diagnose_ifc_file
diagnose_ifc_file(r'C:\path\to\your\file.ifc')
"""

import logging
import sys

try:
    import ifcopenshell
    import ifcopenshell.util.element
    HAS_IFC = True
except ImportError:
    HAS_IFC = False

def setup_diagnostic_logger():
    """Set up logger for diagnostic output"""
    logger = logging.getLogger('IFC_Diagnostic')
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('[IFC_DIAG] %(levelname)s: %(message)s')
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger

logger = setup_diagnostic_logger()

def diagnose_ifc_file(file_path):
    """
    Comprehensive diagnostic of an IFC file
    
    Args:
        file_path (str): Path to the IFC file
    """
    if not HAS_IFC:
        logger.error("ifcopenshell not available. Install with: pip install ifcopenshell")
        return False
    
    try:
        logger.info(f"=== DIAGNOSING IFC FILE: {file_path} ===")
        
        # Load the file
        logger.info("Loading IFC file...")
        ifc_file = ifcopenshell.open(file_path)
        logger.info(f"✓ File loaded successfully")
        
        # Basic file info
        logger.info(f"Schema: {ifc_file.schema}")
        logger.info(f"Total objects: {len(ifc_file)}")
        
        # Check project structure
        logger.info("\n--- PROJECT STRUCTURE ---")
        projects = ifc_file.by_type("IfcProject")
        logger.info(f"Projects: {len(projects)}")
        for project in projects:
            logger.info(f"  - {project.Name if hasattr(project, 'Name') else 'Unnamed'}")
        
        sites = ifc_file.by_type("IfcSite")
        logger.info(f"Sites: {len(sites)}")
        for site in sites:
            logger.info(f"  - {site.Name if hasattr(site, 'Name') else 'Unnamed'}")
        
        buildings = ifc_file.by_type("IfcBuilding")
        logger.info(f"Buildings: {len(buildings)}")
        for building in buildings:
            logger.info(f"  - {building.Name if hasattr(building, 'Name') else 'Unnamed'}")
        
        storeys = ifc_file.by_type("IfcBuildingStorey")
        logger.info(f"Storeys: {len(storeys)}")
        for storey in storeys:
            logger.info(f"  - {storey.Name if hasattr(storey, 'Name') else 'Unnamed'}")
        
        # Check elements
        logger.info("\n--- ELEMENTS ---")
        elements = ifc_file.by_type("IfcElement")
        logger.info(f"Total elements: {len(elements)}")
        
        # Count by type
        element_types = {}
        for element in elements:
            elem_type = element.is_a()
            element_types[elem_type] = element_types.get(elem_type, 0) + 1
        
        logger.info("Element types:")
        for elem_type, count in sorted(element_types.items()):
            logger.info(f"  - {elem_type}: {count}")
        
        # Check geometric representations
        logger.info("\n--- GEOMETRY ---")
        representations = ifc_file.by_type("IfcShapeRepresentation")
        logger.info(f"Shape representations: {len(representations)}")
        
        product_representations = ifc_file.by_type("IfcProductDefinitionShape")
        logger.info(f"Product definition shapes: {len(product_representations)}")
        
        # Check for elements with geometry
        elements_with_geometry = 0
        elements_without_geometry = 0
        
        for element in elements[:min(100, len(elements))]:  # Check first 100 elements
            if hasattr(element, 'Representation') and element.Representation:
                elements_with_geometry += 1
            else:
                elements_without_geometry += 1
        
        sample_size = min(100, len(elements))
        logger.info(f"Geometry check (sample of {sample_size} elements):")
        logger.info(f"  - With geometry: {elements_with_geometry}")
        logger.info(f"  - Without geometry: {elements_without_geometry}")
        
        # Check materials
        logger.info("\n--- MATERIALS ---")
        materials = ifc_file.by_type("IfcMaterial")
        logger.info(f"Materials: {len(materials)}")
        
        material_sets = ifc_file.by_type("IfcMaterialLayerSet")
        logger.info(f"Material layer sets: {len(material_sets)}")
        
        material_lists = ifc_file.by_type("IfcMaterialList")
        logger.info(f"Material lists: {len(material_lists)}")
        
        # Sample materials
        if materials:
            logger.info("Sample materials:")
            for material in materials[:5]:  # Show first 5
                logger.info(f"  - {material.Name if hasattr(material, 'Name') else 'Unnamed'}")
        
        # Check relationships
        logger.info("\n--- RELATIONSHIPS ---")
        spatial_rels = ifc_file.by_type("IfcRelContainedInSpatialStructure")
        logger.info(f"Spatial containment relationships: {len(spatial_rels)}")
        
        aggregation_rels = ifc_file.by_type("IfcRelAggregates")
        logger.info(f"Aggregation relationships: {len(aggregation_rels)}")
        
        # Diagnose common issues
        logger.info("\n--- DIAGNOSTICS ---")
        issues = []
        
        if len(projects) == 0:
            issues.append("❌ No IfcProject found - file may be invalid")
        else:
            logger.info("✓ IfcProject found")
        
        if len(elements) == 0:
            issues.append("❌ No IfcElements found - file appears empty")
        else:
            logger.info(f"✓ {len(elements)} elements found")
        
        if len(representations) == 0:
            issues.append("⚠️  No geometric representations found - elements may not be visible")
        else:
            logger.info(f"✓ {len(representations)} geometric representations found")
        
        if len(spatial_rels) == 0:
            issues.append("⚠️  No spatial relationships found - elements may not be in spatial tree")
        else:
            logger.info(f"✓ {len(spatial_rels)} spatial relationships found")
        
        if elements_without_geometry > elements_with_geometry and sample_size > 10:
            issues.append("⚠️  Many elements lack geometry - visibility issues likely")
        
        # Report issues
        if issues:
            logger.warning("\n--- ISSUES FOUND ---")
            for issue in issues:
                logger.warning(issue)
        else:
            logger.info("\n✓ No major issues detected")
        
        logger.info("\n=== DIAGNOSIS COMPLETE ===")
        return True
        
    except Exception as e:
        logger.error(f"Failed to diagnose IFC file: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def diagnose_active_ifc():
    """Diagnose the currently active IFC in Bonsai"""
    try:
        import bpy
        from bonsai.bim import tool
        
        ifc = tool.Ifc.get()
        if not ifc:
            logger.error("No active IFC file in Bonsai")
            return False
        
        logger.info("Diagnosing active IFC from Bonsai...")
        
        # Run diagnosis on active file
        diagnose_ifc_object(ifc)
        return True
        
    except ImportError:
        logger.error("Bonsai not available or not in Blender environment")
        return False
    except Exception as e:
        logger.error(f"Failed to diagnose active IFC: {str(e)}")
        return False

def diagnose_ifc_object(ifc_file):
    """Diagnose an already loaded IFC file object"""
    try:
        logger.info("=== DIAGNOSING LOADED IFC ===")
        
        # Basic file info
        logger.info(f"Schema: {ifc_file.schema}")
        logger.info(f"Total objects: {len(ifc_file)}")
        
        # Check key elements
        projects = ifc_file.by_type("IfcProject")
        elements = ifc_file.by_type("IfcElement")
        representations = ifc_file.by_type("IfcShapeRepresentation")
        materials = ifc_file.by_type("IfcMaterial")
        
        logger.info(f"Projects: {len(projects)}")
        logger.info(f"Elements: {len(elements)}")
        logger.info(f"Representations: {len(representations)}")
        logger.info(f"Materials: {len(materials)}")
        
        # Quick diagnosis
        if len(elements) == 0:
            logger.warning("❌ No elements found - file appears empty")
        elif len(representations) == 0:
            logger.warning("⚠️  No geometry found - elements may not be visible")
        else:
            logger.info("✓ File appears to have content and geometry")
        
        logger.info("=== DIAGNOSIS COMPLETE ===")
        return True
        
    except Exception as e:
        logger.error(f"Failed to diagnose IFC object: {str(e)}")
        return False

# Convenience functions for Blender console
def diag(file_path):
    """Short alias for diagnose_ifc_file"""
    return diagnose_ifc_file(file_path)

def diag_active():
    """Short alias for diagnose_active_ifc"""
    return diagnose_active_ifc()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        diagnose_ifc_file(sys.argv[1])
    else:
        print("Usage: python ifc_diagnostic.py <path_to_ifc_file>") 