from position_pane import svg_board_image
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from server import app
from global_data import tree_data_pgn, tree_data_fen, game_data_fen, game_data_pgn
import chess
import plottools as pt

def node_info(h, w, right, bottom):
    container = html.Div(id='node-board-container', style={'width': w, 'position': 'absolute',
                                'right': right, 'bottom': bottom, 'zIndex': 9999999,
                                #'border': '1px solid black',
                                #'margin': 0, 'padding': 0,
                                #'transform': 'translate(-100%, 0)',
                                })
    img = html.Img(id='node-board')#, style={'border': '1px solid black'})
    container.children = [img]
    return(container)



@app.callback(
    [Output('node-board', 'src'),
     Output('node-board', 'style')],
    [Input('graph', 'hoverData'),],
    [State('position-mode-selector', 'value'),
     State('move-table', 'active_cell'),
     State('slider1', 'value')])
def update_hover_board(hover_data, position_mode, active_cell, slider_value):
    #print('HOVER TRIGGERED')
    #print('HOVER DATA:', hover_data)
    if hover_data is None:
        return(None, None)
    if position_mode == 'pgn':
        tree_data = tree_data_pgn
        game_data = game_data_pgn
    else:
        tree_data = tree_data_fen
        game_data = game_data_fen

    row = active_cell['row']
    position_id = game_data.get_position_id(row)
    if position_id is None:
        return(None, None)
    try:
        data = tree_data.data[position_id]
    except: #when user has clicked node to set position, hover board callback may trigger while the selected position has already been changed
        return(None, None)
    try:
        node_id = hover_data['points'][0]['customdata']
    except KeyError: #we are not hovering over tree node but on bar chart element
        return(None, None)

    #print('node_id', node_id)
    #print('position_id', position_id)
    #print('slider_value', slider_value)
    #print(tree_data.G_dict[position_id][slider_value].nodes)
    #print('--')
    #for G in tree_data.G_dict[0]:
    #    print(G.nodes)

    #if node_id == 'root':
    #    moves = []
    #else:
    moves = pt.get_moves(tree_data.G_dict[position_id][slider_value], node_id)
    board = chess.Board()
    start_fen = game_data.get_value_by_position_id('fen', position_id)
    board = pt.set_board(moves, board, start_fen)


    #fen = data[node_id]['fen']
    move = data[node_id]['move']
    #board = chess.Board()
    #board.set_fen(fen)
    #print('MOOOOOOOOOOOOOOOOOOOOOVEEEEEEEEEEEEEEEE', move)
    #print(move is None)
    #print(type(move))
    if move is not None:
        last_move = chess.Move.from_uci(move)
    else:
        last_move = None
    svg = svg_board_image(board, [], last_move)
    return(svg, {'border': '1px solid black'})