from position_pane import svg_board_image
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from server import app
from global_data import tree_data_pgn, tree_data_fen, game_data_fen, game_data_pgn
import chess

def node_info(h, w):
    container = html.Div(style={'height': h, 'width': w})
    img = html.Img(id='node-board')
    container.children = [img]
    return(container)


@app.callback(
    Output('node-board', 'src'),
    [Input('graph', 'hoverData'),],
    [State('position-mode-selector', 'value'),
     State('move-table', 'active_cell')])
def update_hover_board(hover_data, position_mode, active_cell):
    #print('HOVER DATA:', hover_data)
    if hover_data is None:
        return(None)
    if position_mode == 'pgn':
        tree_data = tree_data_pgn
        game_data = game_data_pgn
    else:
        tree_data = tree_data_fen
        game_data = game_data_fen

    row = active_cell['row']
    position_id = game_data.get_position_id(row)
    data = tree_data.data[position_id]
    try:
        node_id = hover_data['points'][0]['customdata']
    except KeyError: #we are not hovering over tree node but on bar chart element
        return(None)

    fen = data[node_id]['fen']
    board = chess.Board()
    board.set_fen(fen)
    svg = svg_board_image(board, [], None)
    return(svg)