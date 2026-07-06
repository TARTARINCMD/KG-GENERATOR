import dash
from dash import dcc, html, Input, Output, State, callback_context, no_update, ALL, MATCH
import dash_cytoscape as cyto
import json
import pandas as pd
import base64
import io
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, OWL, SKOS
import re
import sqlite3
import networkx as nx
from networkx.algorithms import community

cyto.load_extra_layouts()

app = dash.Dash(__name__)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Red+Hat+Text:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


app.layout = html.Div([
    html.Div([
        # Left Panel
        html.Div([
            # Brand
            html.Div([
                html.I(className='fa fa-project-diagram brand-icon'),
                html.Span('KG Generator', className='brand-title')
            ], className='brand'),

            # Nodes and Relations
            html.Div([
                html.H4('Nodes and Relations', className='section-title'),
                html.Div([
                    dcc.Input(id='node1-input', type='text', placeholder='Source node', className='text-input'),
                    dcc.Input(id='node2-input', type='text', placeholder='Target node', className='text-input')
                ], className='input-row'),
                dcc.Input(id='relationship-input', type='text', placeholder='Relation', className='text-input'),
                html.Button([
                    html.I(className='fa fa-plus'),
                    'Insert'
                ], id='add-button', className='btn btn-muted')
            ], className='sidebar-section'),

            html.Div(id='insert-error-modal', className='alert-modal', style={'display': 'none'}, children=[
                html.Div([
                    html.H4('Missing Required Fields', className='alert-title'),
                    html.P(id='insert-error-text', className='alert-text')
                ])
            ]),

            # Hidden interval for auto-hiding modal
            dcc.Interval(
                id='modal-timer',
                interval=3000,  # 3 seconds
                n_intervals=0,
                disabled=True
            ),

            # Layout
            html.Div([
                html.Label('Layout', className='section-title'),
                dcc.Dropdown(
                    id='layout-dropdown',
                    options=[
                        {'label': 'Random', 'value': 'random'},
                        {'label': 'Grid', 'value': 'grid'},
                        {'label': 'Circle', 'value': 'circle'},
                        {'label': 'Breadthfirst (BFS)', 'value': 'breadthfirst'},
                        {'label': 'Force directed', 'value': 'cola'},
                        {'label': 'Klay', 'value': 'klay'}
                    ],
                    value='random',
                    clearable=False
                )
            ], className='sidebar-section'),

            # Actions
            html.Div([
                html.Button([
                    html.I(className='fa fa-sitemap'),
                    'Detect Communities'
                ], id='cluster-button', className='btn btn-primary'),
                html.Button([
                    html.I(className='fa fa-trash'),
                    'Delete All'
                ], id='delete-all-button', className='btn btn-danger-ghost')
            ], className='sidebar-section'),

            # Query
            html.Div([
                html.Div([
                    html.Label('Query', className='section-title'),
                    html.Div([
                        html.I(className='fa fa-circle-info query-help-icon'),
                        html.Div([
                            html.P('Supported query patterns:', className='query-help-title'),
                            html.Ul([
                                html.Li([html.Code('connected to <entity>'), ' — all direct links']),
                                html.Li([html.Code('neighbors of <entity>'), ' — direct neighbors only']),
                                html.Li([html.Code('shared by <a> and <b>'), ' — common connections']),
                                html.Li([html.Code('via <relation>'), ' — filter by edge label']),
                                html.Li([html.Code('all'), ' / ', html.Code('reset'), ' — show everything'])
                            ], className='query-help-list')
                        ], className='query-help-tooltip')
                    ], className='query-help')
                ], className='section-title-row'),
                html.Div([
                    dcc.Input(id='query-input', type='text', placeholder='e.g. neighbors of X', className='text-input'),
                    html.Button(html.I(className='fa fa-search'), id='query-button', className='btn btn-icon btn-primary'),
                    html.Button(html.I(className='fa fa-rotate-right'), id='reset-query-button', className='btn btn-icon btn-ghost')
                ], className='query-row'),
                html.Div(id='query-results', className='query-results', style={'display': 'none'})
            ], className='sidebar-section'),

            # Import and Export at bottom
            html.Div([
                dcc.Upload(
                    id='import-graph',
                    children=html.Div([
                        html.I(className='fa fa-folder-open'),
                        'Import RDF/JSON/XML/CSV'
                    ], className='upload-area'),
                    multiple=False,
                    accept='.xml,.rdf,.ttl,.jsonld,.json,.csv'
                ),
                html.Button([
                    html.I(className='fa fa-download'),
                    'Export'
                ], id='export-toggle', className='btn btn-ghost')
            ], className='sidebar-section sidebar-bottom'),

            # Delete All Confirmation
            html.Div([
                html.Div([
                    html.H4('Confirm Delete', className='modal-title'),
                    html.P('Are you sure you want to delete all nodes and edges?', className='modal-text'),
                    html.Div([
                        html.Button('Cancel', id='cancel-delete', className='btn btn-light'),
                        html.Button('Delete All', id='confirm-delete', className='btn btn-danger')
                    ], className='modal-actions')
                ], className='modal-card')
            ], id='delete-confirmation-modal', className='modal-backdrop', style={'display': 'none'}),

            dcc.Download(id='download-nodes-csv'),
            dcc.Download(id='download-edges-csv'),
            dcc.Download(id='download-json'),

            dcc.Store(id='fullscreen-store', data=False),
            dcc.Store(id='layout-store', data='random'),
            dcc.Store(id='shift-key-store', data=False),
            dcc.Store(id='click-timing-store', data={'last_click': None, 'click_count': 0})
        ], className='sidebar'),

        # Export Modal
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.H3('Export Options', className='modal-title'),
                        html.Button('×', id='close-export-modal', className='popover-close')
                    ], className='modal-header'),

                    html.Div([
                        html.Button([
                            html.I(className='fa fa-file-csv', style={'color': '#26d07c'}),
                            'Nodes CSV'
                        ], id='export-nodes-csv', className='btn-row'),

                        html.Button([
                            html.I(className='fa fa-file-csv', style={'color': '#ffa252'}),
                            'Edges CSV'
                        ], id='export-edges-csv', className='btn-row'),

                        html.Button([
                            html.I(className='fa fa-file-image', style={'color': '#6ab2e7'}),
                            'PNG Image'
                        ], id='export-png', className='btn-row'),

                        html.Button([
                            html.I(className='fa fa-file-image', style={'color': '#e31b4c'}),
                            'JPEG Image'
                        ], id='export-jpeg', className='btn-row'),

                        html.Button([
                            html.I(className='fa fa-file-code', style={'color': '#4c3575'}),
                            'JSON Export'
                        ], id='export-json', className='btn-row')
                    ], className='export-options')
                ], className='modal-card')
            ], className='modal-backdrop')
        ], id='export-modal', style={'display': 'none'}),

        # Right Panel
        html.Div([
            # Fullscreen button
            html.Button(
                html.I(className='fa fa-expand'),
                id='fullscreen-btn',
                className='canvas-fab'
            ),

            # Graph container
            html.Div([
                cyto.Cytoscape(
                    id='cytoscape-graph',
                    layout={'name': 'random', 'fit': True, 'animate': True, 'padding': 30},
                    style={
                        'width': '100%',
                        'height': '100%',
                        'background': '#fff',
                        'minHeight': '500px'
                    },
                    elements=[],
                    zoom=1.0,
                    generateImage={'type': 'png', 'action': 'store'},
                    # Multi selection
                    boxSelectionEnabled=True,

                    stylesheet=[
                        {
                            'selector': 'node',
                            'style': {
                                'label': 'data(label)',
                                'font-size': 18,
                                'text-valign': 'center',
                                'text-halign': 'center',
                                'background-color': 'data(color)',
                                'color': '#000',
                                'width': 'data(size)',
                                'height': 'data(size)',
                            }
                        },
                        {
                            'selector': 'node:selected',
                            'style': {
                                'background-color': 'data(color)',
                                'border-width': 4,
                                'border-color': '#042c58',
                                'border-opacity': 0.9,
                                'width': 'data(size)',
                                'height': 'data(size)'
                            }
                        },
                        {
                            'selector': 'edge',
                            'style': {
                                'label': 'data(label)',
                                'font-size': 18,
                                'text-background-color': '#fff',
                                'text-background-opacity': 1,
                                'text-background-padding': '4px',
                                'target-arrow-shape': 'triangle',
                                'target-arrow-color': '#000',
                                'line-color': '#000',
                                'width': 2,
                                'curve-style': 'bezier',
                            }
                        },
                        {
                            'selector': 'node[hidden = "true"]',
                            'style': {
                                'background-color': '#d3d3d3',
                                'color': '#666666',
                                'opacity': 0.4,
                                'border-color': '#999999',
                                'border-width': 1,
                                'text-outline-color': '#666666',
                                'text-outline-width': 1
                            }
                        },
                        {
                            'selector': 'edge[hidden = "true"]',
                            'style': {
                                'line-color': '#d3d3d3',
                                'target-arrow-color': '#d3d3d3',
                                'opacity': 0.3,
                                'width': 1
                            }
                        },
                        {
                            'selector': 'node[hidden = "false"]',
                            'style': {
                                'background-color': 'data(color)',
                                'color': '#000000',
                                'opacity': 1,
                                'border-color': '#000000',
                                'border-width': 0,
                                'text-outline-color': '#000000',
                                'text-outline-width': 0
                            }
                        },
                        {
                            'selector': 'edge[hidden = "false"]',
                            'style': {
                                'line-color': 'data(line-color)',
                                'target-arrow-color': 'data(target-arrow-color)',
                                'opacity': 1,
                                'width': 2
                            }
                        }
                    ]
                ),

                # Node edit window
                html.Div([
                    # click-outside-to-close
                    html.Div(id='node-edit-backdrop', className='edit-backdrop', style={'display': 'none'}),
                    html.Div([
                        html.Div([
                            html.H3('Edit Node', className='popover-title'),
                            html.Button('×', id='close-node-window', className='popover-close')
                        ], className='popover-header'),
                        html.Div([
                            html.Label('Label:', className='field-label'),
                            dcc.Input(
                                id='node-label-input',
                                type='text',
                                placeholder='Enter node label',
                                debounce=True,
                                className='light-input'
                            ),
                            html.Label('Color:', className='field-label'),
                            dcc.Dropdown(
                                id='node-color-dropdown',
                                options=[
                                    {'label': 'Light Blue', 'value': '#87cefa'},
                                    {'label': 'Red', 'value': '#ff6b6b'},
                                    {'label': 'Green', 'value': '#51cf66'},
                                    {'label': 'Yellow', 'value': '#ffd43b'},
                                    {'label': 'Purple', 'value': '#cc5de8'},
                                    {'label': 'Orange', 'value': '#ff922b'},
                                    {'label': 'Pink', 'value': '#f06595'},
                                    {'label': 'Gray', 'value': '#868e96'}
                                ],
                                value='#87cefa',
                                clearable=False,
                                style={'marginBottom': '14px'}
                            ),
                            html.Label('Size:', className='field-label'),
                            dcc.Slider(
                                id='node-size-slider',
                                min=20,
                                max=100,
                                step=5,
                                value=30,
                                marks={20: '20', 30: '30', 50: '50', 70: '70', 100: '100'},
                                tooltip={'placement': 'bottom', 'always_visible': True},
                                updatemode='drag',
                                included=True,
                                className='size-slider'
                            ),

                            # Buttons container at bottom
                            html.Div([
                                html.Button('Hide Node', id='hide-node-button', n_clicks=0, className='btn btn-light'),
                                html.Button('Delete Node', id='delete-node-button', n_clicks=0, className='btn btn-danger')
                            ], className='buttons-container')
                        ])
                    ], className='popover-card')
                ], id='node-edit-window', className='popover-wrap', style={'display': 'none'}),

                # Edge edit window
                html.Div([
                    # click-outside-to-close
                    html.Div(id='edge-edit-backdrop', className='edit-backdrop', style={'display': 'none'}),
                    html.Div([
                        html.Div([
                            html.H3('Edit Edge', className='popover-title'),
                            html.Button('×', id='close-edge-window', className='popover-close')
                        ], className='popover-header'),
                        html.Div([
                            html.Label('Label:', className='field-label'),
                            dcc.Input(
                                id='edge-label-input',
                                type='text',
                                placeholder='Enter edge label',
                                debounce=True,
                                className='light-input'
                            ),
                            html.Button('Delete Edge', id='delete-edge-button', n_clicks=0, className='btn btn-danger')
                        ])
                    ], className='popover-card')
                ], id='edge-edit-window', className='popover-wrap', style={'display': 'none'})
            ], id='graph-container')
        ], className='canvas-panel')
    ], className='app-shell')
], className='app-root')

# Validate input fields for Insert button styling
@app.callback(
    Output('add-button', 'className'),
    [Input('node1-input', 'value'),
     Input('node2-input', 'value'),
     Input('relationship-input', 'value')]
)
def validate_insert_inputs(node1, node2, relationship):
    if node1 and node2 and relationship:
        return 'btn btn-success'
    return 'btn btn-muted'

# Handle error modal for insert button
@app.callback(
    Output('insert-error-modal', 'style'),
    Output('insert-error-text', 'children'),
    Output('modal-timer', 'disabled'),
    [Input('add-button', 'n_clicks')],
    [State('node1-input', 'value'),
     State('node2-input', 'value'),
     State('relationship-input', 'value')],
    prevent_initial_call=True
)
def handle_insert_error(add_clicks, node1, node2, relationship):
    if not add_clicks:
        return {'display': 'none', 'opacity': '0'}, "", True
    
    # Check if all fields are filled
    all_filled = node1 and node2 and relationship
    if all_filled:
        return {'display': 'none', 'opacity': '0'}, "", True
    
    # Generic error message for any missing fields
    error_msg = "Please fill out all required fields"
    
    return {'display': 'block', 'opacity': '1', 'pointerEvents': 'auto'}, error_msg, False

# Auto-hide modal when timer fires
@app.callback(
    Output('insert-error-modal', 'style', allow_duplicate=True),
    Output('modal-timer', 'disabled', allow_duplicate=True),
    Input('modal-timer', 'n_intervals'),
    prevent_initial_call=True
)
def auto_hide_modal(n_intervals):
    if n_intervals > 0:
        return {'display': 'block', 'opacity': '0', 'pointerEvents': 'none'}, True
    return dash.no_update, dash.no_update

# Insert, Delete All, Import, Auto-update node/edge 
@app.callback(
    Output('cytoscape-graph', 'elements'),
    [Input('add-button', 'n_clicks'),
     Input('delete-node-button', 'n_clicks'),
     Input('delete-edge-button', 'n_clicks'),
     Input('hide-node-button', 'n_clicks'),
     Input('node-color-dropdown', 'value'),
     Input('node-label-input', 'value'),
     Input('node-size-slider', 'value'),
     Input('edge-label-input', 'value')],
    [State('node1-input', 'value'),
     State('node2-input', 'value'),
     State('relationship-input', 'value'),
     State('cytoscape-graph', 'elements'),
     State('cytoscape-graph', 'tapNode'),
     State('cytoscape-graph', 'tapEdge')],
    prevent_initial_call=True
)
def update_graph(add_clicks, delete_node_clicks, delete_edge_clicks, hide_clicks, new_color, new_label, new_size, new_edge_label,
                 node1, node2, relationship, elements, selected_node, selected_edge):
    ctx = dash.callback_context
    if not ctx.triggered:
        return elements or []
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    
    if button_id == 'delete-node-button':

        # Delete the selected node and all its connected edges
        if not selected_node or not elements:
            return elements or []
        
        node_id = selected_node.get('data', {}).get('id')
        if not node_id:
            return elements or []
        
        # Remove the node and all edges connected to it
        new_elements = []
        for element in elements:
            if element['data'].get('id') != node_id:  
                if 'source' in element['data']:  
                    if element['data']['source'] != node_id and element['data']['target'] != node_id:
                        new_elements.append(element)
                else:  
                    node_element = element.copy()
                    if 'position' in element:
                        node_element['position'] = element['position']
                    new_elements.append(node_element)
        
        return new_elements
    elif button_id == 'delete-edge-button':
        if not selected_edge or not elements:
            return elements or []
        
        edge_id = selected_edge.get('data', {}).get('id')
        if not edge_id:
            return elements or []
        
        new_elements = []
        for element in elements:
            if element['data'].get('id') != edge_id:
                new_elements.append(element)
        
        return new_elements
    elif button_id == 'add-button':
        # Check if all fields are filled before proceeding
        if not add_clicks or not node1 or not node2 or not relationship:
            return elements or []
        
        node_ids = set([el['data']['id'] for el in elements if el['data'].get('id')]) if elements else set()
        new_elements = elements.copy() if elements else []
        if node1 not in node_ids:
            new_elements.append({'data': {'id': node1, 'label': node1, 'color': '#87cefa', 'size': 30}})
        if node2 not in node_ids:
            new_elements.append({'data': {'id': node2, 'label': node2, 'color': '#87cefa', 'size': 30}})
        # Create the edge with a unique ID
        edge_id = f"{node1}-{node2}"
        new_elements.append({'data': {'id': edge_id, 'source': node1, 'target': node2, 'label': relationship}})
        return new_elements



    elif button_id == 'node-color-dropdown' or button_id == 'node-label-input' or button_id == 'node-size-slider':
        if not selected_node or not elements:
            return elements or []
        
        new_elements = elements.copy()
        old_id = selected_node.get('data', {}).get('id')
        
        for element in new_elements:
            if element['data'].get('id') == old_id:
                if new_color:
                    element['data']['color'] = new_color
                if new_label:
                    element['data']['label'] = new_label
                if new_size and new_size != element['data'].get('size', 30):
                    element['data']['size'] = new_size
                break
        
        return new_elements
    elif button_id == 'edge-label-input':
        if not selected_edge or not elements:
            return elements or []
        
        new_elements = elements.copy()
        for element in new_elements:
            if (element['data'].get('source') == selected_edge.get('data', {}).get('source') and 
                element['data'].get('target') == selected_edge.get('data', {}).get('target')):
                if new_edge_label:
                    element['data']['label'] = new_edge_label
                break
        
        return new_elements
    elif button_id == 'hide-node-button':
        print("DEBUG: Hide button clicked!")
        if not selected_node or not elements:
            print("DEBUG: No selected node or elements for hide")
            return elements or []
        
        node_id = selected_node.get('data', {}).get('id')
        if not node_id:
            print("DEBUG: No node_id found for hide")
            return elements or []
        
        print(f"DEBUG: Processing hide for node {node_id}")
        
        is_currently_hidden = False
        for element in elements:
            if element['data'].get('id') == node_id:
                is_currently_hidden = element['data'].get('hidden') == 'true'
                break
        
        print(f"DEBUG: Node {node_id} is currently hidden: {is_currently_hidden}")
        
        if is_currently_hidden:
            # Unhide the node and all its descendants
            print("DEBUG: Unhiding node and descendants")
            new_elements = []
            for element in elements:
                element_copy = element.copy()
                
                if 'source' in element_copy['data']:  
                    if element_copy['data']['source'] == node_id or element_copy['data']['target'] == node_id:
                        if 'hidden' in element_copy['data']:
                            print(f"DEBUG: Unhiding edge {element_copy['data'].get('id')} connected to {node_id}")
                            element_copy['data']['hidden'] = 'false'
                    else:
                        if element_copy['data'].get('hidden') == 'true':
                            if is_descendant_of(element_copy['data']['target'], node_id, elements):
                                print(f"DEBUG: Unhiding edge {element_copy['data'].get('id')} to descendant {element_copy['data']['target']}")
                                element_copy['data']['hidden'] = 'false'
                else:  
                    if element_copy['data'].get('id') == node_id:
                        if 'hidden' in element_copy['data']:
                            print(f"DEBUG: Unhiding selected node {node_id}")
                            element_copy['data']['hidden'] = 'false'
                    else:
                        if element_copy['data'].get('hidden') == 'true':
                            if is_descendant_of(element_copy['data'].get('id'), node_id, elements):
                                print(f"DEBUG: Unhiding descendant node {element_copy['data'].get('id')}")
                                element_copy['data']['hidden'] = 'false'
                
                new_elements.append(element_copy)
        else:
            print("DEBUG: Hiding node and descendants")
            hidden_nodes = set()
            hidden_edges = set()
            
            hidden_nodes.add(node_id)
            print(f"DEBUG: Adding selected node {node_id} to hidden set")
            
            queue = [node_id]
            while queue:
                current_node = queue.pop(0)
                
                for element in elements:
                    if 'source' in element['data'] and element['data']['source'] == current_node:
                        target_node = element['data']['target']
                        if target_node not in hidden_nodes:
                            hidden_nodes.add(target_node)
                            queue.append(target_node)
                            print(f"DEBUG: Found descendant node {target_node} from {current_node}")
                        hidden_edges.add(element['data'].get('id', f"{current_node}-{target_node}"))
                        print(f"DEBUG: Adding edge {element['data'].get('id', f'{current_node}-{target_node}')} to hidden set")
            
            print(f"DEBUG: Found {len(hidden_nodes)} nodes and {len(hidden_edges)} edges to hide")
            print(f"DEBUG: Hidden nodes: {hidden_nodes}")
            print(f"DEBUG: Hidden edges: {hidden_edges}")
            
            new_elements = []
            for element in elements:
                element_copy = element.copy()
                
                if 'source' in element_copy['data']:  
                    edge_id = element_copy['data'].get('id', f"{element_copy['data']['source']}-{element_copy['data']['target']}")
                    if edge_id in hidden_edges:
                        element_copy['data']['hidden'] = 'true'
                        print(f"DEBUG: Marking edge {edge_id} as hidden")
                    else:
                        element_copy['data']['hidden'] = 'false'
                        print(f"DEBUG: Marking edge {edge_id} as visible")
                else:  
                    if element_copy['data'].get('id') in hidden_nodes:
                        element_copy['data']['hidden'] = 'true'
                        print(f"DEBUG: Marking node {element_copy['data'].get('id')} as hidden")
                    else:
                        element_copy['data']['hidden'] = 'false'
                        print(f"DEBUG: Marking node {element_copy['data'].get('id')} as visible")
                
                new_elements.append(element_copy)
        
        return new_elements
    
    return elements or []

@app.callback(
    Output('download-json', 'data'),
    Input('export-json', 'n_clicks'),
    State('cytoscape-graph', 'elements'),
    prevent_initial_call=True
)
def export_json(n_clicks, elements):
    if not n_clicks or not elements:
        return dash.no_update
    
    print("DEBUG: JSON Export requested!")
    
    export_elements = []
    for element in elements:
        if element['data'].get('hidden') != 'true':
            export_elements.append(element)
    
    clean_elements = []
    for element in export_elements:
        clean_element = {
            'data': element['data'].copy()
        }
        if 'hidden' in clean_element['data']:
            del clean_element['data']['hidden']
        clean_elements.append(clean_element)
    
    import json
    json_str = json.dumps(clean_elements, indent=2)
    
    print("DEBUG: JSON Export:")
    print(json_str)
    
    return dict(
        content=json_str,
        filename='graph_export.json',
        type='application/json'
    )

@app.callback(
    Output('node-edit-window', 'style', allow_duplicate=True),
    Input('delete-node-button', 'n_clicks'),
    State('cytoscape-graph', 'tapNode'),
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def close_window_after_delete(delete_clicks, selected_node):
    if delete_clicks and selected_node:
        return {'display': 'none'}
    return dash.no_update



# Debug for color dropdown
@app.callback(
    Output('cytoscape-graph', 'elements', allow_duplicate=True),
    Input('node-color-dropdown', 'value'),
    [State('cytoscape-graph', 'elements'),
     State('cytoscape-graph', 'tapNode')],
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def debug_color_change(new_color, elements, selected_node):
    if new_color and selected_node and elements:
        print(f"DEBUG: Color changed to {new_color} for node {selected_node.get('data', {}).get('id')}")
        new_elements = elements.copy()
        for element in new_elements:
            if element['data'].get('id') == selected_node.get('data', {}).get('id'):
                element['data']['color'] = new_color
                break
        return new_elements
    return dash.no_update

@app.callback(
    Output('cytoscape-graph', 'elements', allow_duplicate=True),
    Input('node-label-input', 'value'),
    [State('cytoscape-graph', 'elements'),
     State('cytoscape-graph', 'tapNode')],
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def debug_label_change(new_label, elements, selected_node):
    if new_label and selected_node and elements:
        print(f"DEBUG: Label changed to '{new_label}' for node {selected_node.get('data', {}).get('id')}")
        # Update the selected node's label
        new_elements = elements.copy()
        for element in new_elements:
            if element['data'].get('id') == selected_node.get('data', {}).get('id'):
                element['data']['label'] = new_label
                break
        return new_elements
    return dash.no_update



def is_descendant_of(node_id, ancestor_id, elements):
    """Check if a node is a descendant of another node"""
    if node_id == ancestor_id:
        return True
    
    # Find all edges where this node is the target
    for element in elements:
        if 'source' in element['data'] and element['data']['target'] == node_id:
            parent_id = element['data']['source']
            if is_descendant_of(parent_id, ancestor_id, elements):
                return True
    
    return False

# Display selected element info
@app.callback(
    Output('selected-element-info', 'children'),
    [Input('cytoscape-graph', 'tapNodeData'),
     Input('cytoscape-graph', 'tapEdgeData')]
)
def display_selected_element(node_data, edge_data):
    if node_data:
        return f"Selected Node: {node_data.get('label', node_data.get('id'))} (Color: {node_data.get('color', '#87cefa')})"
    elif edge_data:
        return f"Selected Edge: {edge_data.get('source')} → {edge_data.get('target')} (Label: {edge_data.get('label', '')})"
    return "No element selected"


@app.callback(
    Output('node-color-dropdown', 'value'),
    Input('cytoscape-graph', 'tapNode')
)
def update_color_dropdown(node_data):
    if node_data:
        return node_data.get('data', {}).get('color', '#87cefa')
    return '#87cefa'

@app.callback(
    Output('node-label-input', 'value'),
    Input('cytoscape-graph', 'tapNode')
)
def update_label_input(node_data):
    if node_data:
        return node_data.get('data', {}).get('label', node_data.get('data', {}).get('id', ''))
    return ''

@app.callback(
    Output('edge-label-input', 'value'),
    Input('cytoscape-graph', 'tapEdge')
)
def update_edge_label_input(edge_data):
    if edge_data:
        return edge_data.get('data', {}).get('label', '')
    return ''

@app.callback(
    Output('node-size-slider', 'value'),
    Input('cytoscape-graph', 'tapNode')
)
def update_size_slider(node_data):
    if node_data:
        return node_data.get('data', {}).get('size', 30)
    return 30





# Layout
@app.callback(
    Output('cytoscape-graph', 'layout'),
    Input('layout-dropdown', 'value')
)
def update_layout(selected_layout):
    print(f"Layout callback triggered with: {selected_layout}")  # Debug print
    
    if selected_layout == 'random':
        # Random 
        return {
            'name': 'random',
            'fit': True,
            'padding': 30,
            'animate': True,
            'animationDuration': 1000
        }
    elif selected_layout == 'breadthfirst':
        # BFS 
        return {
            'name': 'breadthfirst',
            'fit': True,
            'padding': 60,
            'animate': True,
            'animationDuration': 1000,
            'nodeDimensionsIncludeLabels': True,
            'directed': True
        }

    elif selected_layout == 'circle':
        # Circle 
        return {
            'name': 'circle',
            'fit': True,
            'padding': 50,
            'radius': 250,
            'startAngle': 3.14159,
            'sweep': 6.28319,
            'clockwise': True,
            'animate': True,
            'animationDuration': 1000
        }
    elif selected_layout == 'grid':
        # Grid 
        return {
            'name': 'grid',
            'fit': True,
            'padding': 40,
            'avoidOverlap': True,
            'nodeDimensionsIncludeLabels': True,
            'spacingFactor': 1.5,
            'animate': True,
            'animationDuration': 1000
        }
    elif selected_layout == 'cola':
        # Force directed
        return {
            'name': 'cola',                   
            'fit': True,                       
            'padding': 150,                    
            'animate': True,                   
            'animationDuration': 1000,         
            'randomize': True,                 
            'maxSimulationTime': 5000,         
            'nodeSpacing': 40,                 
            'edgeLength': 200,                 
            'nodeDimensionsIncludeLabels': True, 
            'stop': True                        
        }
    elif selected_layout == 'klay':
        # Klay
        return {
            'name': 'klay',
            'fit': True,
            'padding': 150,
            'animate': True,
            'animationDuration': 1000,
            'nodeLayering': 'NETWORK_SIMPLEX',
            'nodePlacement': 'BRANDES_KOEPF',
            'layoutHierarchy': 'DOWN',
            'spacing': 200,
            'inLayerSpacing': 150,
            'edgeSpacing': 100
        }

    else:
        return {
            'name': 'breadthfirst'
        }



# CSV export nodes
@app.callback(
    Output('download-nodes-csv', 'data'),
    Input('export-nodes-csv', 'n_clicks'),
    State('cytoscape-graph', 'elements'),
    prevent_initial_call=True
)
def export_nodes_csv(n_clicks, elements):
    if not n_clicks or not elements:
        return dash.no_update
    
    # Filter nodes and exclude hidden ones
    nodes = [el['data'] for el in elements if 'id' in el['data'] and 'source' not in el['data'] and el['data'].get('hidden') != 'true']
    df = pd.DataFrame(nodes)
    return dcc.send_data_frame(df.to_csv, "nodes.csv", index=False)

# CSV export edges
@app.callback(
    Output('download-edges-csv', 'data'),
    Input('export-edges-csv', 'n_clicks'),
    State('cytoscape-graph', 'elements'),
    prevent_initial_call=True
)
def export_edges_csv(n_clicks, elements):
    if not n_clicks or not elements:
        return dash.no_update
    
    # Filter edges and exclude hidden ones
    edges = [el['data'] for el in elements if 'source' in el['data'] and el['data'].get('hidden') != 'true']
    df = pd.DataFrame(edges)
    return dcc.send_data_frame(df.to_csv, "edges.csv", index=False)



# PNG/JPEG export
@app.callback(
    Output("cytoscape-graph", "generateImage"),
    [Input("export-png", "n_clicks"),
     Input("export-jpeg", "n_clicks")],
    prevent_initial_call=True
)
def trigger_image_export(png_clicks, jpeg_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "export-png":
        return {'type': 'png', 'action': 'download'}
    elif button_id == "export-jpeg":
        return {'type': 'jpg', 'action': 'download'}
    return dash.no_update

# Show/hide node
@app.callback(
    Output('node-edit-window', 'style'),
    [Input('cytoscape-graph', 'tapNode'),
     Input('close-node-window', 'n_clicks'),
     Input('cytoscape-graph', 'tapEdge')],
    [State('click-timing-store', 'data')]
)
def toggle_node_edit_window(node_data, close_clicks, edge_data, click_timing):
    ctx = dash.callback_context
    print(f"DEBUG: Callback triggered by: {ctx.triggered}")
    print(f"DEBUG: node_data: {node_data}")
    print(f"DEBUG: close_clicks: {close_clicks}")
    print(f"DEBUG: edge_data: {edge_data}")
    
    if not ctx.triggered:
        return {'display': 'none'}
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(f"DEBUG: Button ID: {button_id}")
    
    if button_id == 'close-node-window':
        return {'display': 'none'}
    elif button_id == 'cytoscape-graph' and 'tapEdge' in ctx.triggered[0]['prop_id']:
        return {'display': 'none'}
    elif node_data is not None:
        import time
        current_time = time.time()
        
        if click_timing is None:
            click_timing = {'last_click': None, 'click_count': 0}
        
        is_double_click = False
        if (click_timing.get('last_click') and 
            current_time - click_timing['last_click'] < 0.5 and
            click_timing.get('click_count', 0) > 0):
            is_double_click = True
            print(f"DEBUG: Double-click detected on node: {node_data}")
        else:
            print(f"DEBUG: Single-click detected on node: {node_data}")
        
        if not is_double_click:
            return {'display': 'none'}
        
        print(f"DEBUG: Opening edit window for double-click")
        
        return {'display': 'block'}
    else:
        return {'display': 'none'}

# Show/hide edge edit window when edge is clicked
@app.callback(
    Output('edge-edit-window', 'style'),
    [Input('cytoscape-graph', 'tapEdge'),
     Input('close-edge-window', 'n_clicks'),
     Input('delete-edge-button', 'n_clicks'),
     Input('cytoscape-graph', 'tapNode')]
)
def toggle_edge_edit_window(edge_data, close_clicks, delete_clicks, node_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {'display': 'none'}
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id in ['close-edge-window', 'delete-edge-button']:
        return {'display': 'none'}
    elif button_id == 'cytoscape-graph' and 'tapNode' in ctx.triggered[0]['prop_id']:
        return {'display': 'none'}
    elif edge_data is not None:
        
        return {'display': 'block'}
    else:
        return {'display': 'none'}

# Fullscreen
app.clientside_callback(
    """
    function(n_clicks) {
        var cytoDiv = document.getElementById('cytoscape-graph');
        if (n_clicks && cytoDiv) {
            if (cytoDiv.requestFullscreen) {
                cytoDiv.requestFullscreen();
            } else if (cytoDiv.mozRequestFullScreen) {
                cytoDiv.mozRequestFullScreen();
            } else if (cytoDiv.webkitRequestFullscreen) {
                cytoDiv.webkitRequestFullscreen();
            } else if (cytoDiv.msRequestFullscreen) {
                cytoDiv.msRequestFullscreen();
            }
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('fullscreen-store', 'data'),
    Input('fullscreen-btn', 'n_clicks'),
    prevent_initial_call=True
)

# Toggle export modal
@app.callback(
    [Output('export-modal', 'style'), Output('export-toggle', 'n_clicks')],
    [Input('export-toggle', 'n_clicks'), Input('close-export-modal', 'n_clicks')],
    [State('export-modal', 'style')],
    prevent_initial_call=True
)
def toggle_export_modal(export_clicks, close_clicks, current_style):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'export-toggle':
        return {'display': 'flex'}, 0
    elif trigger_id == 'close-export-modal':
        return {'display': 'none'}, 0
    
    return dash.no_update, dash.no_update

# Detect Shift key
app.clientside_callback(
    """
    function() {
        // Add event listeners for keydown and keyup
        if (!window.shiftKeyListenerAdded) {
            window.shiftKeyListenerAdded = true;
            
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Shift') {
                    window.dash_clientside.setProps({
                        'shift-key-store': true
                    });
                }
            });
            
            document.addEventListener('keyup', function(e) {
                if (e.key === 'Shift') {
                    window.dash_clientside.setProps({
                        'shift-key-store': false
                    });
                }
            });
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('shift-key-store', 'data'),
    Input('cytoscape-graph', 'elements'),
    prevent_initial_call=True
)

# Update click timing store for double-click detection
@app.callback(
    Output('click-timing-store', 'data'),
    Input('cytoscape-graph', 'tapNode'),
    prevent_initial_call=True
)
def update_click_timing(node_data):
    import time
    current_time = time.time()
    
    if node_data:
        current_data = {'last_click': current_time, 'click_count': 1}
        print(f"DEBUG: Click timing updated: {current_data}")
        return current_data
    return dash.no_update


# Callback to show delete confirmation
@app.callback(
    Output('delete-confirmation-modal', 'style'),
    [Input('delete-all-button', 'n_clicks'),
     Input('cancel-delete', 'n_clicks'),
     Input('confirm-delete', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_delete_modal(delete_clicks, cancel_clicks, confirm_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {'display': 'none'}
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'delete-all-button':
        return {'display': 'flex'}
    elif button_id in ['cancel-delete', 'confirm-delete']:
        return {'display': 'none'}
    
    return {'display': 'none'}


@app.callback(
    Output('cytoscape-graph', 'elements', allow_duplicate=True),
    [Input('confirm-delete', 'n_clicks')],
    prevent_initial_call=True
)
def confirm_delete_all(confirm_clicks):
    if not confirm_clicks:
        return dash.no_update
    return []

@app.callback(
    Output('node-edit-window', 'style', allow_duplicate=True),
    Input('node-edit-backdrop', 'n_clicks'),
    prevent_initial_call=True
)
def close_node_window_on_backdrop_click(backdrop_clicks):
    if backdrop_clicks:
        return {'display': 'none'}
    return dash.no_update

@app.callback(
    Output('edge-edit-window', 'style', allow_duplicate=True),
    Input('edge-edit-backdrop', 'n_clicks'),
    prevent_initial_call=True
)
def close_edge_window_on_backdrop_click(backdrop_clicks):
    if backdrop_clicks:
        return {'display': 'none'}
    return dash.no_update

@app.callback(
    Output('node-edit-backdrop', 'style'),
    [Input('cytoscape-graph', 'tapNode'),
     Input('close-node-window', 'n_clicks'),
     Input('cytoscape-graph', 'tapEdge')]
)
def toggle_node_edit_backdrop(node_data, close_clicks, edge_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {'display': 'none'}
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'close-node-window':
        return {'display': 'none'}
    elif button_id == 'cytoscape-graph' and 'tapEdge' in ctx.triggered[0]['prop_id']:
        return {'display': 'none'}
    elif node_data is not None:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(
    Output('edge-edit-backdrop', 'style'),
    [Input('cytoscape-graph', 'tapEdge'),
     Input('close-edge-window', 'n_clicks'),
     Input('delete-edge-button', 'n_clicks'),
     Input('cytoscape-graph', 'tapNode'),
     Input('edge-edit-backdrop', 'n_clicks')]
)
def toggle_edge_edit_backdrop(edge_data, close_clicks, delete_clicks, node_data, backdrop_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {'display': 'none'}

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id in ['close-edge-window', 'delete-edge-button', 'edge-edit-backdrop']:
        return {'display': 'none'}
    elif button_id == 'cytoscape-graph' and 'tapNode' in ctx.triggered[0]['prop_id']:
        return {'display': 'none'}
    elif edge_data is not None:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

# Callback to update hide button
@app.callback(
    Output('hide-node-button', 'children'),
    Input('cytoscape-graph', 'tapNode'),
    State('cytoscape-graph', 'elements')
)
def update_hide_button_text(selected_node, elements):
    print(f"DEBUG: update_hide_button_text called with selected_node={selected_node}")
    
    if not selected_node or not elements:
        print("DEBUG: No selected node or elements")
        return 'Hide Node'
    
    node_id = selected_node.get('data', {}).get('id')
    if not node_id:
        print("DEBUG: No node_id found")
        return 'Hide Node'
    
    print(f"DEBUG: Checking node {node_id} for hidden status")
    
    # Check if node is currently hidden
    for element in elements:
        if element['data'].get('id') == node_id:
            if element['data'].get('hidden') == 'true':
                print(f"DEBUG: Node {node_id} is hidden, returning 'Unhide Node'")
                return 'Unhide Node'
            else:
                print(f"DEBUG: Node {node_id} is not hidden, returning 'Hide Node'")
                return 'Hide Node'
    
    print(f"DEBUG: Node {node_id} not found in elements")
    return 'Hide Node'

# Callback for importing graphs
@app.callback(
    Output('cytoscape-graph', 'elements', allow_duplicate=True),
    Input('import-graph', 'contents'),
    State('import-graph', 'filename'),
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def import_graph(import_contents, import_filename):
    if import_contents is None:
        return dash.no_update
    
    print(f"DEBUG: Import triggered for file: {import_filename}")
    
    try:
        content_type, content_string = import_contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Check if RDF
        if import_filename and any(ext in import_filename.lower() for ext in ['.ttl', '.rdf', '.xml', '.jsonld']):
            print("DEBUG: Processing RDF file")
            # Parse RDF content
            g = Graph()
            content_text = decoded.decode('utf-8')
            
            if '.ttl' in import_filename.lower():
                g.parse(data=content_text, format='turtle')
            elif '.xml' in import_filename.lower() or '.rdf' in import_filename.lower():
                g.parse(data=content_text, format='xml')
            elif '.jsonld' in import_filename.lower():
                g.parse(data=content_text, format='json-ld')
            else:
                g.parse(data=content_text, format='turtle')  # Default to turtle
            
            # Convert RDF to our graph format
            elements = []
            nodes = set()
            
            print(f"DEBUG: Processing {len(g)} RDF triples")
            
            # Extract all subjects and objects as nodes
            for s, p, o in g:
                if isinstance(s, str) or hasattr(s, 'toPython'):
                    subject_id = str(s).split('/')[-1].split('#')[-1]
                    if subject_id not in nodes:
                        nodes.add(subject_id)
                        elements.append({
                            'data': {
                                'id': subject_id,
                                'label': subject_id,
                                'color': '#87cefa',
                                'size': 30
                            }
                        })
                
                if (hasattr(o, 'toPython') and 
                    str(o).startswith('http://')):
                    object_id = str(o).split('/')[-1].split('#')[-1]
                    if object_id not in nodes:
                        nodes.add(object_id)
                        elements.append({
                            'data': {
                                'id': object_id,
                                'label': object_id,
                                'color': '#87cefa',
                                'size': 30
                            }
                        })
            
            print(f"DEBUG: Created {len(nodes)} nodes: {list(nodes)}")
            
            edge_count = 0
            for s, p, o in g:
                if isinstance(s, str) or hasattr(s, 'toPython'):
                    source = str(s).split('/')[-1].split('#')[-1]
                    
                    if (hasattr(o, 'toPython') and 
                        str(o).startswith('http://')):
                        target = str(o).split('/')[-1].split('#')[-1]
                        predicate = str(p).split('/')[-1].split('#')[-1]
                        
                        if source in nodes and target in nodes:
                            edge_id = f"{source}-{target}-{predicate}"
                            edge_data = {
                                'data': {
                                    'id': edge_id,
                                    'source': source,
                                    'target': target,
                                    'label': predicate
                                }
                            }
                            elements.append(edge_data)
                            edge_count += 1
            
            print(f"DEBUG: Created {edge_count} edges")
            print(f"DEBUG: Total elements: {len(elements)}")
            
            if len(elements) == 0:
                print("DEBUG: Warning - No elements created from RDF file")
                return dash.no_update
            
            return elements
            
        elif import_filename and '.json' in import_filename.lower():
            print("DEBUG: Processing JSON file")
            # JSON files
            try:
                data = json.load(io.StringIO(decoded.decode('utf-8')))
                if isinstance(data, list) and all('data' in el for el in data):
                    print(f"DEBUG: Successfully loaded JSON with {len(data)} elements")
                    if len(data) == 0:
                        print("DEBUG: Warning - JSON file contains no elements")
                        return dash.no_update
                    return data
                else:
                    print("DEBUG: JSON format not recognized")
                    return dash.no_update
            except Exception as e:
                print(f"DEBUG: JSON parsing error: {e}")
                return dash.no_update
        elif import_filename and '.csv' in import_filename.lower():
            print("DEBUG: Processing CSV file")
            try:
                # Try different encodings for CSV files
                csv_text = None
                encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
                
                for encoding in encodings_to_try:
                    try:
                        csv_text = decoded.decode(encoding)
                        print(f"DEBUG: Successfully decoded CSV with {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                
                if csv_text is None:
                    print("DEBUG: Could not decode CSV with any supported encoding")
                    return dash.no_update
                df = pd.read_csv(io.StringIO(csv_text))
                lower_cols = [c.lower() for c in df.columns]
                columns = set(lower_cols)

                elements = []

                # If edges CSV: must contain source and target
                if {'source', 'target'}.issubset(columns):
                    print("DEBUG: Detected edges CSV")
                    source_col = df.columns[lower_cols.index('source')]
                    target_col = df.columns[lower_cols.index('target')]
                    id_col = df.columns[lower_cols.index('id')] if 'id' in columns else None
                    label_col = df.columns[lower_cols.index('label')] if 'label' in columns else None

                    # Collect node ids from endpoints
                    node_ids = set(df[source_col].astype(str)).union(set(df[target_col].astype(str)))
                    for nid in sorted(node_ids):
                        elements.append({'data': {
                            'id': str(nid),
                            'label': str(nid),
                            'color': '#87cefa',
                            'size': 30
                        }})

                    # Add edges
                    for _, row in df.iterrows():
                        src = str(row[source_col])
                        tgt = str(row[target_col])
                        eid = str(row[id_col]) if id_col and not pd.isna(row[id_col]) else f"{src}-{tgt}"
                        elabel = str(row[label_col]) if label_col and not pd.isna(row[label_col]) else ''
                        elements.append({'data': {
                            'id': eid,
                            'source': src,
                            'target': tgt,
                            'label': elabel
                        }})

                    print(f"DEBUG: CSV edges import → nodes={len([e for e in elements if 'source' not in e['data']])}, edges={len([e for e in elements if 'source' in e['data']])}")
                    return elements

                # If nodes CSV: must contain id, optional label/color/size
                if 'id' in columns:
                    print("DEBUG: Detected nodes CSV")
                    id_col = df.columns[lower_cols.index('id')]
                    label_col = df.columns[lower_cols.index('label')] if 'label' in columns else None
                    color_col = df.columns[lower_cols.index('color')] if 'color' in columns else None
                    size_col = df.columns[lower_cols.index('size')] if 'size' in columns else None

                    for _, row in df.iterrows():
                        nid = str(row[id_col])
                        nlabel = str(row[label_col]) if label_col and not pd.isna(row[label_col]) else nid
                        ncolor = str(row[color_col]) if color_col and not pd.isna(row[color_col]) else '#87cefa'
                        try:
                            nsize = int(row[size_col]) if size_col and not pd.isna(row[size_col]) else 30
                        except Exception:
                            nsize = 30
                        elements.append({'data': {
                            'id': nid,
                            'label': nlabel,
                            'color': ncolor,
                            'size': nsize
                        }})

                    print(f"DEBUG: CSV nodes import → nodes={len(elements)}")
                    return elements

                # Handle actor/movie CSV with Name column (fallback for entertainment data)
                elif 'name' in columns:
                    print("DEBUG: Detected actor/movie CSV with Name column")
                    name_col = df.columns[lower_cols.index('name')]
                    
                    # Try to find ID column (Const, ID, etc.)
                    id_col = None
                    for col in df.columns:
                        if col.lower() in ['const', 'id', 'imdb_id']:
                            id_col = col
                            break
                    
                    # If no ID column found, use Name as ID
                    if id_col is None:
                        id_col = name_col
                    
                    for _, row in df.iterrows():
                        nid = str(row[id_col])
                        nlabel = str(row[name_col])
                        
                        # Add additional info as node data if available
                        node_data = {
                            'id': nid,
                            'label': nlabel,
                            'color': '#87cefa',
                            'size': 30
                        }
                        
                        # Add optional fields if they exist
                        if 'known for' in columns:
                            known_for_col = df.columns[lower_cols.index('known for')]
                            if not pd.isna(row[known_for_col]):
                                node_data['known_for'] = str(row[known_for_col])
                        
                        if 'birth date' in columns:
                            birth_date_col = df.columns[lower_cols.index('birth date')]
                            if not pd.isna(row[birth_date_col]):
                                node_data['birth_date'] = str(row[birth_date_col])
                        
                        if 'position' in columns:
                            position_col = df.columns[lower_cols.index('position')]
                            if not pd.isna(row[position_col]):
                                node_data['position'] = str(row[position_col])
                        
                        elements.append({'data': node_data})
                    
                    print(f"DEBUG: Built {len(elements)} actor/movie nodes from CSV")
                    return elements

                print("DEBUG: CSV format not recognized. Expect nodes CSV (id,[label,color,size]) or edges CSV (source,target,[id,label])")
                return dash.no_update
            except Exception as e:
                print(f"DEBUG: CSV parsing error: {e}")
                return dash.no_update
        else:
            print("DEBUG: File format not supported")
            return dash.no_update
            
    except Exception as e:
        print(f"DEBUG: Import error: {e}")
        return dash.no_update

# Callback to reset import upload component after import
@app.callback(
    Output('import-graph', 'contents'),
    Input('cytoscape-graph', 'elements'),
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def reset_import_upload(elements):
    if elements and len(elements) > 0:
        print("DEBUG: Resetting import upload component")
        return None
    return dash.no_update

# Callback for Community Detection and Clustering
@app.callback(
    Output('cytoscape-graph', 'elements', allow_duplicate=True),
    Input('cluster-button', 'n_clicks'),
    State('cytoscape-graph', 'elements'),
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def detect_communities(n_clicks, elements):
    print(f"Detect communities callback triggered: n_clicks={n_clicks}, elements_count={len(elements) if elements else 0}")
    
    if not n_clicks or not elements:
        return dash.no_update
    
    # Create NetworkX graph from elements
    G = nx.Graph()
    
    # Add nodes
    for el in elements:
        if 'source' not in el['data']:  # It's a node
            node_id = el['data']['id']
            G.add_node(node_id)
    
    # Add edges
    for el in elements:
        if 'source' in el['data']:  # It's an edge
            source = el['data']['source']
            target = el['data']['target']
            G.add_edge(source, target)
    
    print(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Detect communities using greedy modularity
    try:
        communities = list(community.greedy_modularity_communities(G))
        print(f"Found {len(communities)} communities: {[len(c) for c in communities]}")
        
        # Assign colors to communities
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
                 '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
        
        # Update elements with community colors
        new_elements = []
        for el in elements:
            el_copy = el.copy()
            if 'source' not in el['data']:  # It's a node
                node_id = el['data']['id']
                # Find which community this node belongs to
                for i, community_set in enumerate(communities):
                    if node_id in community_set:
                        el_copy['data']['color'] = colors[i % len(colors)]
                        print(f"Node {node_id} assigned color {colors[i % len(colors)]}")
                        break
            new_elements.append(el_copy)
        
        print(f"Returning {len(new_elements)} updated elements")
        return new_elements
    except Exception as e:
        print(f"Community detection error: {e}")
        return dash.no_update

# Query parsing and execution
@app.callback(
    [Output('query-results', 'children'), Output('query-results', 'style'), Output('cytoscape-graph', 'elements', allow_duplicate=True)],
    Input('query-button', 'n_clicks'),
    State('query-input', 'value'),
    State('cytoscape-graph', 'elements'),
    prevent_initial_call=True
)
def run_entity_query(n_clicks, query_text, elements):
    if not n_clicks or not query_text or not elements:
        return dash.no_update, {'display': 'none'}, dash.no_update

    q = query_text.strip().lower()

    def normalize(s):
        return (s or '').strip().lower()

    # Build lookup maps
    id_to_label = {el['data']['id']: el['data'].get('label', el['data']['id']) for el in elements if 'source' not in el['data']}
    label_to_id = {normalize(v): k for k, v in id_to_label.items()}
    edges = [el['data'] for el in elements if 'source' in el['data']]

    matched_node_ids = set()
    matched_edge_ids = set()

    # Special: show the entire graph
    if q in ['all', 'show all', 'reset', 'clear']:
        new_elements = []
        for el in elements:
            elc = el.copy()
            data = elc['data']
            data['hidden'] = 'false'
            new_elements.append(elc)
        return [], {'display': 'none'}, new_elements

    # Pattern 1: "connected to <entity>" - Find all neighbors of an entity
    if q.startswith('connected to '):
        entity_label = query_text[len('connected to '):].strip()
        entity_id = label_to_id.get(normalize(entity_label))
        if entity_id:
            # Find all edges connected to this entity
            for e in edges:
                if normalize(e.get('source')) == normalize(entity_id) or normalize(e.get('target')) == normalize(entity_id):
                    matched_node_ids.update([e.get('source'), e.get('target')])
                    matched_edge_ids.add(e.get('id', f"{e.get('source')}-{e.get('target')}"))

    # Pattern 2: "shared by <entity1> and <entity2>" - Find common connections
    elif q.startswith('shared by '):
        rest = query_text[len('shared by '):]
        parts = [p.strip() for p in rest.split(' and ') if p.strip()]
        if len(parts) >= 2:
            e1, e2 = parts[0], parts[1]
            e1_id = label_to_id.get(normalize(e1))
            e2_id = label_to_id.get(normalize(e2))
            if e1_id and e2_id:
                # Find neighbors of both entities
                neighbors_e1 = set()
                neighbors_e2 = set()
                
                for e in edges:
                    if normalize(e.get('source')) == normalize(e1_id):
                        neighbors_e1.add(e.get('target'))
                    elif normalize(e.get('target')) == normalize(e1_id):
                        neighbors_e1.add(e.get('source'))
                    
                    if normalize(e.get('source')) == normalize(e2_id):
                        neighbors_e2.add(e.get('target'))
                    elif normalize(e.get('target')) == normalize(e2_id):
                        neighbors_e2.add(e.get('source'))
                
                # Find common neighbors
                common_neighbors = neighbors_e1.intersection(neighbors_e2)
                matched_node_ids.update([e1_id, e2_id])
                matched_node_ids.update(common_neighbors)
                
                # Add edges connecting to common neighbors
                for e in edges:
                    if (e.get('source') in [e1_id, e2_id] and e.get('target') in common_neighbors) or \
                       (e.get('target') in [e1_id, e2_id] and e.get('source') in common_neighbors):
                        matched_edge_ids.add(e.get('id', f"{e.get('source')}-{e.get('target')}"))


    # Pattern 3: "neighbors of <entity>" - Find direct connections
    elif q.startswith('neighbors of '):
        entity_label = query_text[len('neighbors of '):].strip()
        entity_id = label_to_id.get(normalize(entity_label))
        if entity_id:
            # Find all neighbors (exclude the entity itself)
            for e in edges:
                if normalize(e.get('source')) == normalize(entity_id):
                    matched_node_ids.add(e.get('target'))
                    matched_edge_ids.add(e.get('id', f"{e.get('source')}-{e.get('target')}"))
                elif normalize(e.get('target')) == normalize(entity_id):
                    matched_node_ids.add(e.get('source'))
                    matched_edge_ids.add(e.get('id', f"{e.get('source')}-{e.get('target')}"))

    # Pattern 4: "via <relationship>" - Filter by edge labels
    elif q.startswith('via '):
        relationship = query_text[len('via '):].strip()
        for e in edges:
            if normalize(e.get('label', '')) == normalize(relationship):
                matched_node_ids.update([e.get('source'), e.get('target')])
                matched_edge_ids.add(e.get('id', f"{e.get('source')}-{e.get('target')}"))

    # Update visibility using existing hidden flags/styles
    new_elements = []
    for el in elements:
        elc = el.copy()
        data = elc['data']
        if 'source' in data:
            eid = data.get('id', f"{data.get('source')}-{data.get('target')}")
            data['hidden'] = 'false' if eid in matched_edge_ids else 'true'
        else:
            nid = data.get('id')
            data['hidden'] = 'false' if nid in matched_node_ids else 'true'
        new_elements.append(elc)

    return [], {'display': 'none'}, new_elements

# Reset query - show all nodes and edges
@app.callback(
    Output('cytoscape-graph', 'elements', allow_duplicate=True),
    Input('reset-query-button', 'n_clicks'),
    State('cytoscape-graph', 'elements'),
    prevent_initial_call=True
)
def reset_query(n_clicks, elements):
    print(f"DEBUG: Reset button clicked! n_clicks={n_clicks}")
    if not n_clicks or not elements:
        print("DEBUG: No clicks or elements, returning no_update")
        return dash.no_update
    
    print(f"DEBUG: Resetting query for {len(elements)} elements")
    
    # Show all nodes and edges by setting hidden to 'false'
    new_elements = []
    for el in elements:
        elc = el.copy()
        data = elc['data']
        # Set hidden to 'false' to show all elements
        data['hidden'] = 'false'
        new_elements.append(elc)
    
    print(f"DEBUG: Reset complete, returning {len(new_elements)} elements")
    return new_elements
    
if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=False)
