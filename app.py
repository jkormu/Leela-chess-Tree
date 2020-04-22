# -*- coding: utf-8 -*-

from config_table import config_table
from position_pane import position_pane
from server import app
import dash_html_components as html
from graph import tree_graph
import dash_core_components as dcc
from pgn_graphs import pgn_graph_component
from node_info import node_info

DEBUG = False

if DEBUG:
    APP_CONTAINER_BG = 'rgba(116, 153, 46, 0.2)' #ugly green
    LEFT_CONTAINER_BG = 'rgba(46, 148, 153, 0.2)' #teal
    RIGHT_CONTAINER_BG = 'rgba(212, 57, 181, 0.2)' #pink
    GRAPH_CONTAINER_BG = 'rgba(212, 163, 57, 0.7)' #orange-brown
    CONFIG_CONTAINER_BG = 'rgba(57, 106, 212, 0.2)'  #blue
else:
    WHITE = 'rgb(255, 255, 255)'
    APP_CONTAINER_BG = WHITE
    LEFT_CONTAINER_BG = WHITE
    RIGHT_CONTAINER_BG = WHITE
    GRAPH_CONTAINER_BG = WHITE
    CONFIG_CONTAINER_BG = WHITE
LEFT_PANE_WIDTH = 80
RIGHT_PANE_WIDTH = 100 - LEFT_PANE_WIDTH
GRAPH_PANE_HEIGHT = 60
CONFIG_PANE_HEIGHT = 100 - GRAPH_PANE_HEIGHT


position_component = position_pane()
config_component = config_table()
graph_component = tree_graph()

#    layout
#------------|-----|
#    tree    |board|
#    plot    | and |
#------------| pos |
# engine conf|list |
#------------|-----|
left_container = html.Div(
    style={'height': '100%', 'width': f'{LEFT_PANE_WIDTH}%', 'backgroundColor': LEFT_CONTAINER_BG}
)

graph_container = html.Div(
    style={'height': f'{GRAPH_PANE_HEIGHT}%', 'width': '100%', 'backgroundColor': GRAPH_CONTAINER_BG}
)



config_container = html.Div(
    style={'height': '100%', 'width': '100%', 'backgroundColor': CONFIG_CONTAINER_BG,
           'display': 'flex', 'flexDirection': 'column', 'flex': 1}

)

graph_container.children = [graph_component]
config_container.children = [config_component]

tab_style = {
    #'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '6px'
}

bottom_tabs = dcc.Tabs(id='bottom-tabs',
    children=[
    dcc.Tab(label='Lc0 settings',
            children=[config_container],
            style=tab_style,
            selected_style=tab_selected_style,
            value='configurations'
            ),
    dcc.Tab(label='pgn graphs',
            children=[pgn_graph_component(),
                      ],
            style=tab_style,
            selected_style=tab_selected_style,
            value='pgn-graphs'
            )
],
    content_style={'width': '100%', 'height': '100%', 'display': 'flex', 'flexDirection': 'column', 'flex': 1},
    parent_style={'width': '100%', 'height': f'{CONFIG_PANE_HEIGHT}%', 'display': 'flex', 'flexDirection': 'column'},
    style={'height': '30px'},
    value='configurations')


left_container.children = [node_info('150px', '150px'), graph_container, bottom_tabs]

right_container = html.Div(
    style={'height': '100%', 'width': f'{RIGHT_PANE_WIDTH}%', 'backgroundColor': RIGHT_CONTAINER_BG,
           'paddingLeft': 5, 'boxSizing': 'border-box'
           }
)

right_container.children = [position_component]


layout = html.Div(children=[
    left_container,
    right_container,
],
    style={'height': '100vh', 'width': '100vw', 'backgroundColor': APP_CONTAINER_BG,
           'display': 'flex', 'flexDirection': 'row', 'alignItems:': 'flex-end', 'overflow': 'auto'})


app.layout = layout

