"""Tests for Blender operators"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import tempfile
import os

# Since we're testing outside Blender, operators will use mocked base classes
from operators import (
    IFCLCA_OT_LoadIFC,
    IFCLCA_OT_UseActiveIFC,
    IFCLCA_OT_MapMaterial,
    IFCLCA_OT_RunAnalysis,
    IFCLCA_OT_ClearResults,
    IFCLCA_OT_AutoMapMaterials
)


class TestOperatorStructure:
    """Test that operators are properly structured"""
    
    def test_operators_exist(self):
        """Test that all expected operators are defined"""
        assert IFCLCA_OT_LoadIFC is not None
        assert IFCLCA_OT_UseActiveIFC is not None
        assert IFCLCA_OT_MapMaterial is not None
        assert IFCLCA_OT_RunAnalysis is not None
        assert IFCLCA_OT_ClearResults is not None
        assert IFCLCA_OT_AutoMapMaterials is not None
    
    def test_operators_have_bl_idname(self):
        """Test that operators have Blender ID names"""
        assert hasattr(IFCLCA_OT_LoadIFC, 'bl_idname')
        assert hasattr(IFCLCA_OT_UseActiveIFC, 'bl_idname')
        assert hasattr(IFCLCA_OT_MapMaterial, 'bl_idname')
        assert hasattr(IFCLCA_OT_RunAnalysis, 'bl_idname')
        assert hasattr(IFCLCA_OT_ClearResults, 'bl_idname')
        assert hasattr(IFCLCA_OT_AutoMapMaterials, 'bl_idname')
    
    def test_operators_have_execute(self):
        """Test that operators have execute method"""
        assert hasattr(IFCLCA_OT_LoadIFC, 'execute')
        assert hasattr(IFCLCA_OT_UseActiveIFC, 'execute')
        assert hasattr(IFCLCA_OT_MapMaterial, 'execute')
        assert hasattr(IFCLCA_OT_RunAnalysis, 'execute')
        assert hasattr(IFCLCA_OT_ClearResults, 'execute')
        assert hasattr(IFCLCA_OT_AutoMapMaterials, 'execute')


class TestClearResultsOperator:
    """Test the ClearResults operator which is simplest"""
    
    def test_clear_results(self):
        """Test clearing results"""
        op = IFCLCA_OT_ClearResults()
        
        # Mock context
        context = MagicMock()
        props = context.scene.ifclca_props
        props.results_text = "Some results"
        props.total_carbon = 1234.5
        props.show_results = True
        
        # Execute
        result = op.execute(context)
        
        # Check results
        assert result == {'FINISHED'}
        assert props.results_text == ""
        assert props.total_carbon == 0.0
        assert props.show_results == False


class TestRunAnalysisOperator:
    """Test the RunAnalysis operator"""
    
    def test_run_analysis_no_file(self):
        """Test running analysis without IFC file"""
        op = IFCLCA_OT_RunAnalysis()
        op.report = Mock()
        
        # Mock context
        context = MagicMock()
        props = context.scene.ifclca_props
        props.ifc_loaded = False
        
        # Execute
        result = op.execute(context)
        
        # Check results
        assert result == {'CANCELLED'}
        op.report.assert_called_with({'ERROR'}, "Please load an IFC file first")
    
    def test_run_analysis_no_mappings(self):
        """Test running analysis without material mappings"""
        # Set up global IFC file
        import operators
        operators._ifc_file = Mock()
        
        op = IFCLCA_OT_RunAnalysis()
        op.report = Mock()
        
        # Mock context
        context = MagicMock()
        props = context.scene.ifclca_props
        props.ifc_loaded = True
        props.material_mappings = []  # No mappings
        
        # Execute
        result = op.execute(context)
        
        # Check results
        assert result == {'CANCELLED'}
        op.report.assert_called_with({'ERROR'}, "Please map at least one material before running analysis")
        
        # Clean up
        operators._ifc_file = None 