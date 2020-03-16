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

import chess.pgn
import base64
di = {'ply': [0], 'move': ['-'], 'Q': [0.0]}
df = pd.DataFrame(di)
board = chess.Board()
svg_str = str(chess.svg.board(board, size=400))
svg_byte = svg_str.encode()
encoded = base64.b64encode(svg_byte)
svg = 'data:image/svg+xml;base64,{}'.format(encoded.decode())


SELECTED_ROW_COLOR = 'rgb(23,178,207)'

class GameData:
    def __init__(self):
        self.board = chess.Board()
        self.game_data = None

game_data = GameData()

layout = html.Div([
    dcc.Upload(
        id='upload-pgn',
        children=html.Div([
            'Drag and Drop pgn file or ',
            html.A('Select File')
        ]),
        style={
            #'width': '80%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            #'margin': '10px'
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
        columns=[{"name": 'ply', "id": 'ply'},
                 {"name": 'move', "id": 'move'},
                 {"name": 'Q', "id": 'Q'}],#[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        style_cell={'textAlign': 'left', 'minWidth': '0px', 'width':'30px', 'maxWidth': '30px', 'whiteSpace': 'normal', 'height': 'auto', 'overflow': 'hidden'},
        #row_selectable='single',
        style_as_list_view=True,
        style_table={'width': '85%', 'margin-left':'30px'},#, 'maxHeight': '300px', 'overflowY': 'scroll'},#
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }],
        style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
#css= [{ 'selector': 'td.cell--selected, td.focused',
#       'rule': 'background-color: #6464f8 !important;'},
#      { 'selector': 'td.cell--selected *, td.focused *',
#        'rule': 'color: #3C3C3C !important;'},
#      {'selector': 'td.cell--selected *, td.focused *',
#       'rule': 'accent: #6464f8 !important;'}
#      ]
)], style={'width': '100%', 'margin-right': 'auto', 'margin-top': '10px',
           'max-height': '500px', 'overflowY': 'scroll'}) #'overflowY': 'scroll'
], style={'width': '400px'})#'borderStyle': 'dashed'

def parse_pgn(contents, filename):#, date):
    if contents is None:
        dummy = {'ply': [0], 'move': ['-']}
        return(pd.DataFrame(dummy).to_dict('records'))
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
            return(None)#f'{filename} is not a pgn file')
    except Exception as e:
        print(e)
        return('There was an error processing this file.')

    data = {'ply': [0], 'move': ['-']}
    board = first_game.board()
    game_data.board = board
    for ply, move in enumerate(first_game.mainline_moves()):
        san = board.san(move)
        data['move'].append(san)
        data['ply'].append(ply + 1)
        #data['Q'] = 0.0
        board.push(move)

    data = pd.DataFrame(data)
    game_data.game_data = data
    return(data.to_dict('records'))
    #return(' '.join(data['move']))

    #return(first_game.headers["White"])
    #return html.Div([
    #    html.H5(filename),
    #    html.H6(datetime.datetime.fromtimestamp(date)),
    #    html.Div(first_game.headers["White"]),
    #    #dash_table.DataTable(
    #    #    data=df.to_dict('records'),
    #    #    columns=[{'name': i, 'id': i} for i in df.columns]
    #    #),
#
#        html.Hr(),  # horizontal line
#
#        # For debugging, display the raw contents provided by the web browser
#        html.Div('Raw Content'),
#        html.Pre(contents[0:200] + '...', style={
#            'whiteSpace': 'pre-wrap',
#            'wordBreak': 'break-all'
#        })
#    ])


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, '/home/jusufe/PycharmProjects/leela-tree-dash/assets/custom.css'])

app.layout = layout #html.Div(children=[html.Div(children='''Test, test, test...''')])


@app.callback(
    Output('move-table', 'style_data_conditional'),
    [Input('move-table', 'active_cell'),])
def row_highlight_test(active_cell):
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
def update_board_imgage2(active_cell):
    game_data.board.reset()
    board = game_data.board
    print(active_cell)
    if active_cell is None:
        selected_row_ids = 0
    else:
        selected_row_ids = active_cell['row']

    last_move = None
    for i in range(1, selected_row_ids + 1):
        move = game_data.game_data['move'][i]
        last_move = board.push_san(move)
    svg_str = str(chess.svg.board(board, size=400, lastmove=last_move))
    svg_byte = svg_str.encode()
    encoded = base64.b64encode(svg_byte)
    svg = 'data:image/svg+xml;base64,{}'.format(encoded.decode())
    return(svg)

a="""
@app.callback(
    Output('board', 'src'),
    [Input('move-table', 'selected_rows'),])
def update_board_imgage(selected_row_ids):
    game_data.board.reset()
    board = game_data.board
    print(selected_row_ids)
    if selected_row_ids is None:
        selected_row_ids = 0
    else:
        selected_row_ids = selected_row_ids[0]

    last_move = None
    for i in range(1, selected_row_ids + 1):
        move = game_data.game_data['move'][i]
        last_move = board.push_san(move)
    svg_str = str(chess.svg.board(board, size=400, lastmove=last_move))
    svg_byte = svg_str.encode()
    encoded = base64.b64encode(svg_byte)
    svg = 'data:image/svg+xml;base64,{}'.format(encoded.decode())
    return(svg)
"""

@app.callback(
    #Output('output-data-upload', 'children'),
    Output('move-table', 'data'),
    [Input('upload-pgn', 'contents')],
    [State('upload-pgn', 'filename')]
)
def update(content, filename):
    return(parse_pgn(content, filename))

if __name__ == '__main__':
    app.run_server(debug=True)

