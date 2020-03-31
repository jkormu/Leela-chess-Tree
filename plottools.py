import networkx as nx
from networkx.algorithms.dag import topological_sort
import plotly as py
from plotly import tools
import plotly.graph_objs as go
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import chess
from graphtools import *
import time
import numpy as np
from buchheim import buchheim
from lc0tools import *
import os

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

def extract_pos(tree, pos):
    pos[tree.node][0] = tree.x
    pos[tree.node][1] = -tree.y
    for child in tree.children:
        extract_pos(child, pos)

def get_pos(G):
    node = get_root(G)
    pos = {n:[None, None] for n in G.nodes}
    start = time.time()
    tree = buchheim(G, node)
    extract_pos(tree, pos)
    #normalize x,y coords to interval [0,1]
    x_list,y_list = list(zip(*list(pos.values())))
    max_x, max_y = max(x_list), max(y_list)
    min_x, min_y = min(x_list), min(y_list)
    if min_x != max_x and min_y != max_y:
        for n in pos:
            x,y = pos[n]
            pos[n] = ((x-min_x)/(max_x-min_x), (y-min_y)/(max_y-min_y))
    print('Layout algorithm excecuted in:', time.time() - start, 's')
    return(pos)

def adjust_y(pos):
    y = [pos[k][1] for k in pos.keys()]
    set_y = list(set(y))
    set_y.sort()
    for k in pos:
        pos[k] = (pos[k][0],set_y.index(pos[k][1]))
    return(pos)


#def get_branch_parity(G):
#    root = get_root(G)
#    root_children = get_children(G, root)
#    root_children = list(root_children)
#    roo

def pos_separation(G, pos):
    #separates node coordinates into branches for coloring purposes (adjacent branches use different colors)
    
    #finds the ancestor node on depth 1, i.e. the root node of this branch
    #if node is root, then root is returned
    def get_branch(node):
        if is_root(G, node):
            return(node)
        
        while not is_root(G, get_parent(G, node)):
            node = get_parent(G, node)
        return(node)
    
    root = get_root(G)
    root_children = get_children(G, root)

    branches = {child:{} for child in root_children}
    branches[root] = {}
    
    #divide pos into branches
    for n in pos:
        branch = get_branch(n)
        branches[branch][n] = pos[n]
    
    branch_list = list(branches)
    pos_list = [branches[b] for b in branch_list]
    
    def sort_key(b):
        node = get_branch(list(b)[0])
        if is_root(G, node):
            return(-9999999)
        else:
            return(b[node][0])
    
    pos_list.sort(key = sort_key)
    return(pos_list)

def get_moves(G, n):
    #list of moves that lead to this node
    moves = []
    move = G.nodes[n]['move']
    while move != "":
        moves.append(move)
        n = get_parent(G, n)
        move = G.nodes[n]['move']
    return(moves[::-1])

def set_board(moves, board, init_moves):
    board.reset()
    #print('fen', init_moves)
    if type(init_moves)==str:
        board.set_fen(init_moves)
    else:
        for m in init_moves:
            board.push_uci(m.lower())
    for m in moves:
        board.push_uci(m)
    return(board)

def get_miniboard_unicode(G, node, board, init_moves):
    moves = get_moves(G,node)
    board = set_board(moves, board, init_moves)
    COLOR_START = '<a href="" style="color: ' + MOVED_PIECE_COLOR + '">'
    COLOR_END = '</a>'
    board_uni = board.unicode()
    if not moves:
        to_move = (['Black to move', 'White to move'][board.turn])
        return board_uni + '\n' + to_move
    board.pop()
    board_parent_uni = board.unicode()
    new_board = ''
    for i in range(127):
        p0 = board_uni[i]
        if p0 != board_parent_uni[i]:
            p0 = COLOR_START + p0 + COLOR_END
        new_board += p0
    return(new_board)

def get_xy(G, pos, show_miniboard, init_moves):
    pos_keys = pos.keys()
    xy = [pos[k] for k in pos_keys]
    x,y = zip(*xy)
    board = chess.Board()

    def generate_text(node):
        t = ''
        if show_miniboard:
        	t += get_miniboard_unicode(G, node, board, init_moves) + '\n'
        t += 'Move: ' + G.nodes[node]['move']  + '\n'
        t += 'N: ' + G.nodes[node]['N']  + '\n'
        t += 'Q: ' + G.nodes[node]['Q']  + '\n'
        try:
            t += 'D: ' + G.nodes[node]['D']  + '\n'
        except:
            pass
        t += 'P: ' + G.nodes[node]['P']  + '\n'
        return(t)
    text = [generate_text(node) for node in pos_keys]
    text = [t.replace('\n','<br>') for t in text]
    return(x,y,text)

def get_best_edge(G, edges):
        maxN = max([int(G.nodes[e[1]]['N']) for e in edges])
        edges = [e for e in edges if int(G.nodes[e[1]]['N']) == maxN]
        edge = max(edges, key=lambda e: float(G.nodes[e[1]]['Q']))
        return(edge)

#for Dash implementation
def get_WDL(q,d, precision = 5):
    if d is None:
        return(round(100*(0.5*(1+q)), precision), None, round(100*(0.5*(1-q))))
    l = 0.5*(1-q-d)
    w = 0.5*(1+q-d)
    w = round(100* w, precision)
    l = round(100 * l, precision)
    d = round(100 * d, precision)
    return(w,d,l)

#for Dash implementation
def get_node_eval(G, node):
    Q = G.nodes[node]['Q']
    D = G.nodes[node]['D'] if 'D' in G.nodes[node] else None
    M = G.nodes[node]['M'] if 'M' in G.nodes[node] else None

    W, D, L = get_WDL(float(Q), float(D))

    #if node == 'root':
    Q = str(round(-1.0*float(Q), 3))
    return({'Q': Q, 'W': W, 'D': D, 'L': L, 'M': M})

#for Dash implementation
def get_node_metric_text(G, node):
    t = '\n \n'
    t += 'Move: ' + G.nodes[node]['move'] + '\n'
    t += 'N: ' + G.nodes[node]['N'] + '\n'
    if node == 'root':
        Q = str(-1.0*float(G.nodes[node]['Q']))
    else:
        Q = G.nodes[node]['Q']
    t += 'Q: ' + Q + '\n'
    try:
        t += 'D: ' + G.nodes[node]['D'] + '\n'
    except:
        pass
    try:
        t += 'M: ' + G.nodes[node]['M'] + '\n'
    except:
        pass
    t += 'P: ' + G.nodes[node]['P'] + '\n'
    t = t.replace('\n', '<br>')
    return(t)

#for Dash implementation
def get_pv_nodes(G):
    node = get_root(G)
    i = 0
    pv_nodes = []
    if len(G.edges()) == 0:
        return(pv_nodes)
    while True:
        edges = G.out_edges(node)
        if edges == []:
            break
        best_edge = get_best_edge(G, edges)
        node = best_edge[1]
        pv_nodes.append(node)
        if G.out_degree(node) == 0:
            break
    return(pv_nodes)

def get_edge_xy(G, pos):  
    def get_pv(root):
        node = root
        sides = [1.0,-1.0]
        i = 0
        path = []
        Xe_pv = []
        Ye_pv = []
        done = False
        while not done:
            children = get_children(G, node)
            edges = [edge for edge in G.out_edges(node) if float(G.nodes[edge[1]]['Q']) == sides[i]]
            if edges == []:
                done = True
                continue
            edge = edges[0]
            node = edge[1]
            pv_edges.append(edge)
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            Xe_pv += [x0, x1, None]
            Ye_pv += [y0, y1, None] 
            i = (i+1)%2
        return(pv_edges, Xe_pv, Ye_pv)
    #non-pv edge coordinates
    Xe = []
    Ye = []
    #edge coordinates for edges in pv
    Xe_pv = []
    Ye_pv = []
    pv_edges = []
    
    node = get_root(G)
    pv_edges, Xe_pv, Ye_pv = get_pv(node)
    
    
    if pv_edges == []:
        while True:
            edges = G.out_edges(node) 
            edge = get_best_edge(G, edges)
            pv_edges.append(edge)
            child_node = edge[1]
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            Xe_pv += [x0, x1, None]
            Ye_pv += [y0, y1, None]        
            if G.out_degree(child_node) == 0:
                break
            node = child_node
    
    for edge in G.edges():
        if edge in pv_edges:
            continue
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        Xe += [x0, x1, None]
        Ye += [y0, y1, None]
    return(Xe, Ye, Xe_pv, Ye_pv)

def get_y_ticks(pos):
    y = [pos[k][1] for k in pos.keys()]
    depth = len(set(y))
    tick_labels = [str(i) for i in range(depth)][::-1]
    tick_vals=list(range(depth))
    
    l = max([len(depth) for depth in tick_labels])
    tick_labels = [" "*(l-len(depth))+depth for depth in tick_labels]
    
    return(tick_labels, tick_vals)

def get_own_pos(G, merged_pos):
    own_pos = {key:merged_pos[key] for key in G}
    return(own_pos)

def get_x_range(pos):
    x_list = list(zip(*list(pos.values())))[0]
    min_x, max_x = min(x_list), max(x_list)
    margin = (max_x - min_x)*0.01
    return([min_x-margin, max_x+margin])

def generate_tick_labes(tick_labels, node_counts):
    data_tick_labels = []
    l = len(tick_labels)
    for nc in node_counts:
        nc = ["0" for i in range(l - len(nc))] + nc
        max_nc_len = max([len(c) for c in nc])
        labels = [' '*(max_nc_len - len(nc[i])) + nc[i] for i in range(l)]
        data_tick_labels.append(labels)
    return(data_tick_labels)


#def get_titles(engine_names, nets, cmds, G_list):
#    titles = []
#    for i, G in enumerate(G_list):
#        t = engine_names[i] + ', Net '+nets[i]+ '<br>'
#        t += '<i>' + cmds[i] + '</i>, ' 
#        nodes = str(get_visits(G, get_root(G)))
#        branching_factor = str(round(calc_branching_factor(G), 3))
#        t += 'Node count ' + '<b>' + nodes + '</b>, '
#        t += 'Branching factor: ' + '<b>' + branching_factor + '</b>'
#        titles.append(t)
#    return(titles)

def get_titles(titles, G_list):
    titles_out = []
    for i, G in enumerate(G_list):
        t = titles[i] + '<br>'
        nodes = str(get_visits(G, get_root(G)))
        branching_factor, leaf_share = calc_branching_factor_and_leaf_share(G)
        branching_factor = str(round(branching_factor, 3))
        leaf_share = str(round(leaf_share*100, 2))
        t += 'Node count ' + '<b>' + nodes + '</b>, '
        t += 'Branching factor ' + '<b>' + branching_factor + '</b>, '
        t += 'Leaf nodes ' + '<b>' + leaf_share + ' %</b>,'
        titles_out.append(t)
    return(titles_out)

def get_update_menu(dropdown_labels, titles, data_tick_labels, trace_owners):
    buttons = []
    for i in range(len(titles)):
        d = dict(label = dropdown_labels[i],
                 method = 'update',
                 args = [{'visible': [trace_owners[k] == i for k in range(len(trace_owners))]},
                         {'title': titles[i], 'yaxis.ticktext': data_tick_labels[i]}])
        buttons.append(d)
    updatemenus = list([
        dict(active=0, y = 1.1,
             buttons = list(
                 buttons))])
    return(updatemenus)

def update_sliders(labels, titles, data_tick_labels, trace_owners, label_prefix, active, x_labels):
    steps = []
    active = active
    for i in range(len(titles)):
        subplot_visibility = [k == i for k in range(len(trace_owners))]
        step = dict(method = 'update', label=labels[i], 
                    args = [{'visible': [trace_owners[k] == i for k in range(len(trace_owners))]+subplot_visibility},
                         {'title': titles[i], 'yaxis2.ticktext': data_tick_labels[i], 'xaxis.ticktext':x_labels[i]}])
        #step['args'][1][i] = True # Toggle i'th trace to "visible"
        steps.append(step)

    sliders = [dict(
        active = active,
        currentvalue = {"prefix": label_prefix},
        pad = {"t": 90},
        steps = steps
    )]
    return(sliders)

def html_plot(file_name, G_list, titles, update_labels, label_prefix = '', active = 0, init_moves = [], show_miniboard=True, use_online_font = True):
    if use_online_font:
        FONT_FAMILY = "'UnifontMedium'"#'monospace'#"'UnifontMedium'" #"'Space Mono', monospace"
    else:
        FONT_FAMILY = 'monospace'
    G_merged, G_list = merge_graphs(G_list)
    MARKER_SIZE = 4.0

    titles = get_titles(titles, G_list)
    if get_visits(G_merged, get_root(G_merged)) >= 1000:
        MARKER_SIZE = 3.25
    
    for n in topological_sort(G_merged.reverse()):
        parent = get_parent(G_merged, n)
        if parent is None:
            break
        if 'N' not in G_merged.nodes[n]:
            G_merged.nodes[n]['N'] = 1
        if 'N' not in G_merged.nodes[parent]:
            G_merged.nodes[parent]['N'] = 1 + G_merged.nodes[n]['N']
        else:
            G_merged.nodes[parent]['N'] += G_merged.nodes[n]['N']
    
    pos = get_pos(G_merged)
    pos = adjust_y(pos)
    tick_labels, tick_vals = get_y_ticks(pos)
    y_range = [-1, len(tick_vals)]
    x_range = get_x_range(pos)
    data = []
    data2 = []
    trace_owners = []
    node_counts = []
    
    root = get_root(G_merged) #X-label
    root_childern = list(get_children(G_merged, root)) #X-label
    root_childern.sort(key=lambda n: pos[n][0]) #X-label
    x_labels = [] #X-label
    x_label_vals = list(np.linspace(0,1, len(root_childern)))
    
    move_names =[]
    for child in root_childern:
        for G in G_list:
            if child in G:
                move_names.append(G.nodes[child]['move'])
                break
    #print('move names: ', move_names)
    
    for owner, G in enumerate(G_list):
        node_counts.append(get_nodes_in_depth(G))
        G_pos = get_own_pos(G, pos)
        pos_list = pos_separation(G, G_pos)

        #edge coordinates
        xe, ye, xe_pv, ye_pv = get_edge_xy(G, pos)
        
        visible = owner == active
        
        trace_e = go.Scatter(x=xe, y=ye,
                         mode='lines',
                         line=dict(color=EDGE_COLOR, width=0.5),
                         hoverinfo='none', 
                         showlegend=False, visible = visible)
        
        trace_e_pv = go.Scatter(x=xe_pv, y=ye_pv,
                         mode='lines',
                         line=dict(color=PV_COLOR, width=1.0),
                         hoverinfo='none', 
                         showlegend=False, visible = visible)
        data.append(trace_e)
        trace_owners.append(owner)
        data.append(trace_e_pv)
        trace_owners.append(owner)
        
        i = 0
        #node coordinates per branch
        for p in pos_list:
            if i == 0:
                color = ROOT_NODE_COLOR
            else:
                color = BRANCH_COLORS[i%len(BRANCH_COLORS)]
            x,y,text = get_xy(G, p, show_miniboard, init_moves)
            i+=1

            trace_n = go.Scatter(dict(x=x, y=y),
                               mode = 'markers',
                               text = text,
                               hoverinfo = 'text',
                               marker={'color': color, 'symbol': "circle", 'size': MARKER_SIZE},
                               textfont={"family":FONT_FAMILY},
                               hoverlabel = dict(font=dict(family=FONT_FAMILY, size = 15), bgcolor = HOVER_LABEL_COLOR), 
                                showlegend=False, visible = visible)

            data.append(trace_n)
            trace_owners.append(owner)
        
        x_lab = [] #X-label
        G_non_root_nodes = int(G.nodes[get_root(G)]['N']) - 1
        
        #get best root child
        root = get_root(G)
        edges = G.out_edges(root) 
        best_move = get_best_edge(G, edges)[1]
        
        for j, child in enumerate(root_childern): #X-label
            if best_move == move_names[j]:
                val ='<a href="" style="color: '+ BEST_MOVE_COLOR +'"> <b>' + move_names[j] + '</b>'+ '<br>'
            else:
                val ='<b>' + move_names[j] + '</b>'+ '<br>'
            if child in G: #X-label
                nodes = int(G.nodes[child]['N'])
                p = str(round(100*nodes/G_non_root_nodes, 1)) + '%'
                
                val += p #X-label
                if best_move == move_names[j]:
                    val += '</a>'
                
            x_lab.append(val) #X-label
        x_labels.append(x_lab) #X-label

    l = max([len(nc) for nc in node_counts])
    node_counts = [['0']*(l-len(nc)) + nc for nc in node_counts]
    y2_max = max(max([int(x) for x in nc]) for nc in node_counts)
    y2_range = [0, y2_max]
    for i, nc in enumerate(node_counts):
        visible = i == active
        hist_y = [int(x) for x in nc]
        x = list(range(len(hist_y)))
        data2.append(go.Bar(x=hist_y,y=x, visible = visible, orientation='h', 
                            showlegend=False, hoverinfo='none',
                           marker=dict(
        color=BAR_COLOR)))

    data_tick_labels = generate_tick_labes(tick_labels, node_counts)
    sliders = update_sliders(update_labels, titles, data_tick_labels, trace_owners, label_prefix, active, x_labels)
    layout=go.Layout(#title=titles[active],
                        #scene=dict(bgcolor="rgba(0, 0, 0, 0)"),
                        title=dict(text=titles[active], x=0.5, xanchor="center"),
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
                         xaxis=dict(zeroline=False, showgrid = False, range = x_range,
                                   domain = [0.0, 0.91], tickvals=x_label_vals, ticktext = x_labels[active], 
                                    title='Visit distribution'), 
                         yaxis=dict(zeroline=False, title='Depth',
                                    ticktext=tick_labels, tickvals=tick_vals, range = y_range, gridcolor=GRID_COLOR),
                         yaxis2=dict(zeroline=False, title='',
                                     range = y_range, showticklabels=True, side='left',
                                     ticktext = data_tick_labels[active], tickvals=tick_vals),
                         xaxis2=dict(zeroline=False, showgrid = False, showticklabels=False,
                                    domain = [0.93,1.0], range=y2_range),
                         hovermode='closest',
                         font=dict(family=FONT_FAMILY, size=FONT_SIZE, color=FONT_COLOR), 
                         sliders=sliders, # updatemenus=updatemenus,
                         height = 900, plot_bgcolor=PLOT_BACKGROUND_COLOR)
    fig = tools.make_subplots(rows=1, cols=2, specs=[[{}, {}]], shared_xaxes=True, 
                          shared_yaxes=False, vertical_spacing=0.001)
    
    for trace in data:
        fig.append_trace(trace, 1, 1)
    for trace in data2:
        fig.append_trace(trace, 1, 2)
    fig['layout'].update(layout)

    div = py.offline.plot(fig, include_plotlyjs=False, output_type='div', show_link=False)
    
#    head = '''<head> \n <script src="https://cdn.plot.ly/plotly-latest.min.js"></script> \n
#    <link rel="stylesheet" media="screen" href="https://fontlibrary.org/face/gnu-unifont" type="text/css"/> \n
#    </head> \n<body>'''
    head = '''<head> \n <script src="https://cdn.plot.ly/plotly-latest.min.js"></script> \n '''
    if use_online_font:
        head += '''<link rel="stylesheet" media="screen" href="https://fontlibrary.org/face/gnu-unifont" type="text/css"/> \n '''
    head += '''<link rel="stylesheet" media="screen" href="https://fontlibrary.org/face/gnu-unifont" type="text/css"/> \n 
    </head> \n<body>'''
    tail = "</body> \n"
    if type(init_moves)==str:
        extra = "<div>" +"position fen " + init_moves + "</div>"
    elif init_moves != []:
        extra = "<div>" +"position startpos moves " + " ".join(init_moves) + "</div>"
    else:
        extra = ""
    plot = head + extra +div+tail
    #print('Writing file', file_name)
    file = open(file_name,"w")
    file.write(plot)
    file.close()
    return(None)

def preprocess_arguments(nets, exes, shared_params, params, slider_labels, titles, nodes):
    args = locals()
    #preprocess args to be lists of n elements
    n = max([len(args[key]) for key in args if type(args[key])==list and key != 'shared_params'])
    args = {arg:[args[arg]]*n if type(args[arg])!=list else args[arg] for arg in args}
    
    #terminate if wrong number of elements
    terminate = False
    for key in args:
        if len(args[key]) != n and key != 'shared_params':
            print(key, 'list has', len(args[key]), 'elements, expected', n)
            terminate = True
    if terminate:
        return(None)
    
    #combine fixed params with params

    if params is None or params == [] or params =='':
        args['params'] = [shared_params]*n
    elif type(params[0]) == list:
        args['params'] = [shared_params + params[i] for i in range(n)]
    else:
        args['params'] = [shared_params + [params[i]] for i in range(n)]
    return(args['nets'], args['exes'], args['params'], args['slider_labels'], args['titles'], args['nodes'])


def create_graphs(exes, nets, params, nodes, moves):
    G_list = []
    for i in range(len(exes)):
        arg = [exes[i], '--weights='+nets[i]] + params[i]
        play(arg, nodes[i], moves = moves)
        G = nx.readwrite.gml.read_gml('tree.gml',label='id')
        os.remove('tree.gml')
        G_list.append(G)
    return(G_list)


def is_fen(string):
    board = chess.Board()
    try:
        board.set_fen(string)
        return(True)
    except:
        return(False)


def plot_search_tree(file_name, nets, exes, shared_params, params, slider_labels, titles, nodes, init_moves = [], show_miniboard = True, active = 0, use_online_font = True):
    if not file_name.endswith('.html'):
        file_name += '.html'
    #convert string of moves to list 
    if type(init_moves) == str and not is_fen(init_moves):
        init_moves = init_moves.split(' ')
    nets, exes, params, slider_labels, titles, nodes = preprocess_arguments(nets, exes, shared_params, params, slider_labels, titles, nodes)
    if any(n > MAX_ALLOWED_NODES for n in nodes):
        print('Plotting tool is not suited for high node plots. Stay below', MAX_ALLOWED_NODES, 'nodes.')
        return(None)
    G_list = create_graphs(exes, nets, params, nodes, moves=init_moves)
    html_plot(file_name, G_list, titles, slider_labels, label_prefix = '', active = active, init_moves = init_moves, show_miniboard = show_miniboard, use_online_font = use_online_font)
    return(None)
