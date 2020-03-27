# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from plotly import subplots
from datacreate import data_creator #DataCreator

import chess.svg
import base64

from pgn import pgn_layout, GameData

from server import app

RIGHT_TITLE_SIZE = 15
FONT_SIZE = 13
FONT_COLOR = '#2a3f5f' #'rgb(50, 50, 50)' #'#7f7f7f'
GRID_COLOR = 'rgba(127,127,127, 0.25)'
PV_COLOR = 'rgb(23,178,207)'
BRANCH_COLORS = ['rgb(31,119,180)', 'rgb(255,127,14)']
PLOT_BACKGROUND_COLOR = 'rgb(255,255,255)'
BAR_COLOR = 'rgb(31,119,180)'
EDGE_COLOR = 'black'
HOVER_LABEL_COLOR = 'white'
ROOT_NODE_COLOR = 'red'
BEST_MOVE_COLOR = 'rgb(178,34,34)'
MOVED_PIECE_COLOR = 'rgb(210,105,30)'
MAX_ALLOWED_NODES = 200000
MARKER_SIZE = 5.0
FONT_FAMILY = 'monospace'
GRAPH_WIDTH = 84
PGN_WIDTH = 100 - GRAPH_WIDTH


#data_creator = DataCreator('', '')
#data_creator.create_demo_data()

#game_data = GameData()


def get_data(data, visible):
    points_odd, node_text_odd = [], []
    points_even, node_text_even = [], []
    points_root, node_text_root = [], []
    x_edges, y_edges = [], []
    x_edges_pv, y_edges_pv = [], []
    for node in data:
        node = data[node]
        node_state_info = node['visible'].get(visible)
        if node_state_info is None: # node is not visible for this state
            continue

        type, edge_type = node_state_info['type']
        node_metrics = node_state_info['metric']

        point = node['point']
        x_parent, y_parent = node['parent']
        node_text = node['miniboard'] + node_metrics

        if type == 'odd':
            points_odd.append(point)
            node_text_odd.append(node_text)
        elif type == 'even':
            points_even.append(point)
            node_text_even.append(node_text)
        elif type == 'root':
            points_root.append(point)
            node_text_root.append(node_text)
        if edge_type == 'pv':
            x_edges_pv += [point[0], x_parent, None]
            y_edges_pv += [point[1], y_parent, None]
        else:
            x_edges += [point[0], x_parent, None]
            y_edges += [point[1], y_parent, None]

    x_odd, y_odd = zip(*points_odd) if points_odd != [] else ([], [])
    x_even, y_even = zip(*points_even) if points_even != [] else ([], [])
    x_root, y_root = zip(*points_root)

    return (x_odd, y_odd, node_text_odd,
            x_even, y_even, node_text_even,
            x_root, y_root, node_text_root,
            x_edges, y_edges,
            x_edges_pv, y_edges_pv)


#svg_str = str(chess.svg.board(data_creator.board, size=300))
#svg_byte = svg_str.encode()
#encoded = base64.b64encode(svg_byte)


#svg = 'data:image/svg+xml;base64,{}'.format(encoded.decode())
#svg = 'data:image/svg+xml;base64,{}'.format(svg_str)
#svg = 'data:image/svg+xml;base64,{}'.format(encoded.decode())

#test_base64 = base64.b64encode(open(testa_pnga, 'rb').read()).decode('ascii')

pgn_component, game_data = pgn_layout('100%')
a = """
body = dbc.Container(fluid=True, children=
    [
        dbc.Row(id='row1', children=
            [
                dbc.Col(id='row1_col2', children=
                        [
                            dcc.Graph(
                                id='graph',
                                figure={
                                    'layout': {'title': ''},
                                }, #style={'height':'100%'}
                            ), html.Div(children=[
                            dcc.Slider(
                                id='slider1',
                                min=0,
                                max=1,
                                value=0,
                                marks={str(i): str(i) for i in range(2)},
                                step=None,
                                updatemode='drag',
                            ), html.Div(id='hidden-div-slider-state', hidden='hidden', children='test')], style={'margin-top': '30px'})
                        ]
                    ),
                dbc.Col(id='row1_col1', md=2, children=
                [
                    pgn_component
                    #html.Img(id='board',
                    #         src=svg)
                ],
                        ),
            ]
        )
    ]
)
"""

body = html.Div(
    children=[html.Div(id='graph-container',
                       children=[dcc.Graph(id='graph',
                                           figure={'layout': {'title': ''}},
                                           style={'height': '100%', 'marginTop': '0'}),
                                 dcc.Slider(id='slider1',
                                            min=0,
                                            max=1,
                                            value=0,
                                            marks={str(i): str(i) for i in range(2)},
                                            step=None,
                                            updatemode='drag'),
                                 html.Div(id='hidden-div-slider-state', hidden='hidden', children='test')
                                 ],
                       style={'height': '100%', 'width': f'{GRAPH_WIDTH}%', 'float': 'left'}
                       ),
              html.Div(id='pgn-container',
                       children=[pgn_component],
                       style={'height': '100%', 'width': f'{PGN_WIDTH}%', 'float': 'right'})
              ],
    style={'height': '60%', 'width': '100%'}
)

app.layout = html.Div(
    children=[
        html.Div(children=html.Button('generate data', id='generate-data-button', title='Load pgn to analyze')),
        body,
],  style={'height': '100vh', 'width': '100vw'}
)

@app.callback(
    Output('generate-data-button', 'children'),
    [Input('generate-data-button', 'n_clicks')],
    [State('slider1', 'marks')]
)
def generate_data(n_clicks, marks):
    #data = pd.DataFrame(data)
    #print('n_clicks', n_clicks)
    if n_clicks is None or n_clicks == 0:
        return(dash.no_update)

    data = game_data.game_data
    if data is None: #game data not yet created, i.e. pgn not provided
        #print('Game data:', data)
        return ("Generate data (pgn not yet loaded)" + str(n_clicks))
    position_indices = data['ply']
    nr_of_plies = len(position_indices )

    net = '/home/jusufe/leelas/graph_analysis3/nets60T/weights_run1_62100.pb.gz'
    engine = '/home/jusufe/lc0_farmers/build/release/lc0'# '/home/jusufe/lc0_test4/build/release/lc0'
    data_creator.args = [engine, '--weights=' + net]
    param1 = ['--cpuct=2.147', '--minibatch-size=1', '--policy-temp-decay=-0.02931', '--policy-softmax-temp=1.30958', '--smart-pruning-factor=0.0', '--threads=1', '--max-collision-events=1', '--max-collision-visits=1']#, '--threads=1', '--max-collision-events=1', '--max-collision-visits=1']
    param2 = ['--cpuct=4.147', '--minibatch-size=1', '--smart-pruning-factor=0.0', '--threads=1', '--max-collision-events=1', '--max-collision-visits=1']#, '--threads=1', '--max-collision-events=1', '--max-collision-visits=1']
    moves = []
    nodes = 200
    test_arguments = [param1, param2]
    board = game_data.board
    data_creator.G_list = {}
    for test_i in range(len(marks)):
        board.set_fen(game_data.fen)
        for position_index in position_indices:
            print('running position', position_index)
            data_creator.run_search(position_index, test_arguments[test_i], board, nodes)
            if position_index < nr_of_plies - 1:
                move = game_data.game_data['move'][position_index + 1]
                board.push_san(move)

    board.set_fen(game_data.fen)
    #data_creator.reset()
    data_creator.data = {}
    for position_index in position_indices:
        fen = board.fen()
        print('CREATING GRAPH FOR', position_index)
        data_creator.create_data(position_index, fen)
        if position_index < nr_of_plies - 1:
            move = game_data.game_data['move'][position_index + 1]
            board.push_san(move)
    return('test'+str(nr_of_plies))

@app.callback(
    Output('graph', 'figure'),
    [Input('slider1', 'value'),
     Input('move-table', 'active_cell')])
def update_data(selected_value, active_cell):
    if active_cell is None:
        position_index = 0
    else:
        position_index = active_cell['row']

    #Show empty graph if position is not yet analyzed
    if position_index not in data_creator.data:
        figure = subplots.make_subplots(rows=1, cols=2,
                                        specs=[[{}, {}]],
                                        shared_xaxes=True,
                                        shared_yaxes=False,
                                        vertical_spacing=0.001)
        layout = go.Layout(
            annotations=[
                dict(
                    x=1.025,
                    y=0.5,
                    showarrow=False,
                    text='Nodes per depth',
                    xref='paper',
                    yref='paper',
                    textangle=90,
                    font=dict(family=FONT_FAMILY, size=RIGHT_TITLE_SIZE, color=FONT_COLOR)
                ),
            ],
            xaxis={'title': 'Visit distribution',
                   'range': [0, 1],
                   'zeroline': False,
                   'showgrid': False,
                   'domain': [0.0, 0.91],
                   'tickvals': [],
                   'ticktext': []},
            yaxis={'title': 'Depth',
                   'range': [-1, 10],
                   'ticktext': [str(i) for i in range(10)],
                   'tickvals': [i for i in range(10)][::-1],
                   'zeroline': False,
                   'showgrid': True,
                   'gridcolor': GRID_COLOR},
            yaxis2={'title': '',
                    'range': [0, 1],
                    'showticklabels': True,
                    'side': 'left',
                    'ticktext': [0],
                    'tickvals': [i for i in range(10)][::-1]},
            xaxis2={'zeroline': False,
                    'showgrid': False,
                    'showticklabels': False,
                    'domain': [0.93, 1.0],
                    'range': [-1, 10]},
            hovermode='closest',
            plot_bgcolor=PLOT_BACKGROUND_COLOR,
            # height=900,
            margin={'t': 0, 'b': 0}
        )
        figure['layout'].update(layout)
        return(figure)
    data = data_creator.data[position_index]
    x_odd, y_odd, node_text_odd, x_even, y_even, node_text_even, x_root, y_root, node_text_root, x_edges, y_edges, x_edges_pv, y_edges_pv = get_data(data, selected_value)

    trace_node_odd = go.Scatter(dict(x=x_odd, y=y_odd),
                                mode='markers',
                                marker={'color': BRANCH_COLORS[1], 'symbol': "circle", 'size': MARKER_SIZE},
                                text=node_text_odd,
                                hoverinfo='text',
                                textfont={"family": FONT_FAMILY},
                                hoverlabel=dict(font=dict(family=FONT_FAMILY, size=15), bgcolor=HOVER_LABEL_COLOR),
                                showlegend=False
                                )
    trace_node_even = go.Scatter(dict(x=x_even, y=y_even),
                                 mode='markers',
                                 marker={'color': BRANCH_COLORS[0], 'symbol': "circle", 'size': MARKER_SIZE},
                                 text=node_text_even,
                                 hoverinfo='text',
                                 textfont={"family": FONT_FAMILY},
                                 hoverlabel=dict(font=dict(family=FONT_FAMILY, size=15), bgcolor=HOVER_LABEL_COLOR),
                                 showlegend=False
                                 )

    trace_node_root = go.Scatter(dict(x=x_root, y=y_root),
                                 mode='markers',
                                 marker={'color': ROOT_NODE_COLOR, 'symbol': "circle", 'size': MARKER_SIZE},
                                 text=node_text_root,
                                 hoverinfo='text',
                                 textfont={"family": FONT_FAMILY},
                                 hoverlabel=dict(font=dict(family=FONT_FAMILY, size=15), bgcolor=HOVER_LABEL_COLOR),
                                 showlegend=False
                                 )

    trace_edge = go.Scatter(dict(x=x_edges, y=y_edges),
                            mode='lines',
                            line=dict(color=EDGE_COLOR, width=0.5),
                            showlegend=False
                            )
    trace_edge_pv = go.Scatter(dict(x=x_edges_pv, y=y_edges_pv),
                               mode='lines',
                               line=dict(color=PV_COLOR, width=1.75),
                               showlegend=False
                               )

    traces = [trace_edge,
              trace_edge_pv,
              trace_node_odd,
              trace_node_even,
              trace_node_root]

    x_hist, y_hist = data_creator.data_depth[position_index][selected_value]

    #print(x_hist, y_hist)

    trace_depth_histogram = go.Bar(x=y_hist, y=x_hist, orientation='h',
                                   showlegend=False, hoverinfo='none',
                                   marker=dict(color=BAR_COLOR))

    x_range = data_creator.x_range[position_index]
    y_range = data_creator.y_range[position_index]
    y_tick_values = data_creator.y_tick_values[position_index]
    y_tick_labels = data_creator.y_tick_labels[position_index]

    y_hist_labels = ['0' for _ in range(len(y_tick_labels) - len(y_hist))] + list(map(str, y_hist))
    max_y2_label_len = max(map(len, y_hist_labels))
    #print('max_y2_label_len', max_y2_label_len)
    #print([max_y2_label_len - len(label) for label in y_hist_labels])
    y2_tick_labels = [label.rjust(max_y2_label_len, ' ') for label in y_hist_labels]

    y2_range = data_creator.y2_range[position_index]
    #print('y2_range', y2_range)
    #print('x_hist', x_hist)
    #print('y_hist', y_hist)
    #print('y2_tick_labels', y2_tick_labels)

    x_tick_labels = data_creator.x_tick_labels[position_index][selected_value]
    x_tick_values = data_creator.x_tick_values[position_index]


    layout = go.Layout(#title=dict(text='Leela tree Visualization', x=0.5, xanchor="center"),
                       annotations=[
                                    dict(
                                        x=1.025,
                                        y=0.5,
                                        showarrow=False,
                                        text='Nodes per depth',
                                        xref='paper',
                                        yref='paper',
                                        textangle=90,
                                        font=dict(family=FONT_FAMILY, size=RIGHT_TITLE_SIZE, color=FONT_COLOR)
                                    ),
                                ],
                       xaxis={'title': 'Visit distribution',
                              'range': x_range,
                              'zeroline': False,
                              'showgrid': False,
                              'domain': [0.0, 0.91],
                              'tickvals': x_tick_values,
                              'ticktext': x_tick_labels},
                       yaxis={'title': 'Depth',
                              'range': y_range,
                              'ticktext': y_tick_labels,
                              'tickvals': y_tick_values,
                              'zeroline': False,
                              'showgrid': True,
                              'gridcolor': GRID_COLOR},
                       yaxis2={'title': '',
                               'range': y_range,
                               'showticklabels': True,
                               'side': 'left',
                               'ticktext': y2_tick_labels,
                               'tickvals': y_tick_values},
                       xaxis2={'zeroline': False,
                               'showgrid': False,
                               'showticklabels': False,
                               'domain': [0.93, 1.0],
                               'range': y2_range},
                       hovermode='closest',
                       plot_bgcolor=PLOT_BACKGROUND_COLOR,
                       #height=900,
        margin={'t': 0, 'b': 0}
                       )
    figure = subplots.make_subplots(rows=1, cols=2,
                                    specs=[[{}, {}]],
                                    shared_xaxes=True,
                                    shared_yaxes=False,
                                    vertical_spacing=0.001)
    for trace in traces:
        figure.append_trace(trace, 1, 1)

    figure.append_trace(trace_depth_histogram, 1, 2)
    figure['layout'].update(layout)

    return(figure)

@app.callback(
    Output('hidden-div-slider-state', 'children'),
    [Input('slider1', 'value'),
     Input('generate-data-button', 'children')])
def update_game_evals(visible, *args):
    Q_values = []
    W_values = []
    D_values = []
    L_values = []
    if game_data.game_data is None:
        return(dash.no_update)
    for position_index in game_data.game_data['ply']:
        root = data_creator.data[position_index]['root']
        evaluation = root['visible'][visible]['eval']
        Q = evaluation['Q']
        W = evaluation['W']
        D = evaluation['D']
        L = evaluation['L']

        #invert W and L for black
        if not game_data.game_data['turn'][position_index]:
            W = 100 - W - D
            L = 100 - L - D
        Q_values.append(Q)
        W_values.append(W)
        D_values.append(D)
        L_values.append(L)
    game_data.game_data['Q'] = Q_values
    game_data.game_data['W'] = W_values
    game_data.game_data['D'] = D_values
    game_data.game_data['L'] = L_values
    return(str(visible))



#if __name__ == '__main__':
#    app.run_server(debug=True)