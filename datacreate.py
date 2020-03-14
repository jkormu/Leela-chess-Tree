from lc0tools import play
import networkx as nx
from networkx.algorithms.dag import topological_sort
import os
import graphtools as gt
import plottools as pt
import chess

class DataCreator:
    def __init__(self, engine_path, weight_path, init_moves):
        self.args = [engine_path, '--weights='+weight_path]
        self.G_list = []
        self.data = {}
        self.data_depth = {}
        self.moves = init_moves
        self.board = chess.Board()

    def run_search(self, parameters, nodes):
        play(self.args + parameters, nodes, moves=self.moves)
        g = nx.readwrite.gml.read_gml('tree.gml', label='id')
        os.remove('tree.gml')
        self.G_list.append(g)

    def create_data(self):
        G_merged, G_list = gt.merge_graphs(self.G_list)
        for n in topological_sort(G_merged.reverse()):
            parent = gt.get_parent(G_merged, n)
            if parent is None:
                break
            if 'N' not in G_merged.nodes[n]:
                G_merged.nodes[n]['N'] = 1
            if 'N' not in G_merged.nodes[parent]:
                G_merged.nodes[parent]['N'] = 1 + G_merged.nodes[n]['N']
            else:
                G_merged.nodes[parent]['N'] += G_merged.nodes[n]['N']
        pos = pt.get_pos(G_merged)
        pos = pt.adjust_y(pos)

        data = {}
        node_counts = []
        for owner, G in enumerate(G_list):
            G_pos = pt.get_own_pos(G, pos)
            pos_list = pt.pos_separation(G, G_pos)
            node_counts.append(gt.get_nodes_in_depth(G))

            pv_nodes = pt.get_pv_nodes(G)

            for i, branch in enumerate(pos_list):
                for node in branch:
                    if node not in data:
                        parent = gt.get_parent(G, node)
                        parent_point = [None, None] if parent is None else pos[parent]
                        miniboard = pt.get_miniboard_unicode(G, node, self.board, self.moves).replace('\n', '<br>')
                        miniboard += pt.get_node_metric_text(G, node)
                        data[node] = {'point': branch[node],
                                      'parent': parent_point,
                                      'miniboard':  miniboard,
                                      'visible': {}
                                      }

                    edge_type = ''
                    if node in pv_nodes:
                        edge_type = 'pv'
                    if node == 'root':
                        type = 'root'
                    elif i%2 == 0:
                        type = 'even'
                    elif i%2 == 1:
                        type = 'odd'
                    data[node]['visible'][owner] = {'type': (type, edge_type), 'metric': (1, 2, 3)}
        self.data = data
        y_tick_labels, y_tick_values = pt.get_y_ticks(pos)
        y_range = [-1, len(y_tick_values)]
        x_range = pt.get_x_range(pos)
        self.x_range = x_range
        self.y_range = y_range
        self.y_tick_labels = y_tick_labels
        self.y_tick_values = y_tick_values


        max_len = max([len(nc) for nc in node_counts])
        node_counts = [['0'] * (max_len - len(nc)) + nc for nc in node_counts]
        y2_max = max(max([int(x) for x in nc]) for nc in node_counts)
        self.y2_range = [0, y2_max]
        self.data_depth = {i: (list(range(len(node_count))), list(map(int, node_count))) for i, node_count in enumerate(node_counts)}


        #data_tick_labels = []
        #l = len(tick_labels)
        #for nc in node_counts:
        #    nc = ["0" for i in range(l - len(nc))] + nc
        #    max_nc_len = max([len(c) for c in nc])
        #    labels = [' ' * (max_nc_len - len(nc[i])) + nc[i] for i in range(l)]
        #    data_tick_labels.append(labels)
        #return (data_tick_labels)


    def create_demo_data(self):
        net = '/home/jusufe/leelas/graph_analysis3/nets60T/weights_run1_62100.pb.gz'
        engine = '/home/jusufe/lc0_test4/build/release/lc0'
        self.args = [engine, '--weights=' + net]

        param1 = ['--cpuct=2.147']
        param2 = ['--cpuct=4.147']
        nodes = 800

        self.run_search(param1, nodes)
        self.run_search(param2, nodes)
        self.create_data()

#print(data_creator.data)
