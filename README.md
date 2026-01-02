# Knowledge Graph Visualization Tool :DD

A web-based application for creating, editing, and visualizing knowledge graphs using Dash and Cytoscape.js.

## Features

- **Interactive Graph Creation**: Add nodes and edges with custom labels and relationships
- **Multiple Layout Options**: Random, Grid, Circle, Breadthfirst (BFS), Force directed, and Klay layouts
- **Node Editing**: Double-click nodes to edit labels, colors, and sizes
- **Edge Editing**: Click edges to modify labels
- **Import Support**: Import graphs from RDF (TTL, XML, JSON-LD) and JSON files
- **Export Options**: Export to CSV (nodes/edges), PNG, JPEG, and JSON formats
- **Community Detection**: Automatically detect and color-code communities in the graph
- **Node Hiding**: Hide/show nodes and their descendants
- **Fullscreen Mode**: View graphs in fullscreen for better visualization

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. **Download and extract the project files**
   - Download the ZIP file
   - Extract it to a folder on your computer

2. **Install required packages**
   ```bash
   pip install dash dash-cytoscape pandas rdflib networkx
   ```

   Or install from requirements file:
   ```bash
   pip install -r requirements.txt
   ```


## Running the Application

1. **Navigate to the project directory**
   ```bash
   cd KG  # or whatever folder contains KG.py
   ```

2. **Run the application**
   ```bash
   python KG.py
   ```

3. **Access the application**
   - Open your web browser
   - Navigate to: `http://localhost:8080`
   - The application should load and display the knowledge graph interface

## Usage Guide

### Creating a Graph

1. **Add Nodes and Edges**:
   - Enter source node name in "Source Node Name" field
   - Enter target node name in "Target Node Name" field
   - Enter relationship in "Relation" field
   - Click "Insert" button

2. **Change Layout**:
   - Select desired layout from the "Layout" dropdown
   - Options include: Random, Grid, Circle, Breadthfirst (BFS), Force directed, Klay

### Editing Elements

1. **Edit Nodes**:
   - Double-click on any node to open the edit window
   - Modify label, color, or size
   - Use "Hide Node" to hide the node and its descendants
   - Use "Delete Node" to remove the node completely

2. **Edit Edges**:
   - Click on any edge to open the edge edit window
   - Modify the edge label
   - Use "Delete Edge" to remove the edge

### Import/Export

1. **Import Graphs**:
   - Click "Choose RDF/JSON/XML file or drag & drop"
   - Select files with extensions: .ttl, .rdf, .xml, .jsonld, .json
   - The graph will automatically load

2. **Export Data**:
   - **Nodes CSV**: Export all nodes to CSV format
   - **Edges CSV**: Export all edges to CSV format
   - **PNG Image**: Export graph as PNG image
   - **JPEG Image**: Export graph as JPEG image
   - **JSON Export**: Export complete graph as JSON

### Advanced Features

1. **Community Detection**:
   - Click "Detect Communities" button
   - Nodes will be automatically colored based on detected communities

2. **Fullscreen Mode**:
   - Click the fullscreen button (⛶) in the top-right corner
   - Press ESC to exit fullscreen

3. **Delete All**:
   - Click "Delete All" to remove all nodes and edges
   - Confirm deletion in the popup dialog
