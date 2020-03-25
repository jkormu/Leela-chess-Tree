# -*- coding: utf-8 -*-
import dash

import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd
import dash_table
from collections import OrderedDict

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

import chess.engine
import chess

EDITED_CELL_COLOR = 'rgb(255,127,14)'

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
        print(value, out, type(value))
    except ValueError:
        out = value
    return out

def create_column(option, df_dict, columns, dropdowns):
    option_type = option.type
    default = option.default
    if option_type == 'check':
        default = str(default)
    default = try_to_round(default, 3)
    name = option.name
    df_dict[name] = [default]
    df_dict[name+'_default'] = [default]
    col = {'id': name, 'name': name, 'clearable': False}
    if option_type == 'combo' or option_type == 'check':
        col['presentation'] = 'dropdown'
        columns.append(col)
        if option_type == 'combo':
            var = option.var
        else:
            var = ('True', 'False')
        dropdown = {'options': [{'label': val, 'value': val} for val in var],
                    'clearable': False}
        dropdowns[name] = dropdown
    #if option_type == 'spin':
    return(df_dict, columns, dropdowns)

df_dict = {}
columns = []
dropdowns = {}
for opt in lc0.options:
    option = lc0.options[opt]
    if opt not in filter_out_options:
        df_dict, columns, dropdowns = create_column(option, df_dict, columns, dropdowns)


df = pd.DataFrame(df_dict)


print(columns)

print(dropdowns)

print(columns)

print(df['LogitQ'])

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


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


#df = pd.DataFrame(OrderedDict([
#    ('climate', ['Sunny', 'Snowy', 'Sunny', 'Rainy']),
#    ('temperature', [13, 43, 50, 30]),
#    ('city', ['NYC', 'Montreal', 'Miami', 'NYC'])
#]))
#
#di = {'climate': ['Sunny'], 'temperature': [20], 'city':['NYC']}
#df = pd.DataFrame(di)


app.layout = html.Div([
    dash_table.DataTable(
        id='config-table',
        data=df.to_dict('records'),
        columns=columns,
            #{'id': col, 'name': col} for col in df.columns if not col.endswith('_default')

        editable=True,
        dropdown=dropdowns,
        style_data_conditional=[{
            'if': {
                'column_id': col,
                'filter_query': '{{{0}}} != {{{0}_default}}'.format(col)
            },
            'background_color': EDITED_CELL_COLOR  # or whatever
        } for col in df.columns]
    ),
    html.Div(id='table-dropdown-container')
])

a = """
app.layout = html.Div([
    dash_table.DataTable(
        id='table-dropdown',
        data=df.to_dict('records'),
        columns=[
            {'id': 'climate', 'name': 'climate', 'presentation': 'dropdown'},
            {'id': 'temperature', 'name': 'temperature'},
            {'id': 'city', 'name': 'city', 'presentation': 'dropdown'},
        ],

        editable=True,
        dropdown={
            'climate': {
                'options': [
                    {'label': i, 'value': i}
                    for i in df['climate'].unique()
                ]
            },
            'city': {
                 'options': [
                    {'label': i, 'value': i}
                    for i in df['city'].unique()
                ]
            }
        }
    ),
    html.Div(id='table-dropdown-container')
])
"""

if __name__ == '__main__':
    app.run_server(debug=True)