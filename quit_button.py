from global_data import lc0
from flask import request
import sys
from dash.dependencies import Input, Output
import dash_html_components as html
from server import app
import dash

def get_quit_button():
    quit_button = html.Button(id='quit',
                          children='Quit', style={'borderColor': 'red',
                                                  'padding': '3px',
                                                  'paddingLeft': '10px',
                                                  'paddingRight': '10px',
                                                  'marginBottom': '5px',
                                                  'fontWeight': 'bold',
                                                  'float': 'right'})
    shutdown_signal = html.Div(id="shutdown-signal", style={"display": "none"})
    component = html.Div(children=[quit_button, shutdown_signal])
    return(component)

def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    print('closing lc0 engine')
    lc0.quit()
    print('Shutting down server')
    func()
    print('Exiting python')
    sys.exit(0)

@app.callback(
    [Output("quit", "children"),
     Output("quit", "style")],
    [Input("quit", "n_clicks")],
)
def quit_signal(n_clicks):
    print('N_CLICKS', n_clicks)
    if n_clicks is not None and n_clicks >= 1:
        print("setting shutdown signal")
        return("shutdown complete, you may close the browser tab now",
               {'width': '100%', 'borderColor': 'green', 'padding': '3px',
                'marginBottom': '5px', 'fontWeight': 'bold'})
    return(dash.no_update, dash.no_update)

@app.callback(
    Output("shutdown-signal", "style"),
    [Input("quit", "children")],
)
def quit(text):
    #print('Signal', signal)
    if text is not None and text != 'Quit':
        shutdown()
    return({})