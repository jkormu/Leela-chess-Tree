# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from plotly import subplots
from datacreate import DataCreator
import base64

RIGHT_TITLE_SIZE = 15
FONT_SIZE = 13
FONT_COLOR = '#7f7f7f'
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
MARKER_SIZE = 4.0
FONT_FAMILY = 'monospace'

app = dash.Dash(__name__)  # ,external_stylesheets=external_stylesheets)

data_creator = DataCreator('', '', [])
data_creator.create_demo_data()


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

        point = node['point']
        x_parent, y_parent = node['parent']
        node_text = node['miniboard']

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

    x_odd, y_odd = zip(*points_odd)
    x_even, y_even = zip(*points_even)
    x_root, y_root = zip(*points_root)

    return (x_odd, y_odd, node_text_odd,
            x_even, y_even, node_text_even,
            x_root, y_root, node_text_root,
            x_edges, y_edges,
            x_edges_pv, y_edges_pv)

#radar_logo = '/home/jusufe/tmp/download.png'
#encode_logo = base64.b64encode(open(radar_logo, 'rb').read()).decode('ascii')

svg_file = '/home/jusufe/tmp/board_img.svg'
encoded = base64.b64encode(open(svg_file,'rb').read())
svg = 'data:image/svg+xml;base64,{}'.format(encoded.decode())

#test_base64 = base64.b64encode(open(testa_pnga, 'rb').read()).decode('ascii')

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Test, test, test...
    '''),
    html.Img(id='board',
             src=svg),#'data:image/svg;base64,{}'.format(encode_logo)),
    dcc.Graph(
        id='graph',
        figure={
            #'data': [
                #{'x': [1, 2, 3], 'y': [4, 3, 2], 'type': 'bar', 'name': 'SF'},
            #    {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
           # ],
            'layout': {
                'title': ''
            }
        }
    ),
    dcc.Slider(
        id='slider1',
        min=0,
        max=1,
        value=0,
        marks={str(i): str(i) for i in range(2)},
        step=None,
        updatemode='drag',
    )
])

@app.callback(
    Output('graph', 'figure'),
    [Input('slider1', 'value')])
def update_data(selected_value):
    data = data_creator.data
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

    x_hist, y_hist = data_creator.data_depth[selected_value]

    trace_depth_histogram = go.Bar(x=y_hist, y=x_hist, orientation='h',
                                   showlegend=False, hoverinfo='none',
                                   marker=dict(color=BAR_COLOR))

    x_range = data_creator.x_range
    y_range = data_creator.y_range
    y_tick_values = data_creator.y_tick_values
    y_tick_labels = data_creator.y_tick_labels

    y_hist_labels = ['0' for _ in range(len(y_tick_labels) - len(y_hist))] + list(map(str, y_hist))
    max_y2_label_len = max(map(len, y_hist_labels))
    print('max_y2_label_len', max_y2_label_len)
    print([max_y2_label_len - len(label) for label in y_hist_labels])
    y2_tick_labels = [label.rjust(max_y2_label_len, ' ') for label in y_hist_labels]

    y2_range = data_creator.y2_range
    print('y2_range', y2_range)
    print('x_hist', x_hist)
    print('y_hist', y_hist)
    print('y2_tick_labels', y2_tick_labels)

    layout = go.Layout(title=dict(text='Leela tree Visualization', x=0.5, xanchor="center"),
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
                       xaxis={'title': 'X - test',
                              'range': x_range,
                              'zeroline': False,
                              'showgrid': False,
                              'domain': [0.0, 0.91]},
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
                       plot_bgcolor=PLOT_BACKGROUND_COLOR
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

    a = """
    figure = {
            'data': traces,
            'layout': dict(
                title='Dash Data Visualization',
                xaxis={'title': 'X - test',
                       'range': x_range,
                       'zeroline': False,
                       'showgrid': False},
                yaxis={'title': 'Y - test',
                       'range': y_range,
                       'title': 'Depth',
                       'ticktext': y_tick_labels,
                       'tickvals': y_tick_values,
                       'zeroline': False,
                       'showgrid': True,
                       'gridcolor': GRID_COLOR},
                hovermode='closest',
            )
        }
    """
    return figure


if __name__ == '__main__':
    app.run_server(debug=True)