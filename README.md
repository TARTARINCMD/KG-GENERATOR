# KG Generator

A browser-based knowledge graph editor built with Dash and Cytoscape.js — create, edit, query, and visualize node-relation graphs interactively, without writing any code.

This project was built as part of an HCI (Human-Computer Interaction) course, exploring interaction design for a genuinely useful data/research tool.

## Features

- **Interactive Graph Creation**: Add nodes and edges with custom labels and relationships
- **Multiple Layout Options**: Random, Grid, Circle, Breadthfirst (BFS), Force-directed (Cola), and Klay layouts
- **Node Editing**: Double-click nodes to edit labels, colors, and sizes
- **Edge Editing**: Click edges to modify labels
- **Node Hiding**: Hide/show nodes and their descendants
- **Safe Deletion**: Warns before deleting a node that would disconnect the graph
- **Pattern Queries**: Filter the graph with plain-text patterns like `neighbors of X`, `connected to X`, `shared by A and B`, and `via <relation>`
- **Community Detection**: Automatically detect and color-code clusters in the graph
- **Import Support**: Import graphs from RDF/OWL (`.rdf`, `.ttl`, `.xml`), JSON-LD, JSON, and CSV
- **Export Options**: Export to CSV (nodes/edges), PNG, JPEG, and JSON formats
- **Fullscreen Mode**: View the graph in fullscreen for better visualization

## Tech Stack

- **Python** — application logic
- **Dash** (Plotly) — web app framework and reactive callbacks
- **Dash Cytoscape** — interactive graph rendering and layout engine
- **RDFlib** — RDF/OWL/JSON-LD parsing and serialization
- **NetworkX** — graph algorithms (community detection, connectivity checks)
- **Pandas** — CSV import/export
- **HTML/CSS** — custom design system (RPTU brand palette)

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)

## Installation

1. Clone or download this repository
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python KG.py
```

Then open your browser to `http://localhost:8080`.

## Usage Guide

### Creating a Graph

1. **Add Nodes and Edges**: fill in "Source node", "Target node", and "Relation", then click **Insert**.
2. **Change Layout**: pick a layout from the "Layout" dropdown — Random, Grid, Circle, Breadthfirst, Force directed, or Klay.

### Editing Elements

- **Edit a node**: double-click it to open the edit panel — change its label, color, or size, hide it, or delete it.
- **Edit an edge**: click it to open the edge panel — change its label or delete it.
- If deleting a node would split the graph into disconnected pieces, a warning appears before the deletion is applied.

### Querying the Graph

Use the query box in the sidebar (hover the info icon for the full list of patterns):

| Pattern | Result |
|---|---|
| `neighbors of X` | direct neighbors of X |
| `connected to X` | all elements directly linked to X |
| `shared by A and B` | nodes connected to both A and B |
| `via <relation>` | all edges with that relation label |
| `all` / `reset` | show everything again |

### Import / Export

- **Import**: drag and drop, or choose a file with extension `.xml`, `.rdf`, `.ttl`, `.jsonld`, `.json`, or `.csv`.
- **Export**: Nodes CSV, Edges CSV, PNG, JPEG, or full graph JSON.

### Other Features

- **Detect Communities**: automatically clusters and color-codes the graph.
- **Fullscreen**: click the expand icon in the top-right of the canvas; press `Esc` to exit.
- **Delete All**: clears the graph after a confirmation prompt.
