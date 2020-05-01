import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from global_data import tree_data_pgn, tree_data_fen, game_data_pgn, game_data_fen
from pgn_graphs import empty_figure

from server import app
import time

from colors import custom_color_scale



def heatmap_component():
    container = html.Div(style={#'flex': 1,
                                'display': 'flex',
                                'flexDirection': 'row',
                                'marginTop': '3px'})
    container_left = html.Div(style={'flex': 1,
                                'display': 'flex',
                                'flexDirection': 'column',
                                'marginTop': '3px'})
    container_right = html.Div(style={'flex': 1,
                                #'display': 'flex',
                                #'flexDirection': 'column',
                                'marginTop': '3px'})

    type_selector = dcc.Dropdown(id='heatmap-selector',
                                 options=[
                                     {'label': 'destination square', 'value': 'destination'},
                                     {'label': 'origin square', 'value': 'origin'},
                                     {'label': 'occupied squares', 'value': 'occupied'}
                                     ],
                                 value='destination',
                                 clearable=False,
                                 )

    piece_selector = dcc.Dropdown(id='piece-selector',
                                 options=[
                                     {'label': 'All pieces', 'value': 'all'},
                                     {'label': 'Pawn', 'value': 'p'},
                                     {'label': 'Knight', 'value': 'n'},
                                     {'label': 'Bishop', 'value': 'b'},
                                     {'label': 'Rook', 'value': 'r'},
                                     {'label': 'Queen', 'value': 'q'},
                                     {'label': 'King', 'value': 'k'},
                                     ],
                                 value='all',
                                 clearable=False,
                                 )

    color_selector = dcc.Dropdown(id='color-selector',
                                 options=[
                                     {'label': 'Both players', 'value': 'both'},
                                     {'label': 'White', 'value': 'white'},
                                     {'label': 'Black', 'value': 'black'},
                                     ],
                                 value='both',
                                 clearable=False,
                                 )

    depth_selector = dcc.RangeSlider(
        id='depth-selector',
        min=1,
        max=50,
        pushable=1,
        step=None,
        value=[1, 50],
        marks={i: str(i) if i % 2 == 0 else '' for i in range(51)},
        updatemode='drag'
    )

    #button = html.Button(id='button_for_testing', children=['calc'])
    graph = dcc.Graph(id='heatmap',
                      figure=empty_figure(),
                      config={'displayModeBar': False})
    container_left.children = [html.Label('Heatmap type:'),
                               type_selector,
                               html.Label('Filter by moved piece:', style={'marginTop': '5px'}),
                               piece_selector,
                               html.Label('Filter by player:', style={'marginTop': '5px'}),
                               color_selector,
                               html.Label('Filter by search depth:', style={'marginTop': '5px'}),
                               depth_selector,
                               html.Label(id='depth-filter-info')]

    container_right.children = [graph]

    dummy_spacer = html.Div(style={'flex': 1})
    container.children = [container_left, container_right, dummy_spacer]
    return(container)

@app.callback(
    [Output('depth-selector', 'max'),
     Output('depth-selector', 'value')],
    [Input('move-table', 'active_cell'),
     Input('position-mode-selector', 'value')],
    [State('depth-selector', 'value'),
     State('depth-selector', 'max')])
def update_depth_selector_max(active_cell, position_mode, selected_depths, current_max):
    if active_cell is None or position_mode is None:
        return(dash.no_update, dash.no_update)
    selected_min_depth, selected_max_depth = selected_depths
    if position_mode == 'pgn':
        tree_data = tree_data_pgn
        game_data = game_data_pgn
    else:
        tree_data = tree_data_fen
        game_data = game_data_fen
    position_id = game_data.get_position_id(active_cell['row'])
    try:
        new_max = max(tree_data.y_range[position_id])
    except KeyError:
        return(dash.no_update, dash.no_update)

    if selected_max_depth == current_max or selected_max_depth > new_max:
        selected_max_depth = new_max
    selected_min_depth = min(selected_min_depth, selected_max_depth - 1)

    selected_depths = [selected_min_depth, selected_max_depth]
    return(new_max, selected_depths)

@app.callback(
    Output('depth-filter-info', 'children'),
    [Input('depth-selector', 'value'),
     Input('depth-selector', 'max')])
def update_depth_filter_info_text(depth_filter, max_allowed):
    min_depth, max_depth = depth_filter
    max_depth += -1
    text = ''
    if min_depth == 1 and max_depth == max_allowed - 1:
        text = f'No depth filter applied'
    elif min_depth < max_depth:
        text = f'Depths from {min_depth} to {max_depth}'
    elif min_depth == max_depth:
        text = f'Depth {min_depth} only'
    return(text)

@app.callback(
    Output('heatmap', 'figure'),
    [Input('heatmap-selector', 'value'),
     Input('position-mode-selector', 'value'),
     Input('move-table', 'active_cell'),
     Input('bottom-tabs', 'value'),
     Input('slider1', 'value'),
     Input('color-selector', 'value'),
     Input('piece-selector', 'value'),
     Input('depth-selector', 'value')
     ])
def update_heatmap_old(heatmap_type, position_mode, active_cell, active_tab, slider_value,
                   color_filter, piece_filter, depth_filter):
    depth_filter_min, depth_filter_max = depth_filter
    def key_filter(key):
        if color_filter != 'both' and key[0] != color_filter:
            return(False)
        if piece_filter != 'all' and key[1] != piece_filter:
            return(False)
        if key[2] < depth_filter_min or key[2] >= depth_filter_max:
            return(False)
        return(True)


    if heatmap_type is None or active_tab != 'heatmaps':
        return(empty_figure())

    start = time.time()
    if position_mode == 'pgn':
        tree_data = tree_data_pgn
        game_data = game_data_pgn
    else:
        tree_data = tree_data_fen
        game_data = game_data_fen
    selected_row = active_cell['row']
    position_id = game_data.get_position_id(selected_row)
    #tree_data.calculate_heatmap_helpers(position_id)
    if position_id in tree_data.G_dict:
        try:
            heatmap_data = tree_data.heatmap_data_for_moves[position_id][slider_value]
        except KeyError:
            print('generating heat map data')
            tree_data.calculate_heatmap_helpers(position_id)
        if heatmap_type in ('origin', 'destination'):
            heatmap_data = tree_data.heatmap_data_for_moves[position_id][slider_value]
        else:
            heatmap_data = tree_data.heatmap_data_for_board_states[position_id][slider_value]
    else:
        return(empty_figure())

    print('heatmap data retrieved in', time.time() - start)
    start = time.time()
    Zs = [heatmap_data[key][heatmap_type] for key in heatmap_data if key_filter(key)]
    if Zs != []:
        #print('Zs', Zs)
        flat_Zs = [[element for row in z for element in row] for z in Zs]
        #print('flat', flat_Zs)
        z = list(sum(l) for l in zip(*flat_Zs))
        #print('z', z)
        z = [z[i * 8:(i + 1) * 8] for i in range(8)]
    else:
        z = [[0, 0, 0, 0, 0, 0, 0, 0] for _ in range(8)]
    #print('z', z)
    print('heatmap data processed in', time.time() - start)

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=[0,1,2,3,4,5,6,7],
        y=[0,1,2,3,4,5,6,7],
        colorscale=custom_color_scale,#'Cividis', #'Viridis',#'Cividis',#'Bluered',#'Inferno',#'Viridis',
        xgap=2,
        ygap=2,
        zmin=0,
        ),
    )

    layout = go.Layout(
        autosize=False,
        xaxis={'title': None,
               'range': [-0.5, 7.5],
               'zeroline': False,
               'showgrid': False,
               'scaleanchor':'y',
               'constrain': 'domain',
               'constraintoward': 'right',
               'ticktext': [letter for letter in 'abcdefgh'],
               'tickvals': [0,1,2,3,4,5,6,7]
               },
        yaxis={'title': None,
               'range': [-0.5, 7.5],
               'zeroline': False,
               'showgrid': False,
               'ticktext': [letter for letter in '12345678'],
               'tickvals': [0, 1, 2, 3, 4, 5, 6, 7],
               'constrain': 'domain'
               # 'gridcolor': GRID_COLOR
               },
        margin={'t': 0, 'b': 0, 'r': 0, 'l': 0},
    )

    fig['layout'].update(layout)
    fig['layout']['autosize'] = True
    return(fig)


def destination_origin_figure(heatmap_type, heatmap_data, color_filter, piece_filter, depth_filter):
    depth_filter_min, depth_filter_max = depth_filter
    def key_filter(key):
        if color_filter != 'both' and key[0] != color_filter:
            return(False)
        if piece_filter != 'all' and key[1] != piece_filter:
            return(False)
        if key[2] < depth_filter_min or key[2] >= depth_filter_max:
            return(False)
        return(True)

    start = time.time()

    Zs = [heatmap_data[key][heatmap_type] for key in heatmap_data if key_filter(key)]
    if Zs != []:
        #print('Zs', Zs)
        flat_Zs = [[element for row in z for element in row] for z in Zs]
        #print('flat', flat_Zs)
        z = list(sum(l) for l in zip(*flat_Zs))
        #print('z', z)
        z = [z[i * 8:(i + 1) * 8] for i in range(8)]
    else:
        z = [[0, 0, 0, 0, 0, 0, 0, 0] for _ in range(8)]
    #print('z', z)
    print('heatmap data processed in', time.time() - start)

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=[0,1,2,3,4,5,6,7],
        y=[0,1,2,3,4,5,6,7],
        colorscale='Viridis',#'Cividis',#'Bluered',#'Inferno',#'Viridis',
        xgap=2,
        ygap=2,
        zmin=0,
        ),
    )

    layout = go.Layout(
        autosize=False,
        xaxis={'title': None,
               'range': [-0.5, 7.5],
               'zeroline': False,
               'showgrid': False,
               'scaleanchor':'y',
               'constrain': 'domain',
               'constraintoward': 'right',
               'ticktext': [letter for letter in 'abcdefgh'],
               'tickvals': [0,1,2,3,4,5,6,7]
               },
        yaxis={'title': None,
               'range': [-0.5, 7.5],
               'zeroline': False,
               'showgrid': False,
               'ticktext': [letter for letter in '12345678'],
               'tickvals': [0, 1, 2, 3, 4, 5, 6, 7],
               'constrain': 'domain'
               # 'gridcolor': GRID_COLOR
               },
        margin={'t': 0, 'b': 0, 'r': 0, 'l': 0},
    )

    fig['layout'].update(layout)
    fig['layout']['autosize'] = True
    return(fig)