import networkx as nx
from networkx.algorithms.dag import topological_sort
import time

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
    #Only one predecessor as we are dealing with trees
    return(list(G.predecessors(n))[0])

def get_subtree_node_count(G, n):
    #number of nodes in this subbranch
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

#maybe useful someday
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
        return(label)

    return(nx.relabel_nodes(G, mapping, copy=True))

def relabel_new(G, label_dict):
    def mapping(n):
        label = "".join(get_moves(G,n))
        #if label == "":
        #    id = "root"
        #else:
        id = label_dict.get(label, None)
        if id is None:
            id = len(label_dict) + 1
            label_dict[label] = id
        return(id)

    return(nx.relabel_nodes(G, mapping, copy=True), label_dict)

def add_ids(G, label_dict, running_id):

    new_ids = {}
    node_move_chain = {}
    for n in topological_sort(G):
        parent = get_parent(G, n)
        if parent is None:
            chain = ''
        else:
            chain = node_move_chain[parent] + G.nodes[n]['move']

        node_move_chain[n] = chain
        id = label_dict.get(chain, None)
        if id is None:
            id = running_id
            running_id += 1
            label_dict[chain] = id
        new_ids[n] = id
    #print('IDs',new_ids)
    G = nx.relabel_nodes(G, new_ids, copy=True)
    return(G, label_dict, running_id)



#maybe useful someday
def calc_shared_nodes(G1, G2):
    G1 = relabel(G1)
    G2 = relabel(G2)
    count = 0
    for n in G1:
        count += n in G2
    return(count)

def merge_graphs(G_list):
    #takes list of DiGraphs and calculates union of the graphs
    #also unifies the node ids of each graph so that nodes obtained from same move sequence have same id

    start = time.time()
    label_dict = {"": "root"}
    running_id = 0
    G_merged = nx.DiGraph()
    #G_list = [relabel_new(G, label_dict) for G in G_list]

    G_list_new = []
    #for G in G_list:
    #    g, label_dict = relabel_new(G, label_dict)
    #    #print('label_dict', label_dict)
    #    G_list_new.append(g)
    #G_list = G_list_new

    for G in G_list:
        G, label_dict, running_id = add_ids(G, label_dict, running_id)
        G_list_new.append(G)
    G_list = G_list_new

    G_merged.add_node(get_root(G_list[0]))  # add root node to handle case of no edges

    print('Merging - relabel', time.time() - start)
    start = time.time()
    for G in G_list:
        for edge in G.edges():
            if edge not in G_merged.edges():
                G_merged.add_edge(edge[0], edge[1])
    print('Merging - 1st merged', time.time() - start)
    start = time.time()
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

    visits_and_nodes = [(G_merged.nodes[node]['N'], node) for node in G_merged]
    #visits, nodes = zip(*visits_and_nodes)
    visits, nodes = zip(*sorted(visits_and_nodes, reverse=True))
    print('Merging - calc visits', time.time() - start)
    
    #visits = []
    #nodes = []
    #for n in G_merged:
    #    visits.append(get_subtree_node_count(G_merged, n))
    #    nodes.append(n)
    #visits, nodes = zip(*sorted(zip(visits, nodes), reverse=True))

    #reconstruct by adding nodes in order of visit counts for prettier layout result from buchheim algorithm
    # -> node heavy branches will be aligned left
    start = time.time()
    G_merged_ordered = nx.DiGraph()
    for n in nodes:
        G_merged_ordered.add_node(n, N=G_merged.nodes[n]['N'])
    for edge in G_merged.edges():
        G_merged_ordered.add_edge(edge[0], edge[1])

    #print('G list nodes after merge graphs')
    #for G in G_list:
    #    print(G.nodes)
    print('Merging - 2d merged', time.time() - start)
        
    return(G_merged_ordered, G_list)
