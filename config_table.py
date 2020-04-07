# -*- coding: utf-8 -*-
import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import dash_table
from server import app
from global_data import config_data
from flask import request
import sys

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


MAX_NUMBER_OF_CONFIGS = 10
EDITED_CELL_COLOR = 'rgba(255,127,14, 0.5)'


def get_config_table():
    nodes_input = html.Div(children=[#html.Label('Nodes: ', style={'margin-left': '10px'}),
                                     dcc.Input(id='nodes_input', type="number", min=1, max=10000, step=1,
                                               inputMode='numeric',
                                               value=200,
                                               style={'margin-left': '10px'}),
                                     ])
    nodes_mode_select = html.Div(children=[#html.Label('Set nodes: ', style={'margin-left': '10px'}),
                                 dcc.Checklist(id='nodes-mode-selector', options=[
                                     #{'label': 'per config', 'value': 'config'},
                                     {'label': 'Global nodes', 'value': 'global'},
                                 ],
                                                value=['global']),
                                           nodes_input],
                                 style={'display': 'flex'})
    number_of_configs_input = html.Div(children=[html.Label('Configurations: '),
                                                 dcc.Input(id='number-of-configs-input', type="number", min=1, max=10,
                                                           step=1,
                                                           inputMode='numeric',
                                                           value=2, debounce=False),
                                                 ])

    net_selector = html.Div(children=[#html.Label('Net: ', style={'margin-left': '10px'}),
                                      dcc.Dropdown(id='net_selector',
                                                   options=[{'label': weight_file,
                                                             'value': weight_path}
                                                            for weight_file, weight_path
                                                            in zip(config_data.weight_files,
                                                                   config_data.weight_paths)],
                                                   #style={'flex': 1},
                                                   #style={'display': 'inline-block'},
                                                   value=config_data.weight_paths[0],
                                                   placeholder='',
                                                   clearable=False),
                                      ],
                            #style={'display': 'flex'}
                            )
    net_mode_select = html.Div(children=[#html.Label('Select net: ', style={'margin-left': '10px'}),
                                         dcc.Checklist(id='net-mode-selector', options=[
                                             #{'label': 'per config', 'value': 'config'},
                                             {'label': 'Global net', 'value': 'global'},
                                         ],
                                                value=['global']),
                                         net_selector],
                               #style={'display': 'flex'}
                               )

    reset_button = html.Button(id='reset_defaults_button',
                               children='Reset')

    reset_button_clicked_indicator = html.Div(id='reset_button_clicked_indicator', style={'display': 'none'})

    settings_bar = html.Div()#style={'display': 'flex', 'justify-content': 'flex-start'})#'space-between'
    settings_bar.children = [number_of_configs_input, net_mode_select, nodes_mode_select,
                             reset_button,
                             reset_button_clicked_indicator
                             ]

    style_non_default = [{
                'if': {
                    'column_id': col,
                    'filter_query': '{{{0}}} != {{{0}_default}}'.format(col)
                },
                'background_color': EDITED_CELL_COLOR
            } for col in config_data.data.columns if col != 'Nodes' and col != 'WeightsFile']

    style_below_min = [{
                'if': {
                    'column_id': col,
                    'filter_query': '{{{0}}} < {{{0}_min}}'.format(col)
                },
                'background_color': 'red'
            } for col in config_data.columns_with_min]

    style_above_max = [{
                'if': {
                    'column_id': col,
                    'filter_query': '{{{0}}} > {{{0}_max}}'.format(col)
                },
                'background_color': 'red'
            } for col in config_data.columns_with_max]

    conditional_style = style_non_default + style_below_min + style_above_max

    config_table = html.Div([
        #settings_bar,
        #number_of_configs_dropdown,
        dash_table.DataTable(
            id='config-table',
            data=config_data.data.to_dict('records'),
            columns=config_data.columns,
            editable=True,
            dropdown=config_data.dropdowns,
            style_data_conditional=conditional_style,
            merge_duplicate_headers=True,
            style_cell={'textAlign': 'center'},
            style_table={'overflowX': 'auto', 'padding-bottom': '6em'}
        ),
        html.Div([html.Br() for _ in range(4)]),
        #html.Div('Dummy2 to take space')
    ],
        style={'width': '100%', 'height': '100%'})

    config_component = html.Div([
        #number_of_configs_dropdown,
        settings_bar,
        config_table,
        html.Div(id='config-table-dummy-div', style={'display': 'none'}),
        html.Div(id='data-validity', style={'display': 'none'}),
        #html.Div('Font1 .a.b.c.d.E.F.G', style={'font-family': 'sans-serif'}),
        #html.Div('Font2 .a.b.c.d.E.F.G', style={'font-family': "'BundledMonoSpace'"}),
        #html.Div('Font3 .a.b.c.d.E.F.G'),
        #html.Div('Font4 .a.b.c.d.E.F.G', style={'font-family': "'BundledFreeMono'"})
        ],
        style={'width': '100%', 'display': 'flex', 'flex-direction': 'column'})

    return(config_component)


@app.callback(
    Output("config-table-dummy-div", "children"),
    [Input("config-table", "data")],
#    [State("number-of-configs-input", "value")]
)
def copy_table(data):
    data = pd.DataFrame(data)
    has_changed = config_data.update_data(data)
    #print('data changed')
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
    print('DAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA:')
    print(dd)
    print(nr_of_rows)
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
        slider_style["visibility"] = "hidden" #= {"visibility": "hidden"}
    data = config_data.get_data(nr_of_rows)#config_data.data[:nr_of_rows]
    #print(data)
    #print(data.columns)
    print(data.shape)
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
