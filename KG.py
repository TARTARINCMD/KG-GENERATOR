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
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Red+Hat+Text:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="https://use.fontawesome.com/releases/v6.4.0/css/all.css" rel="stylesheet">

        <style>
            * {
                font-family: "Red Hat Text", sans-serif !important;
            }
            
            /* Export dropdown styling */
            .export-dropdown .Select-control {
                background-color: transparent !important;
                border: 2px solid rgba(255,255,255,0.3) !important;
                border-radius: 8px !important;
                min-height: 45px !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
                transition: all 0.3s ease !important;
                position: relative !important;
                z-index: 1000 !important;
            }
            
            .export-dropdown .Select-control:hover {
                border-color: rgba(255,255,255,0.5) !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
            }
            
            .export-dropdown .Select-control .Select-value {
                color: white !important;
                font-weight: 500 !important;
                font-size: 14px !important;
            }
            
            .export-dropdown .Select-control .Select-placeholder {
                color: rgba(255,255,255,0.7) !important;
                font-size: 14px !important;
            }
            
            .export-dropdown .Select-menu-outer {
                background-color: #042c58 !important;
                border: 2px solid rgba(255,255,255,0.3) !important;
                border-radius: 8px !important;
                max-height: 200px !important;
                overflow-y: auto !important;
                overflow-x: hidden !important;
                z-index: 9999 !important;
                position: absolute !important;
                top: 100% !important;
                left: 0 !important;
                right: 0 !important;
                margin-top: 4px !important;
                box-shadow: 0 8px 25px rgba(0,0,0,0.3) !important;
            }
            
            .export-dropdown .Select-option {
                background-color: rgba(255,255,255,0.1) !important;
                color: white !important;
                padding: 12px 16px !important;
                cursor: pointer !important;
                border-bottom: 1px solid rgba(255,255,255,0.1) !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                transition: all 0.2s ease !important;
            }
            
            .export-dropdown .Select-option:hover {
                background-color: rgba(255,255,255,0.2) !important;
                transform: translateX(4px) !important;
            }
            
            .export-dropdown .Select-option:last-child {
                border-bottom: none !important;
            }
            
            /* Button hover effects */
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
            }
            
            /* Import area hover effects */
            .import-upload-area:hover {
                border-color: rgba(255,255,255,0.5) !important;
                background-color: rgba(255,255,255,0.1) !important;
                transform: translateY(-2px) !important;
            }
            
            /* Export button hover effects */
            button[id^="export-"]:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
                filter: brightness(1.1) !important;
            }
            
            button[id^="export-"]:active {
                transform: translateY(0) !important;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3) !important;
            }
            

            
            /* Ensure Font Awesome icons are visible */
            .fas, .fa {
                font-family: "Font Awesome 6 Free" !important;
                font-weight: 900 !important;
                display: inline-block !important;
                font-style: normal !important;
                font-variant: normal !important;
                text-rendering: auto !important;
                -webkit-font-smoothing: antialiased !important;
                -moz-osx-font-smoothing: grayscale !important;
            }
            
            /* Fallback icons if Font Awesome doesn't load */
            .fa.fa-trash::before { content: "🗑️"; }
            .fa.fa-save::before { content: "💾"; }
            .fa.fa-folder-open::before { content: "📁"; }
            
            /* Button icon styling */
            button .fa, button .fas {
                font-size: 16px !important;
                color: white !important;
                display: inline-block !important;
                width: auto !important;
                height: auto !important;
            }
            
            /* Delete button specific styling */
            #delete-node-button {
                transition: all 0.3s ease !important;
                position: relative !important;
                z-index: 1001 !important;
                pointer-events: auto !important;
                cursor: pointer !important;
                display: block !important;
                width: 100% !important;
                height: auto !important;
                min-height: 40px !important;
                opacity: 1 !important;
                visibility: visible !important;
            }
            
            #delete-node-button:hover {
                background-color: #c82333 !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 20px rgba(220, 53, 69, 0.4) !important;
            }
            
            #delete-node-button:active {
                transform: translateY(0) !important;
                box-shadow: 0 2px 10px rgba(220, 53, 69, 0.4) !important;
            }
            
            #delete-node-button:focus {
                outline: 2px solid #fff !important;
                outline-offset: 2px !important;
            }
            
            /* Size slider styling */
            #node-size-slider {
                z-index: 1002 !important;
                position: relative !important;
                pointer-events: auto !important;
                cursor: pointer !important;
                margin: 10px 0 !important;
            }
            
            #node-size-slider .rc-slider-track {
                background-color: #007bff !important;
                height: 6px !important;
                border-radius: 3px !important;
            }
            
            #node-size-slider .rc-slider-rail {
                background-color: #e9ecef !important;
                height: 6px !important;
                border-radius: 3px !important;
            }
            
            #node-size-slider .rc-slider-handle {
                background-color: #007bff !important;
                border: 2px solid #fff !important;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3) !important;
                width: 20px !important;
                height: 20px !important;
                margin-top: -7px !important;
                cursor: grab !important;
                z-index: 1003 !important;
            }
            

            
            #node-size-slider .rc-slider-handle:active {
                cursor: grabbing !important;
                transform: scale(1.05) !important;
            }
            
            #node-size-slider .rc-slider-mark {
                color: #666 !important;
                font-size: 12px !important;
                font-weight: 500 !important;
            }
            
            #node-size-slider .rc-slider-mark-text {
                margin-top: 8px !important;
            }
            
            /* Additional slider enhancements */
            .size-slider {
                width: 100% !important;
                margin: 15px 0 !important;
                padding: 0 10px !important;
                box-sizing: border-box !important;
            }
            
            .size-slider .rc-slider {
                position: relative !important;
                z-index: 1002 !important;
            }
            
            .size-slider .rc-slider-rail {
                position: absolute !important;
                width: 100% !important;
                background-color: #e9ecef !important;
                height: 6px !important;
                border-radius: 3px !important;
                cursor: pointer !important;
            }
            
            .size-slider .rc-slider-track {
                position: absolute !important;
                background-color: #007bff !important;
                height: 6px !important;
                border-radius: 3px !important;
                cursor: pointer !important;
            }
            
            .size-slider .rc-slider-handle {
                position: absolute !important;
                background-color: #007bff !important;
                border: 2px solid #fff !important;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3) !important;
                width: 20px !important;
                height: 20px !important;
                margin-top: -7px !important;
                cursor: grab !important;
                z-index: 1003 !important;
                transition: all 0.2s ease !important;
            }
            

            
            .size-slider .rc-slider-handle:active {
                cursor: grabbing !important;
                transform: scale(1.05) !important;
            }
            
            .size-slider .rc-slider-mark {
                position: absolute !important;
                top: 20px !important;
                color: #666 !important;
                font-size: 12px !important;
                font-weight: 500 !important;
                cursor: pointer !important;
            }
            
            .size-slider .rc-slider-mark-text {
                cursor: pointer !important;
            }
            
            /* Button container styling */
            #node-edit-window .buttons-container {
                margin-top: auto !important;
                padding-top: 30px !important;
            }
            
            /* Color dropdown styling */
            #node-color-dropdown {
                z-index: 9998 !important;
                position: relative !important;
                pointer-events: auto !important;
                cursor: pointer !important;
            }
            
            #node-color-dropdown .Select-control {
                cursor: pointer !important;
                pointer-events: auto !important;
                z-index: 9998 !important;
            }
            
            #node-color-dropdown .Select-control:hover {
                border-color: #007bff !important;
                box-shadow: 0 0 0 1px #007bff !important;
            }
            
            #node-color-dropdown .Select-menu-outer {
                z-index: 9999 !important;
                position: absolute !important;
                pointer-events: auto !important;
                background-color: white !important;
                border: 1px solid #ddd !important;
                border-radius: 4px !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
            }
            
            #node-color-dropdown .Select-option {
                cursor: pointer !important;
                pointer-events: auto !important;
            }
            
            #node-color-dropdown .Select-option:hover {
                background-color: #f8f9fa !important;
            }
            
            /* Ensure dropdown is fully interactive */
            #node-color-dropdown .Select {
                position: relative !important;
                z-index: 9998 !important;
            }
            
            #node-color-dropdown .Select-control:hover {
                border-color: #007bff !important;
                box-shadow: 0 0 0 1px #007bff !important;
            }
            
            #node-color-dropdown .Select-control:focus {
                border-color: #007bff !important;
                box-shadow: 0 0 0 1px #007bff !important;
            }
            
            /* Label input styling */
            #node-label-input {
                z-index: 1002 !important;
                position: relative !important;
                pointer-events: auto !important;
                cursor: text !important;
                transition: all 0.2s ease !important;
            }
            
            #node-label-input:focus {
                border-color: #007bff !important;
                box-shadow: 0 0 0 1px #007bff !important;
                outline: none !important;
            }
            
            #node-label-input:hover {
                border-color: #007bff !important;
            }
            
            /* Import area styling */
            .import-upload-area {
                transition: all 0.3s ease !important;
                cursor: pointer !important;
            }
            
            .import-upload-area:hover {
                border-color: rgba(255,255,255,0.6) !important;
                background-color: rgba(255,255,255,0.1) !important;
                transform: translateY(-2px) !important;
            }
            
            .import-upload-area.dragover {
                border-color: #007bff !important;
                background-color: rgba(0, 123, 255, 0.1) !important;
                transform: scale(1.02) !important;
            }
            
            /* File upload feedback */
            .upload-feedback {
                color: #28a745 !important;
                font-size: 12px !important;
                margin-top: 5px !important;
                text-align: center !important;
            }
            
            /* Close button styling */
            #close-node-window {
                cursor: pointer !important;
                transition: all 0.2s ease !important;
                pointer-events: auto !important;
                z-index: 1001 !important;
            }
            
            #close-node-window:hover {
                color: #dc3545 !important;
                transform: scale(1.1) !important;
            }
            
            #close-node-window:active {
                transform: scale(0.95) !important;
            }
            

        </style>
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
            html.Div([
                # Logo above Nodes and Relations
                html.Div([
                    html.I(className='fa fa-project-diagram', style={
                        'fontSize': '28px',
                        'color': '#007bff',
                        'marginRight': '10px',
                        'verticalAlign': 'middle'
                    }),
                    html.Span('KG Generator', style={
                        'color': 'white',
                        'fontSize': '24px',
                        'fontWeight': '700',
                        'verticalAlign': 'middle',
                        'fontFamily': '"Red Hat Text", sans-serif'
                    })
                ], style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'marginBottom': '75px'
                }),
                html.H4("Nodes and Relations", style={'color': 'white', 'fontWeight': '600', 'marginBottom': '10px', 'marginTop': '0', 'fontSize': '18px'}),
                html.Div([
                    dcc.Input(id='node1-input', type='text', placeholder='Source node', style={
                        'width': '48%',
                        'padding': '8px',
                        'border': '2px solid #ddd',
                        'borderRadius': '4px',
                        'boxSizing': 'border-box'
                    }),
                    dcc.Input(id='node2-input', type='text', placeholder='Target node', style={
                        'width': '48%',
                        'padding': '8px',
                        'border': '2px solid #ddd',
                        'borderRadius': '4px',
                        'boxSizing': 'border-box',
                        'marginLeft': '4%'
                    })
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '10px'}),

                dcc.Input(id='relationship-input', type='text', placeholder='Relation', style={
                    'width': '100%',
                    'padding': '8px',
                    'border': '2px solid #ddd',
                    'borderRadius': '4px',
                    'marginBottom': '10px',
                    'boxSizing': 'border-box'
                }),
                
                html.Button('Insert', id='add-button', style={
                    'backgroundColor': '#95a5a6',
                    'color': 'white',
                    'border': 'none',
                    'padding': '12px 16px',
                    'borderRadius': '8px',
                    'cursor': 'pointer',
                    'width': '100%',
                    'marginBottom': '10px',
                    'fontSize': '14px',
                    'fontWeight': '600',
                    'boxShadow': '0 2px 8px rgba(149, 165, 166, 0.3)',
                    'transition': 'all 0.3s ease'
                }),
                
                html.Div(id='insert-error-modal', style={
                    'position': 'fixed',
                    'top': '50%',
                    'left': '50%',
                    'transform': 'translate(-50%, -50%)',
                    'backgroundColor': '#fff',
                    'border': '2px solid #e74c3c',
                    'borderRadius': '8px',
                    'padding': '20px',
                    'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
                    'zIndex': '1000',
                    'display': 'none',
                    'minWidth': '300px',
                    'textAlign': 'center',
                    'opacity': '0',
                    'transition': 'opacity 0.3s ease-in-out',
                    'fontFamily': '"Red Hat Text", sans-serif'
                }, children=[
                    html.Div([
                        html.H4('Missing Required Fields', style={'color': '#e74c3c', 'margin': '0 0 10px 0', 'fontFamily': '"Red Hat Text", sans-serif'}),
                        html.P(id='insert-error-text', style={'color': '#333', 'margin': '0', 'fontFamily': '"Red Hat Text", sans-serif'})
                    ])
                ]),
                
                # Hidden interval for auto-hiding modal
                dcc.Interval(
                    id='modal-timer',
                    interval=3000,  # 3 seconds
                    n_intervals=0,
                    disabled=True
                ),
                
                html.Label("Layout", style={'color': 'white', 'marginBottom': '10px', 'fontWeight': '600', 'fontSize': '18px'}),
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
                    clearable=False,
                    style={'width': '100%', 'marginBottom': '15px', 'marginTop': '12px', 'boxSizing': 'border-box'}
                ),
                html.Br(),
                
                html.Button([
                    html.I(className='fa fa-sitemap', style={'marginRight': '8px'}),
                    'Detect Communities'
                ], id='cluster-button', style={
                    'backgroundColor': '#9c27b0',
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '8px',
                    'padding': '12px 16px',
                    'cursor': 'pointer',
                    'width': '100%',
                    'marginBottom': '6px',
                    'fontSize': '14px',
                    'fontWeight': '600',
                    'transition': 'all 0.3s ease',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'boxShadow': '0 2px 8px rgba(156, 39, 176, 0.3)'
                }),
                
                html.Button('Delete All', id='delete-all-button', style={
                    'backgroundColor': '#e74c3c',
                    'color': 'white',
                    'border': 'none',
                    'padding': '12px 16px',
                    'borderRadius': '8px',
                    'cursor': 'pointer',
                    'width': '100%',
                    'marginBottom': '6px',
                    'fontSize': '14px',
                    'fontWeight': '600',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'boxShadow': '0 2px 8px rgba(231, 76, 60, 0.3)',
                    'transition': 'all 0.3s ease'
                }),
            ], style={
                'padding': '12px',
                'borderRadius': '8px',
                'marginBottom': '6px'
            }),
            
            html.Div([

                # Query Section (no heading)
                html.Div([
                    html.Div([
                        dcc.Input(
                            id='query-input',
                            type='text',
                            placeholder='Query',
                            style={'width': '50%', 'padding': '8px', 'border': '2px solid #ddd', 'borderRadius': '8px', 'boxSizing': 'border-box'}
                        ),
                        html.Button([
                            html.I(className='fa fa-search')
                        ], id='query-button', style={
                            'backgroundColor': '#3498db',
                            'color': 'white',
                            'border': 'none',
                            'borderRadius': '8px',
                            'padding': '8px 12px',
                            'cursor': 'pointer',
                            'width': '23%',
                            'fontSize': '14px',
                            'fontWeight': '700',
                            'transition': 'all 0.3s ease',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'marginLeft': '2%'
                        }),
                        html.Button([
                            html.I(className='fa fa-refresh')
                        ], id='reset-query-button', style={
                            'backgroundColor': '#e74c3c',
                            'color': 'white',
                            'border': 'none',
                            'borderRadius': '8px',
                            'padding': '8px 12px',
                            'cursor': 'pointer',
                            'width': '23%',
                            'fontSize': '14px',
                            'fontWeight': '700',
                            'transition': 'all 0.3s ease',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'marginLeft': '2%'
                        })
                    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
                    html.Div(id='query-results', style={
                        'backgroundColor': 'rgba(255,255,255,0.1)',
                        'borderRadius': '8px',
                        'padding': '10px',
                        'marginTop': '6px',
                        'display': 'none'
                    })
                ], style={'marginBottom': '12px'}),

                # Import and Export at bottom
                 dcc.Upload(
                     id='import-graph',
                     children=html.Div([
                         html.I(className='fa fa-folder-open', style={'fontSize': '18px', 'marginRight': '8px'}),
                         'Import RDF/JSON/XML/CSV'
                    ], className='import-upload-area', style={
                         'display': 'flex',
                         'flexDirection': 'row',
                         'alignItems': 'center',
                         'justifyContent': 'center',
                         'padding': '12px 16px',
                         'border': '2px dashed rgba(255,255,255,0.3)',
                         'borderRadius': '8px',
                         'backgroundColor': 'rgba(255,255,255,0.05)',
                         'color': 'white',
                         'cursor': 'pointer',
                         'transition': 'all 0.3s ease',
                         'fontSize': '14px',
                         'fontWeight': '500',
                         'minHeight': '45px'
                    }),
                    style={'width': '100%', 'marginTop': '12px'},
                    multiple=False,
                    accept='.xml,.rdf,.ttl,.jsonld,.json,.csv'
                ),

                html.Button([
                    html.I(className='fa fa-download', style={'marginRight': '8px'}),
                    'Export'
                ], id='export-toggle', style={
                    'backgroundColor': 'rgba(255,255,255,0.1)',
                    'color': 'white',
                    'border': '2px solid rgba(255,255,255,0.3)',
                    'borderRadius': '8px',
                    'padding': '10px 16px',
                    'cursor': 'pointer',
                    'width': '100%',
                    'fontSize': '14px',
                    'fontWeight': '600',
                    'transition': 'all 0.3s ease',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'marginTop': '12px'
                }),
                 
                 # Delete All Confirmation
                 html.Div([
                     html.Div([
                         html.H4("Confirm Delete", style={
                             'color': '#333',
                             'marginBottom': '15px',
                             'fontWeight': '600'
                         }),
                         html.P("Are you sure you want to delete all nodes and edges?", style={
                             'color': '#666',
                             'marginBottom': '20px'
                         }),
                         html.Div([
                             html.Button('Cancel', id='cancel-delete', style={
                                 'backgroundColor': '#95a5a6',
                                 'color': 'white',
                                 'border': 'none',
                                 'padding': '8px 16px',
                                 'borderRadius': '4px',
                                 'cursor': 'pointer',
                                 'marginRight': '10px',
                                 'fontSize': '14px'
                             }),
                             html.Button('Delete All', id='confirm-delete', style={
                                 'backgroundColor': '#e74c3c',
                                 'color': 'white',
                                 'border': 'none',
                                 'padding': '8px 16px',
                                 'borderRadius': '4px',
                                 'cursor': 'pointer',
                                 'fontSize': '14px'
                             })
                         ], style={'textAlign': 'right'})
                     ], style={
                         'backgroundColor': 'white',
                         'padding': '20px',
                         'borderRadius': '8px',
                         'boxShadow': '0 4px 12px rgba(0,0,0,0.3)',
                         'maxWidth': '400px',
                         'margin': 'auto'
                     })
                 ], id='delete-confirmation-modal', style={
                     'position': 'fixed',
                     'top': '0',
                     'left': '0',
                     'width': '100%',
                     'height': '100%',
                     'backgroundColor': 'rgba(0,0,0,0.5)',
                     'display': 'none',
                     'zIndex': 2000,
                     'alignItems': 'center',
                     'justifyContent': 'center'
                 }),
                 
                 dcc.Download(id='download-nodes-csv'),
                 dcc.Download(id='download-edges-csv'),
                 dcc.Download(id='download-json'),
                 
             ], style={
                'padding': '20px',
                'paddingTop': '6px',
                 'borderRadius': '8px'
             }),

            dcc.Store(id='fullscreen-store', data=False),
            dcc.Store(id='layout-store', data='random'),  
            dcc.Store(id='shift-key-store', data=False),  
            dcc.Store(id='click-timing-store', data={'last_click': None, 'click_count': 0}), 
            
                ], style={
            'width': '25%',
            'padding': '20px',
            'height': 'calc(100vh - 40px)',
            'overflowY': 'auto',
            'boxSizing': 'border-box'
        }),
        
        # Export Modal
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.H3("Export Options", style={'color': 'white', 'margin': '0', 'textAlign': 'center', 'flex': '1'}),
                        html.Button("×", id='close-export-modal', style={
                            'background': 'none',
                            'border': 'none',
                            'color': 'white',
                            'fontSize': '24px',
                            'cursor': 'pointer',
                            'padding': '0',
                            'width': '30px',
                            'height': '30px',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'borderRadius': '50%',
                            'transition': 'all 0.3s ease'
                        })
                    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'marginBottom': '20px'}),
                    
                    html.Div([
                        html.Button([
                            html.I(className='fa fa-file-csv', style={'marginRight': '8px', 'color': '#27ae60'}),
                            'Nodes CSV'
                        ], id='export-nodes-csv', style={
                            'backgroundColor': 'rgba(39, 174, 96, 0.1)',
                            'color': '#27ae60',
                            'border': '2px solid #27ae60',
                            'borderRadius': '8px',
                            'padding': '12px 20px',
                            'cursor': 'pointer',
                            'width': '100%',
                            'fontSize': '14px',
                            'fontWeight': '600',
                            'transition': 'all 0.3s ease',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'marginBottom': '10px'
                        }),
                        
                        html.Button([
                            html.I(className='fa fa-file-csv', style={'marginRight': '8px', 'color': '#e67e22'}),
                            'Edges CSV'
                        ], id='export-edges-csv', style={
                            'backgroundColor': 'rgba(230, 126, 34, 0.1)',
                            'color': '#e67e22',
                            'border': '2px solid #e67e22',
                            'borderRadius': '8px',
                            'padding': '12px 20px',
                            'cursor': 'pointer',
                            'width': '100%',
                            'fontSize': '14px',
                            'fontWeight': '600',
                            'transition': 'all 0.3s ease',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'marginBottom': '10px'
                        }),
                        
                        html.Button([
                            html.I(className='fa fa-file-image', style={'marginRight': '8px', 'color': '#9b59b6'}),
                            'PNG Image'
                        ], id='export-png', style={
                            'backgroundColor': 'rgba(155, 89, 182, 0.1)',
                            'color': '#9b59b6',
                            'border': '2px solid #9b59b6',
                            'borderRadius': '8px',
                            'padding': '12px 20px',
                            'cursor': 'pointer',
                            'width': '100%',
                            'fontSize': '14px',
                            'fontWeight': '600',
                            'transition': 'all 0.3s ease',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'marginBottom': '10px'
                        }),
                        
                        html.Button([
                            html.I(className='fa fa-file-image', style={'marginRight': '8px', 'color': '#e74c3c'}),
                            'JPEG Image'
                        ], id='export-jpeg', style={
                            'backgroundColor': 'rgba(231, 76, 60, 0.1)',
                            'color': '#e74c3c',
                            'border': '2px solid #e74c3c',
                            'borderRadius': '8px',
                            'padding': '12px 20px',
                            'cursor': 'pointer',
                            'width': '100%',
                            'fontSize': '14px',
                            'fontWeight': '600',
                            'transition': 'all 0.3s ease',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'marginBottom': '10px'
                        }),
                        
                        html.Button([
                            html.I(className='fa fa-file-code', style={'marginRight': '8px', 'color': '#3498db'}),
                            'JSON Export'
                        ], id='export-json', style={
                            'backgroundColor': 'rgba(52, 152, 219, 0.1)',
                            'color': '#3498db',
                            'border': '2px solid #3498db',
                            'borderRadius': '8px',
                            'padding': '12px 20px',
                            'cursor': 'pointer',
                            'width': '100%',
                            'fontSize': '14px',
                            'fontWeight': '600',
                            'transition': 'all 0.3s ease',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'marginBottom': '0'
                        })
                    ])
                ], style={
                    'backgroundColor': '#34495e',
                    'padding': '30px',
                    'borderRadius': '12px',
                    'boxShadow': '0 8px 32px rgba(0,0,0,0.3)',
                    'maxWidth': '400px',
                    'width': '90%'
                })
            ], style={
                'position': 'fixed',
                'top': 0,
                'left': 0,
                'width': '100%',
                'height': '100%',
                'backgroundColor': 'rgba(0,0,0,0.7)',
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'center',
                'zIndex': 1000
            })
        ], id='export-modal', style={'display': 'none'}),
        
        # Right Panel
        html.Div([
            # Fullscreen button 
            html.Button(
                '⛶', 
                id='fullscreen-btn',
                style={
                    'position': 'absolute',
                    'top': '30px',
                    'right': '30px',
                    'backgroundColor': 'rgba(0,0,0,0.7)',
                    'color': 'white',
                    'border': 'none',
                    'padding': '8px',
                    'borderRadius': '50%',
                    'cursor': 'pointer',
                    'width': '40px',
                    'height': '40px',
                    'fontSize': '18px',
                    'zIndex': 1000,
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'transition': 'background-color 0.3s ease'
                }
            ),
            
            # Graph container
            html.Div([
                cyto.Cytoscape(
                    id='cytoscape-graph',            
                    layout={'name': 'random', 'fit': True, 'animate': True, 'padding': 30},
                    style={
                        'width': '100%', 
                        'height': 'calc(100vh - 60px)', 
                        'background': '#fff',
                        'position': 'static',
                        'minHeight': '600px',
                        'boxSizing': 'border-box',
                        'borderRadius': '12px'
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
                                'border-color': '#ff6b6b',
                                'border-opacity': 0.8,
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
            html.Div(id='node-edit-backdrop', style={
                'position': 'fixed',
                'top': '0',
                'left': '0',
                'width': '100%',
                'height': '100%',
                'backgroundColor': 'transparent',
                'zIndex': 999,
                'display': 'none'
            }),
            html.Div([
                html.Div([
                    html.H3("Edit Node", style={'margin': '0', 'color': '#333', 'flex': '1'}),
                    html.Button("×", id='close-node-window', style={
                        'background': 'none',
                        'border': 'none',
                        'fontSize': '24px',
                        'cursor': 'pointer',
                        'color': '#999',
                        'padding': '0',
                        'width': '30px',
                        'height': '30px',
                        'display': 'flex',
                        'alignItems': 'center',
                        'justifyContent': 'center'
                    })
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '15px'}),
                html.Div([
                    html.Label("Label:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.Input(
                        id='node-label-input',
                        type='text',
                        placeholder='Enter node label',
                        debounce=True,
                        style={'width': '100%', 'padding': '8px', 'border': '1px solid #ddd', 'borderRadius': '4px', 'marginBottom': '15px', 'boxSizing': 'border-box'}
                    ),
                    html.Label("Color:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
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
                        style={'width': '100%', 'marginBottom': '15px'}
                    ),
                    html.Label("Size:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
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
                        html.Button('Hide Node', id='hide-node-button', n_clicks=0, style={
                            'backgroundColor': '#6c757d',
                            'color': 'white',
                            'border': 'none',
                            'padding': '6px 16px',
                            'borderRadius': '4px',
                            'cursor': 'pointer',
                            'width': '100%',
                            'marginBottom': '6px',
                            'position': 'relative',
                            'zIndex': 1001,
                            'pointerEvents': 'auto',
                            'fontSize': '14px',
                            'fontWeight': 'bold',
                            'height': '40px'
                        }),
                        html.Button('Delete Node', id='delete-node-button', n_clicks=0, style={
                            'backgroundColor': '#dc3545',
                            'color': 'white',
                            'border': 'none',
                            'padding': '6px 16px',
                            'borderRadius': '4px',
                            'cursor': 'pointer',
                            'width': '100%',
                            'marginTop': '6px',
                            'position': 'relative',
                            'zIndex': 1001,
                            'pointerEvents': 'auto',
                            'userSelect': 'none',
                            'outline': 'none',
                            'fontSize': '14px',
                            'fontWeight': 'bold',
                            'height': '40px'
                        })
                    ], style={'marginTop': 'auto'}, className='buttons-container')
                ])
            ], style={
                'backgroundColor': 'white',
                'border': '1px solid #ccc',
                'borderRadius': '8px',
                'padding': '20px',
                'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
                'minWidth': '280px',
                'maxWidth': '320px',
                'height': '400px',
                'display': 'flex',
                'flexDirection': 'column',
                'justifyContent': 'space-between'
            })
        ], id='node-edit-window', style={
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'zIndex': 9999,
            'display': 'none'
        }),
        
        # Edge edit window
        html.Div([
            # click-outside-to-close
            html.Div(id='edge-edit-backdrop', style={
                'position': 'fixed',
                'top': '0',
                'left': '0',
                'width': '100%',
                'height': '100%',
                'backgroundColor': 'transparent',
                'zIndex': 999,
                'display': 'none'
            }),
            html.Div([
                html.Div([
                    html.H3("Edit Edge", style={'margin': '0', 'color': '#333', 'flex': '1'}),
                    html.Button("×", id='close-edge-window', style={
                        'background': 'none',
                        'border': 'none',
                        'fontSize': '24px',
                        'cursor': 'pointer',
                        'color': '#999',
                        'padding': '0',
                        'width': '30px',
                        'height': '30px',
                        'display': 'flex',
                        'alignItems': 'center',
                        'justifyContent': 'center'
                    })
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '15px'}),
                html.Div([
                    html.Label("Label:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.Input(
                        id='edge-label-input',
                        type='text',
                        placeholder='Enter edge label',
                        debounce=True,
                        style={'width': '100%', 'padding': '8px', 'border': '1px solid #ddd', 'borderRadius': '4px', 'marginBottom': '15px'}
                    ),
                    html.Button('Delete Edge', id='delete-edge-button', n_clicks=0, style={
                        'backgroundColor': '#dc3545',
                        'color': 'white',
                        'border': 'none',
                        'padding': '8px 16px',
                        'borderRadius': '4px',
                        'cursor': 'pointer',
                        'width': '100%',
                        'marginTop': '10px'
                    })

                ])
            ], style={
                'backgroundColor': 'white',
                'border': '1px solid #ccc',
                'borderRadius': '8px',
                'padding': '20px',
                'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
                'minWidth': '250px',
                'maxWidth': '300px',
                'maxHeight': '80vh',
                'overflowY': 'auto'
            })
        ], id='edge-edit-window', style={
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'zIndex': 1000,
            'display': 'none'
        })
    ], id='graph-container', style={'position': 'relative', 'width': '100%'})
    ], style={
        'width': '75%',
        'marginLeft': '20px',
        'marginRight': '20px',
        'marginTop': '20px',
        'height': 'calc(100vh - 40px)',
        'overflow': 'hidden',
        'boxSizing': 'border-box'
    })
    ], style={
        'display': 'flex',
        'height': 'calc(100vh - 40px)',
        'overflow': 'hidden',
        'boxSizing': 'border-box'
    })
], style={
    'backgroundColor': '#042c58', 
    'minHeight': '100vh',
    'maxHeight': '100vh',
    'overflow': 'hidden',
    'boxSizing': 'border-box',
    'fontFamily': '"Red Hat Text", sans-serif'
})

# Validate input fields for Insert button styling
@app.callback(
    Output('add-button', 'style'),
    [Input('node1-input', 'value'),
     Input('node2-input', 'value'),
     Input('relationship-input', 'value')]
)
def validate_insert_inputs(node1, node2, relationship):
    all_filled = node1 and node2 and relationship
    
    if all_filled:
        return {
            'backgroundColor': '#27ae60',
            'color': 'white',
            'border': 'none',
            'padding': '12px 16px',
            'borderRadius': '8px',
            'cursor': 'pointer',
            'width': '100%',
            'marginBottom': '10px',
            'fontSize': '14px',
            'fontWeight': '600',
            'boxShadow': '0 2px 8px rgba(39, 174, 96, 0.3)',
            'transition': 'all 0.3s ease'
        }
    else:
        return {
            'backgroundColor': '#95a5a6',
            'color': 'white',
            'border': 'none',
            'padding': '12px 16px',
            'borderRadius': '8px',
            'cursor': 'pointer',
            'width': '100%',
            'marginBottom': '10px',
            'fontSize': '14px',
            'fontWeight': '600',
            'boxShadow': '0 2px 8px rgba(149, 165, 166, 0.3)',
            'transition': 'all 0.3s ease'
        }
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
    
    return {
        'position': 'fixed',
        'top': '50%',
        'left': '50%',
        'transform': 'translate(-50%, -50%)',
        'backgroundColor': '#fff',
        'border': '2px solid #e74c3c',
        'borderRadius': '8px',
        'padding': '20px',
        'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
        'zIndex': '1000',
        'display': 'block',
        'minWidth': '300px',
        'textAlign': 'center',
        'opacity': '1',
        'transition': 'opacity 0.3s ease-in-out',
        'fontFamily': '"Red Hat Text", sans-serif'
    }, error_msg, False

# Auto-hide modal when timer fires
@app.callback(
    Output('insert-error-modal', 'style', allow_duplicate=True),
    Output('modal-timer', 'disabled', allow_duplicate=True),
    Input('modal-timer', 'n_intervals'),
    prevent_initial_call=True
)
def auto_hide_modal(n_intervals):
    if n_intervals > 0:
        return {
            'position': 'fixed',
            'top': '50%',
            'left': '50%',
            'transform': 'translate(-50%, -50%)',
            'backgroundColor': '#fff',
            'border': '2px solid #e74c3c',
            'borderRadius': '8px',
            'padding': '20px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
            'zIndex': '1000',
            'display': 'block',
            'minWidth': '300px',
            'textAlign': 'center',
            'opacity': '0',
            'transition': 'opacity 0.3s ease-in-out',
            'fontFamily': '"Red Hat Text", sans-serif'
        }, True
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
        return {
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'zIndex': 1000,
            'display': 'none'
        }
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
        return {
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'zIndex': 1000,
            'display': 'none'
        }
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(f"DEBUG: Button ID: {button_id}")
    
    if button_id == 'close-node-window':
        return {
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'zIndex': 1000,
            'display': 'none'
        }
    elif button_id == 'cytoscape-graph' and 'tapEdge' in ctx.triggered[0]['prop_id']:
        return {
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'zIndex': 1000,
            'display': 'none'
        }
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
            return {
                'position': 'absolute',
                'top': '10px',
                'left': '10px',
                'zIndex': 1000,
                'display': 'none'
            }
        
        print(f"DEBUG: Opening edit window for double-click")
        graph_width = 1200  
        graph_height = 800 
        window_width = 320 
        window_height = 400 
        
        window_x = (graph_width - window_width) // 2
        window_y = (graph_height - window_height) // 2
        
        return {
            'position': 'absolute',
            'top': f'{window_y}px',
            'left': f'{window_x}px',
            'zIndex': 9999,
            'display': 'block'
        }
    else:
        return {
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'zIndex': 1000,
            'display': 'none'
        }

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
        return {
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'zIndex': 1000,
            'display': 'none'
        }
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id in ['close-edge-window', 'delete-edge-button']:
        return {
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'zIndex': 1000,
            'display': 'none'
        }
    elif button_id == 'cytoscape-graph' and 'tapNode' in ctx.triggered[0]['prop_id']:
        return {
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'zIndex': 1000,
            'display': 'none'
        }
    elif edge_data is not None:
        graph_width = 1200  
        graph_height = 800  
        window_width = 300  
        window_height = 200  
        
        window_x = (graph_width - window_width) // 2
        window_y = (graph_height - window_height) // 2
        
        window_x = max(10, min(window_x, graph_width - window_width - 10))
        window_y = max(10, min(window_y, graph_height - window_height - 10))
        
        return {
            'position': 'absolute',
            'top': f'{window_y}px',
            'left': f'{window_x}px',
            'zIndex': 1000,
            'display': 'block'
        }
    else:
        return {
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'zIndex': 1000,
            'display': 'none'
        }

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
        return {
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'rgba(0,0,0,0.5)',
            'display': 'flex',
            'zIndex': 2000,
            'alignItems': 'center',
            'justifyContent': 'center'
        }
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
        return {
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'zIndex': 1000,
            'display': 'none'
        }
    return dash.no_update

@app.callback(
    Output('edge-edit-window', 'style', allow_duplicate=True),
    Input('edge-edit-backdrop', 'n_clicks'),
    prevent_initial_call=True
)
def close_edge_window_on_backdrop_click(backdrop_clicks):
    if backdrop_clicks:
        return {
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'zIndex': 1000,
            'display': 'none'
        }
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
        return {
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'transparent',
            'zIndex': 999,
            'display': 'block'
        }
    else:
        return {'display': 'none'}

@app.callback(
    Output('edge-edit-backdrop', 'style'),
    [Input('cytoscape-graph', 'tapEdge'),
     Input('close-edge-window', 'n_clicks'),
     Input('delete-edge-button', 'n_clicks'),
     Input('cytoscape-graph', 'tapNode')]
)
def toggle_edge_edit_backdrop(edge_data, close_clicks, delete_clicks, node_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {'display': 'none'}
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id in ['close-edge-window', 'delete-edge-button']:
        return {'display': 'none'}
    elif button_id == 'cytoscape-graph' and 'tapNode' in ctx.triggered[0]['prop_id']:
        return {'display': 'none'}
    elif edge_data is not None:
        return {
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'transparent',
            'zIndex': 999,
            'display': 'block'
        }
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
    app.run_server(host='localhost', port=8080, debug=False) 
