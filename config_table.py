# -*- coding: utf-8 -*-
import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import dash_table
from server import app
from global_data import config_data
#from flask import request
#import sys

from constants import MAX_NODES, MAX_NUMBER_OF_CONFIGS, DEFAULT_NUMBER_OF_CONFIGS, DEFAULT_NODES

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

EDITED_CELL_COLOR = 'rgba(255,127,14, 0.5)'
LINE_COLOR = 'rgb(100, 100, 100)'

def get_settings_bar():
    settings_bar = html.Div(style={'display': 'flex',
                                   'justifyContent': 'space-between',
                                   'borderTop': f'1px solid {LINE_COLOR}',
                                   'paddingTop': '5px',
                                   'paddingBottom': '5px'})  # style={'display': 'flex', 'justifyContent': 'flex-start'})#'space-between'


    number_of_configs_input = html.Div(children=[html.Div('#Configurations: '),
                                                 dcc.Input(id='number-of-configs-input', type="number", min=1, max=MAX_NUMBER_OF_CONFIGS,
                                                           step=1,
                                                           inputMode='numeric',
                                                           value=DEFAULT_NUMBER_OF_CONFIGS, debounce=False),
                                                 ], style={'flex': 1})

    weight_options = [{'label': weight_file, 'value': weight_path} for weight_file, weight_path
                      in zip(config_data.weight_files, config_data.weight_paths)]
    net_selector_dropdown = dcc.Dropdown(id='net_selector',
                                         options=weight_options,
                                         value=config_data.weight_paths[0],
                                         placeholder='',
                                         clearable=False)

    net_mode_select = dcc.Checklist(id='net-mode-selector',
                                    options=[{'label': 'Global net',
                                              'value': 'global'}],
                                    value=['global'])

    net_selector = html.Div(children=[net_mode_select, net_selector_dropdown],
                            style={'flex': 1})


    nodes_input = dcc.Input(id='nodes_input',
                            type="number",
                            min=1,
                            max=MAX_NODES,
                            step=1,
                            inputMode='numeric',
                            value=DEFAULT_NODES,
                            )

    nodes_mode_select = dcc.Checklist(id='nodes-mode-selector',
                                      options=[{'label': 'Global nodes',
                                                'value': 'global'}],
                                      value=['global'])

    nodes_selector = html.Div(children=[nodes_mode_select, nodes_input],
                              style={'flex': 1})


    reset_button = html.Button(id='reset_defaults_button',
                               children='Reset',
                               style={'width': '100%', 'height': '100%'})

    reset_button_clicked_indicator = html.Div(id='reset_button_clicked_indicator',
                                              style={'display': 'none'})

    reset_button_container = html.Div(children=[reset_button, reset_button_clicked_indicator],
                                      style={'flex': 1})

    separator_div1 = html.Div(style={'flex': 1})

    settings_bar.children = [number_of_configs_input, nodes_selector, net_selector, separator_div1, reset_button_container]

    return(settings_bar)

def get_config_table():
    settings_bar = get_settings_bar()

    highlight_non_default = [{
                'if': {
                    'column_id': col,
                    'filter_query': '{{{0}}} != {{{0}_default}}'.format(col)
                },
                'background_color': EDITED_CELL_COLOR
            } for col in config_data.data.columns if col != 'Nodes' and col != 'WeightsFile']

    highlight_below_min = [{
                'if': {
                    'column_id': col,
                    'filter_query': '{{{0}}} < {{{0}_min}}'.format(col)
                },
                'background_color': 'red'
            } for col in config_data.columns_with_min]

    highlight_above_max = [{
                'if': {
                    'column_id': col,
                    'filter_query': '{{{0}}} > {{{0}_max}}'.format(col)
                },
                'background_color': 'red'
            } for col in config_data.columns_with_max]

    conditional_style = highlight_non_default + highlight_below_min + highlight_above_max

    config_table = html.Div([
        dash_table.DataTable(
            id='config-table',
            data=config_data.data.to_dict('records'),
            columns=config_data.columns,
            editable=True,
            dropdown=config_data.dropdowns,
            style_data_conditional=conditional_style,
            merge_duplicate_headers=True,
            style_cell={'textAlign': 'center'},
            style_table={'overflowX': 'auto', 'flex': 1},# 'height': '100%'}#, 'paddingBottom': '6em'}
        ),
        #html.Div([html.Br() for _ in range(4)]),
    ],
        style={'width': '100%', 'height': '100%', 'display': 'flex', 'flexDirection': 'column', 'flex': 1})

    config_component = html.Div([
        #number_of_configs_dropdown,
        settings_bar,
        config_table,
        html.Div(id='config-table-dummy-div', style={'display': 'none'}),
        html.Div(id='data-validity', style={'display': 'none'}),
        ],
        style={'width': '100%', 'display': 'flex', 'flexDirection': 'column', 'flex': 1})

    return(config_component)


@app.callback(
    Output("config-table-dummy-div", "children"),
    [Input("config-table", "data")],
)
def copy_table(data):
    data = pd.DataFrame(data)
    has_changed = config_data.update_data(data)
    return(str(has_changed))

@app.callback(
    [Output("config-table", "data"),
     Output("slider1", "marks"),
     Output("slider1", "max"),
     Output("slider1", "style"),
     Output("slider1", "value")],
    [Input("number-of-configs-input", "value"),
     Input("reset_button_clicked_indicator", "children")
     ],
    [State("config-table", "dropdown"),
     State("slider1", "value")]
)
def update_rows(nr_of_rows, reset_button_clicked, dd, slider_value):
    try:
        nr_of_rows = int(nr_of_rows)
        nr_of_rows = min(MAX_NUMBER_OF_CONFIGS, nr_of_rows)
        nr_of_rows = max(1, nr_of_rows)
    except:
        return(dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update)
    slider_marks = {str(i): 'config' + str(i+1) for i in range(nr_of_rows)}
    slider_max = nr_of_rows - 1
    slider_style = {}
    if nr_of_rows == 1:
        slider_style["visibility"] = "hidden"
    data = config_data.get_data(nr_of_rows)
    data = data.to_dict('records')

    new_slider_value = min(slider_value, slider_max)

    return(data, slider_marks, slider_max, slider_style, new_slider_value)

@app.callback(
    [Output("nodes_input", "disabled"),
     Output("net_selector", "disabled"),
     Output("config-table", "columns"),
     ],
    [Input("nodes-mode-selector", "value"),
     Input("net-mode-selector", 'value')],
)
def set_nodes_and_net_mode(nodes_mode, net_mode):
    global_nodes_disabled = True if nodes_mode != ['global'] else False
    global_net_disabled = True if net_mode != ['global'] else False
    columns = config_data.get_columns(with_nodes=global_nodes_disabled, with_nets=global_net_disabled)
    return(global_nodes_disabled, global_net_disabled, columns)


@app.callback(
    Output('reset_button_clicked_indicator', 'children'),
    [Input('reset_defaults_button', 'n_clicks_timestamp')],
)
def reset_data(n_clicks_timestamp):
    config_data.construct_config_data()
    return(str(n_clicks_timestamp))

#for debugging datatable data
#@app.callback(
#     Output('reset_button_clicked_indicator', "style"),
#    [Input("config-table", "data")],
#)
#def set_nodes_and_net_mode(data):
#    print('Data:')
#    print(data)
#    return(dash.no_update)
