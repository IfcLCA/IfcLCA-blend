"""
Setup file for IfcLCA-blend

This allows the addon to be installed as a package for testing
"""
from setuptools import setup, find_packages

setup(
    name="ifclca-blend",
    version="0.1.0",
    description="Life Cycle Assessment for IFC models - Blender Addon",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.9",
    install_requires=[
        # Note: Blender dependencies (bpy) are not included as they come with Blender
    ],
    extras_require={
        "test": [
            "pytest>=7.0",
            "pytest-cov",
            "pytest-mock",
            "mock",
        ],
    },
) 