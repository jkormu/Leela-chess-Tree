# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


data = {0: {'x': 0, 'y': 1, 'visible': [0, 1]},
        1: {'x': 1, 'y': 3, 'visible': [0]},
        2: {'x': 2, 'y': 2, 'visible': [0, 1, 2]}}
print(data)
print(data[0]['visible'])

def get_data(data, visible):
    x = [data[i]['x'] for i in data if visible in data[i]['visible']]
    y = [data[i]['x'] for i in data if visible in data[i]['visible']]
    return x, y


body = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2('Blaaa left')
                    ]),
                    dbc.Col(
                        [
                            html.H2('Blalaa right')
                        ]
                    )

            ]
        )
    ]
)


print('fuck this shit')
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
#app.layout = html.Div([body])
app.layout = html.Div([body])

if __name__ == '__main__':
    app.run_server(debug=True)