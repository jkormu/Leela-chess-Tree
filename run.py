from app import app
import webbrowser

if __name__ == '__main__':
    #webbrowser.open_new_tab("http://localhost:8050")
    app.run_server(debug=True, threaded=False)