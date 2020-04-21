import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
#from global_data import tree_data_pgn, tree_data_fen, game_data_pgn, game_data_fen, config_data

from server import app

GRID_COLOR = 'rgba(127,127,127, 0.25)'

W_WIN_COLOR = 'rgba(31,119,180, 0.9)'
DRAW_COLOR = 'rgba(255,127,14, 0.9)'
B_WIN_COLOR = 'rgba(0,128,0, 0.9)'
EXPECTED_SCORE_COLOR = 'rgb(0,0,0)'


def pgn_graph_component():
    container = html.Div()
    graph = dcc.Graph(id='pgn-graph',
                      figure={'layout': {'title': ''}},
                      style={'height': '100%', 'width': '100%'},
                      config={'displayModeBar': False},
                      )
    container.children = [graph]
    return(container)


@app.callback(
    Output('pgn-graph', 'figure'),
    [Input('move-table', 'data'),
     ])
def update_pgn_graph(data):
    flip_value = {True: 1, False: -1}
    if data is None or 'W' not in data[0] or 'D' not in data[0] or 'L' not in data[0]:
        return(dash.no_update)
    plys = [row['ply'] for row in data]
    W = [row['W'] for row in data]
    D = [row['D'] for row in data]
    L = [row['L'] for row in data]
    Q = [0.5*(flip_value[row['turn']]*row['Q'] + 1.0)*100 if (row['turn'] is not None and row['Q'] is not None)
         else None for row in data]
    print([row['turn'] for row in data])

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
                             line={'width': 2.0, 'color': EXPECTED_SCORE_COLOR}
                             ))

    layout = go.Layout(
        title='WDL',
        xaxis={'title': 'Ply',
               'zeroline': False,
               'showgrid': False,
               },
        yaxis={'title': 'Probability',
               'range': [0, 100],
               'zeroline': False,
               'showgrid': True,
               'gridcolor': GRID_COLOR},
        legend_orientation="h",
        transition={
            'duration': 500,
            'easing': 'cubic-in-out'
        }
    )

    fig['layout'].update(layout)

    return(fig)