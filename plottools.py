from graphtools import *
from buchheim import buchheim
import time

MOVED_PIECE_COLOR = 'rgb(210,105,30)'
COLOR_START = '<a href="" style="color: ' + MOVED_PIECE_COLOR + '">'
COLOR_END = '</a>'


def extract_coordinates(tree, pos):
    pos[tree.node][0] = tree.x
    pos[tree.node][1] = -tree.y
    for child in tree.children:
        extract_coordinates(child, pos)

#calculates node positions in canvas
def get_tree_layout(G):
    node = get_root(G)
    pos = {n:[None, None] for n in G.nodes}
    start = time.time()
    tree = buchheim(G, node)
    extract_coordinates(tree, pos)
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

#set y-coordinates to integers
def adjust_y(pos):
    y = [pos[k][1] for k in pos.keys()]
    set_y = list(set(y))
    set_y.sort()
    for k in pos:
        pos[k] = (pos[k][0],set_y.index(pos[k][1]))
    return(pos)


def branch_separation(G, pos):
    #separates node coordinates into branches for coloring purposes (adjacent branches use different colors)
    
    #finds the ancestor node on depth 1, i.e. the first node of this branch
    def get_branch(node):
        if is_root(G, node):
            return(node)
        
        while not is_root(G, get_parent(G, node)):
            node = get_parent(G, node)
        return(node)
    
    root = get_root(G)
    root_children = get_children(G, root)

    branches = {child: {} for child in root_children}
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
    board_uni = board.unicode()
    fen = board.fen()
    if not moves:
        to_move = (['Black to move', 'White to move'][board.turn])
        return(board_uni + '\n' + to_move, fen)
    board.pop()
    board_parent_uni = board.unicode()
    new_board = ''
    #color the last moved piece and origin square
    for i in range(127):
        p0 = board_uni[i]
        if p0 != board_parent_uni[i]:
            p0 = COLOR_START + p0 + COLOR_END
        new_board += p0
    #new_board = new_board.replace('.', 'O')
    return(new_board, fen)

def get_best_edge(G, edges):
        node_counts = [int(G.nodes[e[1]]['N']) for e in edges]
        if node_counts == []:
            return([None, None])
        maxN = max(node_counts)
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
    Q = float(G.nodes[node]['Q'])
    D = G.nodes[node]['D'] if 'D' in G.nodes[node] else None
    M = float(G.nodes[node]['M']) if 'M' in G.nodes[node] else None

    #filp root Q
    Q = -Q
    W, D, L = get_WDL(Q, float(D))

    #Q = str(round(Q, 3))
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


