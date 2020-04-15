# -*- coding: utf-8 -*-

from config_table import config_table
from position_pane import position_pane
from server import app
import dash_html_components as html
from graph import tree_graph

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
    style={'height': f'{CONFIG_PANE_HEIGHT}%', 'width': '100%', 'backgroundColor': CONFIG_CONTAINER_BG,
           'display': 'flex', 'flexDirection': 'column'}
)

graph_container.children = [graph_component]
config_container.children = [config_component]

left_container.children = [graph_container, config_container]

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

