import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
#from global_data import tree_data_pgn, tree_data_fen, game_data_pgn, game_data_fen, config_data

from server import app

GRID_COLOR = 'rgba(127,127,127, 0.25)'
PLOT_BACKGROUND_COLOR = 'rgb(255,255,255)'

W_WIN_COLOR = 'rgba(31,119,180, 0.5)'
DRAW_COLOR = 'rgba(255,127,14, 0.5)'
B_WIN_COLOR = 'rgba(0,128,0, 0.5)'
EXPECTED_SCORE_COLOR = 'rgb(0,0,0)'
EXPECTED_SCORE_COLOR_LINE_WIDTH = 1.5


def empty_figure():
    fig = go.Figure()
    layout = go.Layout(
        xaxis={'title': '',
               'zeroline': False,
               'showgrid': False,
               'showticklabels': False,
               },
        yaxis={'title': '',
               'zeroline': False,
               'showgrid': False,
               'showticklabels': False,
               },
        plot_bgcolor=PLOT_BACKGROUND_COLOR,
        margin={'t': 0, 'b': 0, 'l': 0, 'r': 0}
    )
    fig['layout'].update(layout)
    return(fig)

def pgn_graph_component():
    container = html.Div(style={'flex': 1, 'display': 'flex', 'flexDirection': 'column'})
    type_selector = dcc.Dropdown(id='pgn-graph-selector',
                                 options=[
                                     {'label': 'WDL', 'value': 'WDL'},
                                     {'label': 'ML', 'value': 'ML'},
                                     ],
                                 value='WDL',
                                 #style={'height': '10%'}
                                 )
    graph = dcc.Graph(id='pgn-graph',
                      figure=empty_figure(),
                      style={'flex': 1,
                             #'height':'90%',
                             'width': '100%',
                             'margin': '0',
                             'padding': '0',
                             #'marginTop': '0', 'marginBottom': '0',
                             },#'height': '80%'
                      config={'displayModeBar': False},
                      )
    container.children = [type_selector, graph]
    return(container)

def WDL_graph(data):
    flip_value = {True: 1, False: -1}
    if data is None or 'W' not in data[0] or 'D' not in data[0] or 'L' not in data[0]:
        return(empty_figure())
    plys = [row['ply'] for row in data]
    W = [row['W'] for row in data]
    D = [row['D'] for row in data]
    L = [row['L'] for row in data]
    Q = [0.5*(flip_value[row['turn']]*row['Q'] + 1.0)*100 if (row['turn'] is not None and row['Q'] is not None)
         else None for row in data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plys, y=L, fill='tozeroy', mode='none',
                             name='Black win-%', stackgroup='one',
                             fillcolor=B_WIN_COLOR,
                             #line={'width': 0.0, 'color': B_WIN_COLOR}
                             )
                  )
    fig.add_trace(go.Scatter(x=plys, y=D, fill='tonexty', mode='none',
                             name='Draw-%', stackgroup='one',
                             fillcolor=DRAW_COLOR,
                             #line={'width': 0.0, 'color': DRAW_COLOR}
                             )
                  )
    fig.add_trace(go.Scatter(x=plys, y=W, fill='tonexty', mode='none',
                             name='White win-%', stackgroup='one',
                             fillcolor=W_WIN_COLOR,
                             line={'width': 0.0, 'color': W_WIN_COLOR}
                             )
                  )
    fig.add_trace(go.Scatter(x=plys, y=Q, mode='lines',
                             name="White's expected score",
                             line={'width': EXPECTED_SCORE_COLOR_LINE_WIDTH, 'color': EXPECTED_SCORE_COLOR}
                             ))

    layout = go.Layout(
        xaxis={'title': 'Ply',
               'zeroline': False,
               'showgrid': False,
               },
        yaxis={'title': 'Probability',
               'range': [0, 100],
               'zeroline': False,
               'showgrid': True,
               'gridcolor': GRID_COLOR},
        margin={'t': 0, 'b': 0, 'l': 0, 'r': 0},
        legend_orientation="h",
        hovermode="x",
        transition={
            'duration': 500,
            'easing': 'cubic-in-out'
        }
    )

    fig['layout'].update(layout)

    return(fig)

def ML_graph(data):
    if 'M' not in data[0]:
        return(empty_figure())
    plys = [row['ply'] for row in data]
    ML = [row['M'] for row in data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plys, y=ML, #fill='tozeroy', mode='none',
                             name='ML',
                             #line={'width': 0.0, 'color': B_WIN_COLOR}
                             )
                  )

    layout = go.Layout(
        xaxis={'title': 'Ply',
               'zeroline': False,
               'showgrid': False,
               },
        yaxis={'title': 'Predicted half moves left',
               #'range': [0, 100],
               'zeroline': False,
               'showgrid': True,
               'gridcolor': GRID_COLOR},
        margin={'t': 0, 'b': 0,
                #'l': 0, 'r': 0
                },
        legend_orientation="h",
        hovermode="x",
        transition={
            'duration': 500,
            'easing': 'cubic-in-out'
        }
    )

    fig['layout'].update(layout)

    return(fig)

@app.callback(
    Output('pgn-graph', 'figure'),
    [Input('move-table', 'data'),
     Input('position-mode-selector', 'value'),
     Input('pgn-graph-selector', 'value')
     ])
def update_pgn_graph(data, position_mode, graph_type):
    fig = empty_figure()
    if position_mode != 'pgn' or data is None or position_mode is None or graph_type is None:
        return(fig)
    if graph_type == 'WDL':
        fig = WDL_graph(data)
    elif graph_type == 'ML':
        fig = ML_graph(data)
    return(fig)