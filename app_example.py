# -*- coding: utf-8 -*-
import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import dash_table
from collections import OrderedDict

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

import chess.engine
import chess

MAX_NUMBER_OF_CONFIGS = 10
EDITED_CELL_COLOR = 'rgba(255,127,14,0.5)'

class ConfigData:
    def __init__(self):
        self.data = pd.DataFrame()
        self.data_analyzed = pd.DataFrame()

    def update_data(self, data):
        nr_of_rows = data.shape[0]
        self.data[:nr_of_rows] = data
        return(self.is_data_equal_to_analyzed())

    def is_data_equal_to_analyzed(self):
        return(self.data.equals(self.data_analyzed))


filter_out_options = ['WeightsFile',
                      'Backend',
                      'BackendOptions',
                      'NNCacheSize',
                      'Temperature',
                      'TempDecayMoves',
                      'TempCutoffMove',
                      'TempEndgame',
                      'TempValueCutoff',
                      'TempVisitOffset',
                      'DirichletNoise',
                      'VerboseMoveStats',
                      'SyzygyFastPlay',
                      'MultiPV',
                      'PerPVCounters',
                      'ScoreType',
                      'HistoryFill',
                      'SyzygyPath',
                      'Ponder',
                      'UCI_Chess960',
                      'UCI_ShowWDL',
                      'ConfigFile',
                      'SmartPruningFactor',
                      'RamLimitMb',
                      'MoveOverheadMs',
                      'Slowmover',
                      'ImmediateTimeUse',
                      'LogFile']

threading_and_batching = ['Threads',
                         'MinibatchSize',
                         'MaxPrefetch',
                         'MaxCollisionEvents',
                         'MaxCollisionVisits',
                         'OutOfOrderEval',
                         'MaxConcurrentSearchers']

cpuct = ['CPuct', 'CPuctRootOffset', 'CPuctBase', 'CPuctFactor']

fpu = ['FpuStrategy',
       'FpuValue',
       'FpuStrategyAtRoot',
       'FpuValueAtRoot']

draw_score = ['DrawScoreSideToMove',
              'DrawScoreOpponent',
              'DrawScoreWhite',
              'DrawScoreBlack']

search_enhancements = ['LogitQ',
                       'ShortSightedness']

policy_temp = ['PolicyTemperature']

misc = ['CacheHistoryLength',
        'StickyEndgames']

selfplay_parameters = ['KLDGainAverageInterval',
                       'MinimumKLDGainPerNode']

groups = {'cpuct': cpuct,
          'fpu': fpu,
          'pst': policy_temp,
          'search enhancements': search_enhancements,
          'draw score': draw_score,
          'misc': misc,
          'self-play parameters': selfplay_parameters,
          'threading and batching': threading_and_batching}

column_order = cpuct + fpu + policy_temp + search_enhancements + draw_score + misc + selfplay_parameters + threading_and_batching

def leela(args):
    lc0 = chess.engine.SimpleEngine.popen_uci(args)
    return(lc0)

net = '/home/jusufe/tmp/weights_run2_591226.pb.gz'
engine = '/home/jusufe/lc0_test4/build/release/lc0'
args = [engine, '--weights=' + net]
lc0 = leela(args)


def try_to_round(value, precision):
    #don't convert boolean values to floats
    if isinstance(value, bool):
        return value
    try:
        out = str(round(float(value), precision))
        #print(value, out, type(value))
    except ValueError:
        out = value
    return out

def get_gategory(name, groups):
    category = 'misc'
    for group in groups:
        if name in groups[group]:
            category = group
            return(category)
    return(category)

def create_column(option, df_dict, columns, dropdowns, category_groups):
    option_type = option.type
    default = option.default
    if option_type == 'check':
        default = str(default)
    default = try_to_round(default, 3)
    name = option.name
    df_dict[name] = [default]
    df_dict[name+'_default'] = [default]

    category = get_gategory(name, groups)
    col = {'id': name, 'name': [category, name], 'clearable': False}
    if option_type == 'combo' or option_type == 'check':
        col['presentation'] = 'dropdown'
        if option_type == 'combo':
            var = option.var
        else:
            var = ('True', 'False')
        dropdown = {'options': [{'label': val, 'value': val} for val in var],
                    'clearable': False}
        dropdowns[name] = dropdown
    columns.append(col)
    #if option_type == 'spin':
    return(df_dict, columns, dropdowns)


def get_config_table(lc0_engine):
    config_data = ConfigData()

    df_dict = {}
    columns = []
    dropdowns = {}
    for opt in lc0.options:
        option = lc0.options[opt]
        if opt not in filter_out_options:
            df_dict, columns, dropdowns = create_column(option, df_dict, columns, dropdowns, groups)

    columns.sort(key= lambda x: column_order.index(x['name'][1]) if x['name'][1] in column_order else 999999)



    df = pd.DataFrame(df_dict)
    df = pd.concat([df]*MAX_NUMBER_OF_CONFIGS, ignore_index=True)
    config_data.data = df


    number_of_configs_dropdown = html.Div(children=[html.P(''),
                                                    dcc.Dropdown(
        id='number-of-configs-dropdown',
        options=[
            {'label': i, 'value': i} for i in range(1, MAX_NUMBER_OF_CONFIGS + 1)
        ],
        value=2,
        clearable=False,
        style={'width': '50px'},
                                                    )
                                                    ],
                                          style={'display': 'flex',
                                                 'flex-direction': 'row',
                                                 'align-items:': 'flex-end'}
                                          )
    config_table = html.Div([
        dash_table.DataTable(
            id='config-table',
            data=df.to_dict('records'),
            columns=columns,
            editable=True,
            dropdown=dropdowns,
            style_data_conditional=[{
                'if': {
                    'column_id': col,
                    'filter_query': '{{{0}}} != {{{0}_default}}'.format(col)
                },
                'background_color': EDITED_CELL_COLOR  # or whatever
            } for col in df.columns],
            merge_duplicate_headers=True,
            style_cell={'textAlign': 'center'},
        ),
        html.Div([html.Br() for _ in range(4)]),
        #html.Div('Dummy2 to take space')
    ],
        style={'width': '100%', 'height': '100%', 'overflowX': 'auto'})

    #config_table = html.Div(
    #    config_table,
    #    style={'height': '50vh'}
    #)

    config_component = html.Div([
        number_of_configs_dropdown,
        config_table,
        html.Div(id='config-table-dummy-div'),
        ],
        style={'width': '100%'})
    #config_component = html.Div(
    #    config_component,
    #    style={'height': '100vh'}
    #)

    return(config_component, config_data)




config_component, config_data = get_config_table(lc0)
body = html.Div(
    children=[config_component],
    style={'height': '40%', 'width': '100%'})

html.Div(
    children=[
        #html.Div(children=html.Button('generate data', id='generate-data-button', title='Load pgn to analyze')),
        body,
    ],
    style={'height': '100vh', 'width': '100vw'}
)

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    children=[
        #html.Div(children=html.Button('generate data', id='generate-data-button', title='Load pgn to analyze')),
        body,
    ],
    style={'height': '100vh', 'width': '100vw'}
)


@app.callback(
    Output("config-table-dummy-div", "children"),
    [Input("config-table", "data")],
#    [State("number-of-configs-dropdown", "value")]
)
def copy_table(data):
    data = pd.DataFrame(data)
    has_changed = config_data.update_data(data)
    print('data changed')
    return(dash.no_update)

@app.callback(
    Output("config-table", "data"),
    [Input("number-of-configs-dropdown", "value")]
)
def set_number_of_rows(nr_of_rows):
    print(nr_of_rows)
    data = config_data.data[:nr_of_rows]
    print(data)
    data = data.to_dict('records')
    return(data)

if __name__ == '__main__':
    app.run_server(debug=True)