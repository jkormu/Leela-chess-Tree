import networkx as nx

def get_root(G):
    for n in G:
        if G.in_degree(n) == 0:
            return(n)

def is_root(G, n):
    return(G.in_degree(n) == 0)

def is_leaf(G, n):
    return(G.out_degree(n)==0)
        
def get_children(G, n):
    return(G.successors(n))

def get_parent(G, n):
    if is_root(G, n):
        return(None)
    return(list(G.predecessors(n))[0])

def get_visits(G, n):
    visits = 1+len(nx.algorithms.dag.descendants(G,n))
    return(visits)

def calc_branching_factor_and_leaf_share(G):
    out_degrees = [G.out_degree(n) for n in G]
    num_of_non_leafs = sum([out_d > 0 for out_d in out_degrees])
    leaf_share = (len(out_degrees) - num_of_non_leafs)/len(out_degrees)
    branching_factor = sum(out_degrees)/num_of_non_leafs
    return(branching_factor, leaf_share)

def get_nodes_in_depth(G):
    root = get_root(G)
    distances = [nx.shortest_path_length(G, root, n) for n in G]
    l = list(set(distances))
    l.sort()
    counts = [str(distances.count(x)) for x in l][::-1]
    return(counts)

def number_of_shared_nodes(G1,G2):
    G = nx.intersection(G1, G2)
    return(G.number_of_nodes())

def calc_leaf_portion(G):
    N = len(list(G.nodes))
    n = len([n for n in G if G.out_degree(n)==0])
    return(n/N)

def get_moves(G, n):
    moves = []
    move = G.nodes[n]['move']
    while move != "":
        moves.append(move)
        n = get_parent(G, n)
        move = G.nodes[n]['move']
    return(moves[::-1])


def relabel(G):
    def mapping(n):
        label = "".join(get_moves(G,n))
        if label == "":
            label = "root"
        #label = G.nodes[n]['N'] + label
            
        return(label)

    return(nx.relabel_nodes(G, mapping, copy=True))

def calc_shared_nodes(G1, G2):
    G1 = relabel(G1)
    G2 = relabel(G2)
    count = 0
    for n in G1:
        count += n in G2
    return(count)


def merge_graphs(G_list):
    G_merged = nx.DiGraph()
    G_list = [relabel(G) for G in G_list]
    
    for G in G_list:
        for edge in G.edges():
            if edge not in G_merged.edges():
                G_merged.add_edge(edge[0], edge[1])
    
    visits = []
    nodes = []
    for n in G_merged:
        visits.append(get_visits(G_merged, n))
        nodes.append(n)
        
    visits, nodes = zip(*sorted(zip(visits, nodes), reverse=True))
    
    G_merged_ordered = nx.DiGraph()
    for n in nodes:
        G_merged_ordered.add_node(n)
    for edge in G_merged.edges():
        G_merged_ordered.add_edge(edge[0], edge[1])
        
    return(G_merged_ordered, G_list)
