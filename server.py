
import dash_bootstrap_components as dbc
import dash

app = dash.Dash(__name__)#, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config['suppress_callback_exceptions']=True