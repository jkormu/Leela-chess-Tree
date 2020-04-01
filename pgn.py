# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_table
import dash_html_components as html
import io
import pandas as pd
import chess
import chess.svg
import python_chess_customized_svg as svg
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

import chess.pgn
import base64
from server import app

from data_holders import data_creator, game_data
from dash_table.Format import Format, Symbol, Scheme

from colors import rgb_adjust_saturation

COMPONENT_WIDTH = '98%'
WHITE_WIN_COLOR = 'rgb(255, 255, 255)'
DRAW_COLOR ='rgb(184, 184, 184)'
BLACK_WIN_COLOR = 'rgb(0, 0, 0)'
SELECTED_ROW_COLOR = 'rgba(23,178,207,0.5)'
BAR_LINE_COLOR = 'rgb(100, 100, 100)'
WHITE_WIN_BAR_LINE_COLOR = BAR_LINE_COLOR#'rgb(0, 0, 0)'
DRAW_BAR_LINE_COLOR = BAR_LINE_COLOR#'rgb(0, 0, 0)'
BLACK_WIN_BAR_LINE_COLOR = BAR_LINE_COLOR#'rgb(255, 255, 255)'
BAR_LINE_WIDTH = 1
RELATIVE_HEIGHT_OF_SCORE_BAR = "7.5%"
SHOW_BOARD_COORDINATES = False

ARROW_COLORS = {'p': (23, 178, 207),
                'n': (0, 255, 0),
                'q': (255, 0, 0)}


di = {'ply': [0], 'move': ['-'], 'Q': [0.0], 'W': [0.0], 'D': [0.0], 'L': [0.0]}
df = pd.DataFrame(di)
board = chess.Board()
svg_str = str(svg.board(board, size=400))
svg_byte = svg_str.encode()
encoded = base64.b64encode(svg_byte)
svg_board = 'data:image/svg+xml;base64,{}'.format(encoded.decode())




def get_score_bar_figure(W, D, B):
    W = go.Bar(name='White win-%', y=[''], x=[W],
               orientation='h',
               marker=dict(color=WHITE_WIN_COLOR,
                           line=dict(color=WHITE_WIN_BAR_LINE_COLOR,
                                     width=BAR_LINE_WIDTH)))
               #marker_color=WHITE_WIN_COLOR,)
               #orientation='h')
    D = go.Bar(name='Draw-%', y=[''], x=[D],
               orientation='h',
               marker=dict(color=DRAW_COLOR,
                           line=dict(color=DRAW_BAR_LINE_COLOR,
                                     width=BAR_LINE_WIDTH)))
              # orientation='h')
    B = go.Bar(name='Black win-%', y=[''], x=[B],
               orientation='h',
               marker=dict(color=BLACK_WIN_COLOR,
                           line=dict(color=BLACK_WIN_BAR_LINE_COLOR,
                                     width=BAR_LINE_WIDTH)))
              # orientation='h')
    fig = go.Figure(data=[W, D, B])
    #Change the bar mode
    xaxis = {'range': [0,100],
             #'zeroline': False,
             'showgrid': False,
             #'ticks': 'outside',
             'showticklabels': False}
    fig.update_layout(barmode='stack',
                      showlegend=False,
                      margin={'t': 0, 'b': 0, 'l': 0, 'r': 0},
                      xaxis=xaxis,
                      #height=50,
                      plot_bgcolor='rgb(255, 255, 255)')
    return(fig)

def score_bar():
    fig = get_score_bar_figure(20, 30, 50)

    #the height of the component is set relative to it's width
    #this is achieved by the padding hack from
    #https://stackoverflow.com/questions/8894506/can-i-scale-a-divs-height-proportionally-to-its-width-using-css
    component = dcc.Graph(id='score-bar',
                          figure=fig,
                          style={'width': '100%','height': '100%',
                                 'position': 'absolute', 'left': 0},#{'height': '50px'},#, 'marginTop': '0'},
                          config={'displayModeBar': False}
                          )
    container = html.Div(style={
        'position': 'relative',
        'width': '100%',
        'padding-bottom': RELATIVE_HEIGHT_OF_SCORE_BAR,
        'float': 'left',
        'height': 0})
    container.children = component
    return(container)


def pgn_layout():

    upload = dcc.Upload(
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
        )

    arrow_settings = html.Div(style={'display': 'flex',
                                     'flex-direction': 'row',
                                     'padding': '3px', 'padding-top': '5px'})
    arrow_options = html.Div(children=[html.Label('Arrow type: '),
        dcc.RadioItems(
            id='arrow-type-selector',
            options=[
                {'label': 'Policy-%', 'value': 'p'},
                {'label': 'Visits-%', 'value': 'n'},
                {'label': 'Q-%', 'value': 'q'},
            ],
            value='n',
            labelStyle={'padding-left': '3px'},
            style={'flex': 1}
    )],
                             style={'flex': 1, 'display': 'flex', 'flex-direction': 'row'})
    arrows_input = html.Div(children=[html.Label('#Arrows: '),
                                      dcc.Input(id='nr_of_arrows_input', type="number",
                                                min=0, max=100, step=1,
                                                inputMode='numeric', value=3)])

    arrow_settings.children = [arrow_options, arrows_input]

    img = html.Img(id='board', src=svg_board)
    upload_output = html.Div(id='output-data-upload')

    buttons = html.Div(children=[
        html.Button('Analyze all',
                    id='generate-data-button',
                    title='Load pgn to analyze',
                    style={'flex': '1', 'padding': '5px', 'margin-right': '5px',
                           'margin-top': '8px', 'margin-bottom': '5px'}),
        html.Button('Analyze selected',
                    id='generate-data-selected-button',
                    title='',
                    style={'flex': '1', 'padding': '5px', 'margin-left': '5px',
                           'margin-top': '8px', 'margin-bottom': '5px'})],
    style={'display': 'flex', 'flex-direction': 'row'})

    data_table = dash_table.DataTable(
            id='move-table',
            columns=[{"name": '', "id": 'dummy_left'},
                     {"name": 'ply', "id": 'ply'},
                     {"name": 'move', "id": 'move'},
                     {"name": 'Q', "id": 'Q'},
                     {"name": 'W-%', "id": 'W', 'type': 'numeric', 'format': Format(precision=0, symbol=Symbol.yes, symbol_suffix='%', scheme=Scheme.fixed)},
                     {"name": 'D-%', "id": 'D', 'type': 'numeric', 'format': Format(precision=0, symbol=Symbol.yes, symbol_suffix='%', scheme=Scheme.fixed)},
                     {"name": 'B-%', "id": 'L', 'type': 'numeric', 'format': Format(precision=0, symbol=Symbol.yes, symbol_suffix='%', scheme=Scheme.fixed)},
                     {"name": '', "id": 'dummy_right'}],
            data=df.to_dict('records'),
            fixed_rows={'headers': True, 'data': 0},
            style_cell={'textAlign': 'left', 'minWidth': '5px', 'width': '20px', 'maxWidth': '20px',
                        'whiteSpace': 'normal', 'height': 'auto', 'overflow': 'hidden'},
            # row_selectable='single',
            style_as_list_view=True,
            style_table={'width': '100%', 'margin-left': '0px', 'overflowY': 'auto',
                         'border-left': f'1px solid {BAR_LINE_COLOR}', 'border-top': f'1px solid {BAR_LINE_COLOR}'},  # , 'maxHeight': '300px', 'overflowY': 'scroll'},#'height': '750px'
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
            #css=[{"selector": ".dash-spreadsheet-container", "rule": "accent: #e1e1e1 !important;"}],
            css=[{"selector": "table", "rule": "width: 100%;"},{"selector": ".dash-spreadsheet.dash-freeze-top, .dash-spreadsheet .dash-virtualized", "rule": "max-height: none;"}],

        )
    container_table = html.Div(children=data_table,
    style={'flex': '1', 'overflow': 'auto'})
    container = html.Div(style={'height': '100%', 'width': COMPONENT_WIDTH, 'display': 'flex', 'flex-direction': 'column'})
    content = [upload, arrow_settings, img, score_bar(), upload_output, buttons, container_table]#container_table]
    container.children = content
    return(container)

def parse_pgn(contents, filename):
    if contents is None:
        return(dash.no_update)
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'pgn' in filename:
            # Assume that the user uploaded a pgn file
            first_game = chess.pgn.read_game(io.StringIO(decoded.decode('utf-8')))
        else:
            return('Not a pgn')
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


X = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
Y = ['1', '2', '3', '4', '5', '6', '7', '8']
move_table = {x+y: 8*Y.index(y)+X.index(x) for y in Y for x in X}

def get_arrows(position_index, slider_value, type, nr_of_arrows):
    if nr_of_arrows == 0 or nr_of_arrows is None:
        return([])
    moves, metrics = data_creator.get_best_moves(position_index=position_index,
                                                  slider_value=slider_value,
                                                  type=type,
                                                  max_moves=nr_of_arrows)
    r,g,b = ARROW_COLORS[type]#POLICY_ARROW_COLOR#[23,178,207]#[0, 255, 0]
    if metrics == []:
        return([])
    arrows = []
    best_metric = metrics[0]
    for move, metric in zip(moves, metrics):
        from_square = move[:2]
        to_square = move[2:4]
        tail = move_table[from_square]
        head = move_table[to_square]
        #the worse the move is, the more desaturated the arrow color shall be
        if type != 'q':
            saturation_factor = (metric/best_metric)**0.618
        else:
            saturation_factor = ((1+metric)/(1+best_metric))**1.618
        r,g,b = rgb_adjust_saturation(saturation_factor, r, g, b)
        color = f"rgb({r}, {g}, {b})"#"rgb(0, 255, 0)"#"#FF0000"
        annotation = f'{round(100*metric)}'
        arrow = svg.Arrow(tail, head, color=color, annotation=annotation)
        arrows.append(arrow)
    return(arrows)

@app.callback(
    Output('board', 'src'),
    [Input('move-table', 'active_cell'),
     Input('slider1', 'value'),
     Input('arrow-type-selector', 'value'),
     Input('nr_of_arrows_input', 'value')])
def update_board_imgage(active_cell, slider_value, arrow_type, nr_of_arrows):
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
    arrows = get_arrows(selected_row_ids, slider_value, arrow_type, nr_of_arrows)
    #reverse the order so that better moves are drawn above worse moves
    arrows = arrows[::-1]
    svg_str = str(svg.board(board, size=200, arrows=arrows, lastmove=last_move, coordinates=SHOW_BOARD_COORDINATES))
    svg_str = svg_str.replace('height="200"', 'height="100%"')
    svg_str = svg_str.replace('width="200"', 'width="100%"')
    svg_byte = svg_str.encode()
    encoded = base64.b64encode(svg_byte)
    svg_board = 'data:image/svg+xml;base64,{}'.format(encoded.decode())
    return(svg_board)

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
     Input('generate-data-button', 'title'),
     ],
    [State('move-table', 'active_cell')])
def reset_selected_cells(arg1, arg2, active_cell):
    if active_cell is None:
        active_cell = {'row': 0, 'column': 0}
    selected_cells = [active_cell]
    return(active_cell, selected_cells)

@app.callback([
     Output('generate-data-selected-button', 'disabled'),
     Output('generate-data-selected-button', 'title')],
    [Input('move-table', 'active_cell')])
def set_state_of_analyze_selected_button(active_cell):
    if active_cell is None:
        disabled = True
        title = 'First, select a position to analyze'
    else:
        disabled = False
        title = 'Analyze selected position'
    return(disabled, title)

@app.callback(
    [Output('score-bar', 'figure'),
     Output('score-bar', 'style')],
    [Input('hidden-div-slider-state', 'children'),
     Input('move-table', 'active_cell')])
def update_score_bar(value, active_cell):
    style = {'width': '100%','height': '100%', 'position': 'absolute', 'left': 0, 'visibility': 'visible'}
    print('SLIDER VALUE', value)
    if active_cell is None or game_data.game_data is None or active_cell['row'] not in data_creator.data:#game_data.game_data['ply']:
        style['visibility'] = 'hidden'
        return(dash.no_update, style)

    row = active_cell['row']
    W = game_data.game_data['W'][row]
    D = game_data.game_data['D'][row]
    B = game_data.game_data['L'][row]
    fig = get_score_bar_figure(W, D, B)
    return(fig, style)

#if __name__ == '__main__':
#    app.run_server(debug=True)

