# IfcLCA-blend

<div align="center">
  <img src="https://github.com/IfcLCA/IfcLCA-blend/raw/main/assets/logo.png" alt="IfcLCA Logo" width="120"/>
  
  <h3>Life Cycle Assessment for IFC building models in Blender</h3>
  
  [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
  [![Blender](https://img.shields.io/badge/Blender-4.2%2B-orange)](https://www.blender.org/)
  [![Extension](https://img.shields.io/badge/Extension-Compatible-green)](https://extensions.blender.org/)
  
</div>

---

**IfcLCA-blend** is a professional Blender extension that brings **Life Cycle Assessment (LCA)** capabilities directly into your BIM workflow. Seamlessly analyze the environmental impact of IFC building models with real-time carbon footprint calculations and comprehensive material database integration.

> 🌱 **Sustainable Design Made Simple** - Transform your architectural workflow with integrated environmental analysis

## Features

<img src="https://github.com/IfcLCA/IfcLCA-blend/raw/main/assets/UI.png" alt="IfcLCA Blender Interface" width="100%" style="border-radius: 8px; margin: 20px 0;"/>

- 🏗️ **IFC Model Integration**: Load IFC models and analyze building elements seamlessly
- 🌍 **Environmental Databases**: Access KBOB (Swiss) and ÖKOBAUDAT (German) material databases
- 🔗 **API Integration**: Direct API access to Ökobaudat database (EN 15804+A2 compliant)
- 📊 **Carbon Footprint Analysis**: Calculate embodied carbon and environmental indicators
- 🎯 **Smart Material Mapping**: Auto-mapping and manual assignment capabilities
- 📈 **Interactive Visualization**: Web-based dashboard for results analysis
- 📤 **Export Capabilities**: Export results for further analysis and reporting

## 🚀 Installation

### For Blender 5.0+ (Extension System)
```bash
# Method 1: Via Blender Extensions Platform
1. Open Blender → Edit → Preferences → Get Extensions
2. Search for "IfcLCA Integration"
3. Click Install

# Method 2: Install from Disk
1. Download the extension .zip file
2. Blender → Edit → Preferences → Get Extensions
3. Click dropdown → Install from Disk
4. Select the .zip file
```

### For Blender 4.x (Legacy Add-ons)
```bash
1. Install BlenderBIM addon first
2. Download IfcLCA-blend.zip
3. Blender → Edit → Preferences → Add-ons → Install
4. Select the zip file and enable
```

### Prerequisites
- **Blender 4.2.0+** (Blender 5.0+ recommended)
- **BlenderBIM** addon for full IFC support
- **Internet connection** for ÖKOBAUDAT API (optional)


## ⚡ Quick Start

<table>
<tr>
<td width="50%">

### 1️⃣ **Load Your Model**
- Import IFC file via BlenderBIM
- Or use active BIM model

### 2️⃣ **Configure Database**
- Choose KBOB (Swiss) or ÖKOBAUDAT (German)
- Set API key if needed

### 3️⃣ **Map Materials**
- Use auto-mapping for common materials
- Manual assignment via database browser

</td>
<td width="50%">

### 4️⃣ **Run Analysis**
- Click "Calculate Embodied Carbon"
- Review material mappings

### 5️⃣ **Visualize Results**
- View in interactive web dashboard
- Export to CSV for reports

### 6️⃣ **Optimize Design**
- Compare material alternatives
- Reduce environmental impact

</td>
</tr>
</table>

### Interactive Results Dashboard

<img src="https://github.com/IfcLCA/IfcLCA-blend/raw/main/assets/Web.png" alt="IfcLCA Web Dashboard" width="100%" style="border-radius: 8px; margin: 20px 0;"/>

The web-based dashboard provides comprehensive visualization of your LCA results with:
- **Total Carbon Impact**: Overall embodied carbon footprint
- **Material Breakdown**: Detailed analysis by material type
- **Interactive Charts**: Pie charts and bar graphs for easy interpretation
- **Multiple Views**: Analyze by material, class, or individual elements

## 🌍 Environmental Databases

<table>
<tr>
<td width="50%">

### 🇨🇭 **KBOB (Swiss)**
- **314+ materials** ready to use
- **Indicators**: GWP, PENRE, UBP
- **Source**: Pre-loaded database
- **Standards**: Swiss building standards
- **Usage**: Plug-and-play

</td>
<td width="50%">

### 🇩🇪 **ÖKOBAUDAT (German)**
- **1000+ EPDs** via API
- **Standards**: EN 15804+A2 compliant
- **Real-time**: Live database access
- **Optional**: API key for full access
- **Auto-bundled**: No setup required

</td>
</tr>
</table>

> 📋 **Custom Databases**: Import your own material data in JSON format - see documentation for details

## 📚 Examples & Documentation

<details>
<summary><strong>🔍 Explore Database Examples</strong></summary>

```python
# Browse KBOB materials
python examples/explore_kbob_database.py

# Test ÖKOBAUDAT API
python examples/okobaudat_api_example.py
```
</details>

<details>
<summary><strong>🧪 Running Tests</strong></summary>

```bash
cd IfcLCA-blend
python -m pytest tests/ -v
```
</details>



## 🤝 Contributing

We welcome contributions! Here's how you can help:

- 🐛 **Report bugs** via [GitHub Issues](https://github.com/louistrue/IfcLCA-blend/issues)
- 💡 **Suggest features** or improvements
- 🔧 **Submit pull requests** with fixes or enhancements
- 📖 **Improve documentation** and examples


## 📄 License

Licensed under **GNU General Public License v3.0** - see [LICENSE](LICENSE) file for details.

<div align="center">
  
**Made with ❤️ by LT+ for sustainable construction**

</div> 