# -*- coding: utf-8 -*-
import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import dash_table
from server import app
from global_data import config_data, lc0

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


MAX_NUMBER_OF_CONFIGS = 10
EDITED_CELL_COLOR = 'rgba(255,127,14, 0.5)'


def get_config_table():
    nodes_mode_select = html.Div(children=[html.Label('Set nodes ', style={'margin-left': '10px'}),
                                 dcc.RadioItems(id='nodes-mode-selector', options=[
                                     {'label': 'globally', 'value': 'global'},
                                     {'label': 'per config', 'value': 'config'},
                                 ],
                                                value='global')],
                                 style={'display': 'flex'})

    nodes_input = html.Div(children=[html.Label('Nodes: ', style={'margin-left': '10px'}),
                                     dcc.Input(id='nodes_input', type="number", min=1, max=10000, step=1, inputMode='numeric',
                            value=200),
                                     ])
    number_of_configs_input = html.Div(children=[html.Label('Configurations: '),
                                     dcc.Input(id='number-of-configs-input', type="number", min=1, max=10, step=1, inputMode='numeric',
                            value=2, debounce=False),
                                     ])

    settings_bar = html.Div(style={'display': 'flex', 'justify-content': 'space-between'})
    settings_bar.children = [number_of_configs_input, nodes_mode_select, nodes_input]

    config_table = html.Div([
        #settings_bar,
        #number_of_configs_dropdown,
        dash_table.DataTable(
            id='config-table',
            data=config_data.data.to_dict('records'),
            columns=config_data.columns,
            editable=True,
            dropdown=config_data.dropdowns,
            style_data_conditional=[{
                'if': {
                    'column_id': col,
                    'filter_query': '{{{0}}} != {{{0}_default}}'.format(col)
                },
                'background_color': EDITED_CELL_COLOR  # or whatever
            } for col in config_data.data.columns if col != 'Nodes'],
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
        html.Div(id='config-table-dummy-div'),
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
    print('data changed')
    return(dash.no_update)

@app.callback(
    [Output("config-table", "data"),
     Output("slider1", "marks"),
     Output("slider1", "max"),
     Output("slider1", "style")],
    [Input("number-of-configs-input", "value")],
    [State("config-table", "dropdown")]
)
def update_rows(nr_of_rows, dd):
    print('DROPDOWN:')
    print(dd)
    print(nr_of_rows)
    try:
        nr_of_rows = int(nr_of_rows)
        nr_of_rows = min(MAX_NUMBER_OF_CONFIGS, nr_of_rows)
        nr_of_rows = max(1, nr_of_rows)
    except:
        return(dash.no_update, dash.no_update, dash.no_update, dash.no_update)
    slider_marks = {str(i): str(i+1) for i in range(nr_of_rows)}
    slider_max = nr_of_rows - 1
    slider_style = {}
    if nr_of_rows == 1:
        slider_style = {"visibility": "hidden"}
    data = config_data.get_data(nr_of_rows)#config_data.data[:nr_of_rows]
    print(data)
    data = data.to_dict('records')
    return(data, slider_marks, slider_max, slider_style)

@app.callback(
    [Output("nodes_input", "disabled"),
     Output("config-table", "columns")],
    [Input("nodes-mode-selector", "value")],
#    [State("number-of-configs-input", "value")]
)
def set_nodes_mode(nodes_mode, ):
    if nodes_mode != 'global':
        global_nodes_disabled = True
    else:
        global_nodes_disabled = False
    columns = config_data.get_columns(with_nodes=global_nodes_disabled)
    return(global_nodes_disabled, columns)

#if __name__ == '__main__':
#    app.run_server(debug=True)
