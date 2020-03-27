# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_table
import dash_html_components as html
import io
import pandas as pd
import chess
import chess.svg
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import chess.pgn
import base64
from server import app

from datacreate import data_creator

SELECTED_ROW_COLOR = 'rgba(23,178,207,0.5)'

di = {'ply': [0], 'move': ['-'], 'Q': [0.0], 'W': [0.0], 'D': [0.0], 'L': [0.0]}
df = pd.DataFrame(di)
board = chess.Board()
svg_str = str(chess.svg.board(board, size=400))
svg_byte = svg_str.encode()
encoded = base64.b64encode(svg_byte)
svg = 'data:image/svg+xml;base64,{}'.format(encoded.decode())



class GameData:
    def __init__(self):
        self.board = chess.Board()
        self.game_data = None#{'ply': [0], 'move': ['-']}
        self.fen = self.board.fen()

def pgn_layout(width):
    #define global variable holding the game data accessible by the callbacks
    global game_data
    game_data = GameData()

    layout = html.Div([
        dcc.Upload(
            id='upload-pgn',
            children=html.Div([
                'Drag and Drop pgn file or ',
                html.A('Select File')
            ]),
            style={
                # 'width': '80%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                # 'margin': '10px'
            },
            # Only one pgn allowed
            multiple=False
        ),
        html.Img(id='board',
                 src=svg),
        html.Div(id='output-data-upload'),
        html.Div(id='test', children=
        [dash_table.DataTable(
            id='move-table',
            columns=[{"name": '', "id": 'dummy_left'},
                     {"name": 'ply', "id": 'ply'},
                     {"name": 'move', "id": 'move'},
                     {"name": 'Q', "id": 'Q'},
                     {"name": 'W-%', "id": 'W'},
                     {"name": 'D-%', "id": 'D'},
                     {"name": 'B-%', "id": 'L'},
                     {"name": '', "id": 'dummy_right'}],
            data=df.to_dict('records'),
            fixed_rows={'headers': True, 'data': 0},
            style_cell={'textAlign': 'left', 'minWidth': '5px', 'width': '20px', 'maxWidth': '20px',
                        'whiteSpace': 'normal', 'height': 'auto', 'overflow': 'hidden'},
            # row_selectable='single',
            style_as_list_view=True,
            style_table={'width': '100%', 'margin-left': '0px', 'overflowY': 'auto'},  # , 'maxHeight': '300px', 'overflowY': 'scroll'},#
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }],
            style_cell_conditional=[
                {
                    'if': {'column_id': 'Q'},
                    'textAlign': 'right'
                },
                {
                    'if': {'column_id': 'W'},
                    'textAlign': 'right'
                },
                {
                    'if': {'column_id': 'D'},
                    'textAlign': 'right'
                },
                {
                    'if': {'column_id': 'L'},
                    'textAlign': 'right'
                }
            ],
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            css=[{"selector": ".dash-spreadsheet-container", "rule": "accent: #e1e1e1 !important;"}],

        )], style={'width': '100%', 'margin-right': 'auto', 'margin-top': '10px',
                   'max-height': '100%'})#, 'overflowY': 'scroll'})#
    ], style={'width': width})
    return(layout, game_data)

def parse_pgn(contents, filename):#, date):
    #active_cell = {'row': 0, 'column': 0}
    #selected_cells = [active_cell]
    if contents is None:
        return(dash.no_update)
        #dummy = {'ply': [0], 'move': ['-']}
        #return(pd.DataFrame(dummy).to_dict('records'), dash.no_update)
        #return('waiting for content')
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'pgn' in filename:
            # Assume that the user uploaded a pgn file
            first_game = chess.pgn.read_game(io.StringIO(decoded.decode('utf-8')))

            #df = pd.read_csv(
            #    io.StringIO(decoded.decode('utf-8')))
        else:
            #raise PreventUpdate
            return('Not a pgn')
            #return(None)#f'{filename} is not a pgn file')
    except Exception as e:
        print(e)
        return('Upload failed')

    board = first_game.board()
    fen = board.fen()
    game_data.board = board
    data = {'dummy_left': '', 'ply': [0], 'move': ['-'], 'turn': [board.turn], 'dummy_right': ''}
    for ply, move in enumerate(first_game.mainline_moves()):
        san = board.san(move)
        uci = board.uci(move).lower()
        data['move'].append(san)
        data['ply'].append(ply + 1)
        data['turn'].append(board.turn)
        #data['move'].append(uci)
        board.push(move)

    data = pd.DataFrame(data)
    print('parsing done, setting game_data')
    print(data)
    game_data.game_data = data
    game_data.fen = fen

    game_info = f'**File**: {filename}\n'
    game_info += f'**White**: {first_game.headers.get("White", "?")}\n'
    game_info += f'**Black**: {first_game.headers.get("Black", "?")}'
    game_info = dcc.Markdown(game_info, style={"white-space": "pre"})

    #reset analysis of previous pgn
    data_creator.reset_data()
    return(game_info)


#app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, '/home/jusufe/PycharmProjects/leela-tree-dash/assets/custom.css'])

#app.layout = pgn_layout('500px')#layout

@app.callback(
    Output('move-table', 'style_data_conditional'),
    [Input('move-table', 'active_cell'),])
def row_highlight(active_cell):
    style_data_conditional=[
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(248, 248, 248)'
        }
    ]

    if active_cell is None:
        return style_data_conditional

    ind = active_cell['row']
    highligh = {
            'if': {'row_index': ind},
            'backgroundColor': SELECTED_ROW_COLOR
        }
    style_data_conditional.append(highligh)
    return(style_data_conditional)

@app.callback(
    Output('board', 'src'),
    [Input('move-table', 'active_cell'),])
def update_board_imgage(active_cell):
    game_data.board.set_fen(game_data.fen)#reset()
    board = game_data.board
    if active_cell is None:
        selected_row_ids = 0
    else:
        selected_row_ids = active_cell['row']

    last_move = None
    for i in range(1, selected_row_ids + 1):
        move = game_data.game_data['move'][i]
        last_move = board.push_san(move)
    svg_str = str(chess.svg.board(board, size=200, lastmove=last_move))
    svg_str = svg_str.replace('height="200"', 'height="100%"')
    svg_str = svg_str.replace('width="200"', 'width="100%"')
    svg_byte = svg_str.encode()
    encoded = base64.b64encode(svg_byte)
    svg = 'data:image/svg+xml;base64,{}'.format(encoded.decode())
    return(svg)

#@app.callback(
#    [Output('move-table', 'data'),
#     Output('move-table', 'active_cell'),
#     Output('move-table', 'selected_cells')],
#    [Input('upload-pgn', 'contents')],
#    [State('upload-pgn', 'filename')]
#)
@app.callback(
    #Output('move-table', 'data'),
     Output('output-data-upload', 'children'),
    [Input('upload-pgn', 'contents')],
    [State('upload-pgn', 'filename')]
)
def update_pgn(content, filename):
    return(parse_pgn(content, filename))

@app.callback(
    Output('move-table', 'data'),
    [Input('output-data-upload', 'children'),
     #Input('generate-data-button', 'children'),
     Input('hidden-div-slider-state', 'children')],
)
def update_datatable(text, *args):
    if text is None:
        dummy = {'ply': [0], 'move': ['-']}
        return(pd.DataFrame(dummy).to_dict('records'))
    data = game_data.game_data
    return(data.to_dict('records'))

@app.callback([
     Output('move-table', 'active_cell'),
     Output('move-table', 'selected_cells')],
    [Input('upload-pgn', 'contents'),
     Input('generate-data-button', 'children')])
def reset_selected_cells(*args):
    active_cell = {'row': 0, 'column': 0}
    selected_cells = [active_cell]
    return(active_cell, selected_cells)

#if __name__ == '__main__':
#    app.run_server(debug=True)

