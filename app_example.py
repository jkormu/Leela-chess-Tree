# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__)  # ,external_stylesheets=external_stylesheets)


data = {0: {'x': 0, 'y': 1, 'visible': [0, 1]},
        1: {'x': 1, 'y': 3, 'visible': [0]},
        2: {'x': 2, 'y': 2, 'visible': [0, 1, 2]}}
print(data)
print(data[0]['visible'])

def get_data(data, visible):
    x = [data[i]['x'] for i in data if visible in data[i]['visible']]
    y = [data[i]['x'] for i in data if visible in data[i]['visible']]
    return x, y

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [1, 2, 3], 'y': [4, 3, 2], 'type': 'bar', 'name': 'SF'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
            ],
            'layout': {
                'title': 'Dash Data Visualization'
            }
        }
    ),
    dcc.Slider(
        id='slider1',
        min=0,
        max=2,
        value=0,
        marks={str(i): str(i) for i in range(3)},
        step=None
    )
])

@app.callback(
    Output('example-graph', 'figure'),
    [Input('slider1', 'value')])
def update_data(selected_value):
    x, y = get_data(data, selected_value)
    figure = {
            'data': [
                {'x': x, 'y': y, 'type': 'bar', 'name': 'SF'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
            ],
            'layout': {
                'title': 'Dash Data Visualization'
            }
        }
    return figure

if __name__ == '__main__':
    app.run_server(debug=True)