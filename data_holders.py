from networkx.algorithms.dag import topological_sort
import os
import graphtools as gt
import plottools as pt
import chess
from lc0tools import leela
import chess.engine
import time
import numpy as np
import pandas as pd
from leela import leela_engine


BEST_MOVE_COLOR = 'rgb(178,34,34)'

#def leela(args):
#    lc0 = chess.engine.SimpleEngine.popen_uci(args)
#    return(lc0)

class GameData:
    def __init__(self):
        self.board = chess.Board()
        self.game_data = None
        self.fen = self.board.fen()
    def set_board_position(self, position_index):
        self.reset_board()
        for move in self.game_data['move'][1:position_index + 1]:
            self.board.push_san(move)
    def reset_board(self):
        self.board.set_fen(self.fen)


class ConfigData:
    def __init__(self):
        self.data = pd.DataFrame()
        self.data_analyzed = pd.DataFrame()

    def update_data(self, data):
        nr_of_rows = data.shape[0]
        self.data[:nr_of_rows] = data
        return(self.is_data_equal_to_analyzed())

    def is_data_equal_to_analyzed(self):
        return(self.data.equals(self.data_analyzed))

    def get_row(self, row_ind):
        row = self.data.iloc[row_ind]
        return(row)

    def get_configurations(self, row_ind, only_non_default=False):
        row = self.get_row(row_ind)
        #print('config row', row)
        config = {}
        for option_name in row.index:
            if option_name.endswith('_default'):
                continue
            option_value = row[option_name]
            if not only_non_default or option_value != row[option_name + '_default']:
                config[option_name] = option_value
        return(config)

class DataCreator:
    def __init__(self, lc0):#, engine_path, weight_path):
        #self.engine_path = engine_path
        #self.weight_path = weight_path
        #self.args = [engine_path, '--weights='+weight_path]
        self.lc0 = lc0
        self.G_list = {} #{position_index1: [], position_index2: []....}
        self.data = {}
        self.data_depth = {}
        self.board = chess.Board()
        #self.parameters = None

        self.x_range = {}
        self.y_range = {}
        self.y_tick_labels = {}
        self.y_tick_values = {}
        self.y2_range = {}
        self.x_tick_labels = {}
        self.x_tick_values = {}

    def reset_data(self):
        self.G_list = {}
        self.data = {}
        self.data_depth = {}
        self.board = chess.Board()
        #self.parameters = None
        self.x_range = {}
        self.y_range = {}
        self.y_tick_labels = {}
        self.y_tick_values = {}
        self.y2_range = {}
        self.x_tick_labels = {}
        self.x_tick_values = {}

    #def reset(self):
    #    self.__init__(self.engine_path, self.weight_path)

    def get_best_moves(self, position_index, slider_value, type, max_moves):
        try:
            tree = self.G_list[position_index][slider_value]
        except KeyError:
            #not yet analyzed
            return([], [])
        children = gt.get_children(tree, gt.get_root(tree))

        metrics = []
        moves = []
        for node in children:
            if type == 'p':
                metric = float(tree.nodes[node]['P'])
            elif type == 'n':
                metric = int(tree.nodes[node]['N'])
            elif type == 'q':
                metric = float(tree.nodes[node]['Q'])
            metrics.append(metric)
            moves.append(tree.nodes[node]['move'])

        metrics, moves = zip(*sorted(zip(metrics, moves), reverse=True))

        #convert absolute number of visits to ratios
        if type == 'n':
            total = sum(metrics)
            metrics = [visits/total for visits in metrics]

        nr_of_children = len(moves)
        metrics = metrics[: min(max_moves, nr_of_children)]
        moves = moves[: min(max_moves, nr_of_children)]
        return(moves, metrics)

    def run_search(self, position_index, parameters, board, nodes):
        self.lc0.configure(parameters)
        start = time.time()
        g = self.lc0.play(board, nodes)
        print('search completed in time: ', time.time() - start)
        if position_index in self.G_list:
            self.G_list[position_index].append(g)
        else:
            self.G_list[position_index] = [g]

    def create_data(self, position_index, moves):
        #print('G_LIST', self.G_list)
        G_merged, G_list = gt.merge_graphs(self.G_list[position_index])
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

        root = gt.get_root(G_merged)  # X-label
        root_children = list(gt.get_children(G_merged, root))  # X-label
        root_children.sort(key=lambda n: pos[n][0])  # X-label
        x_labels = []  # X-label
        x_label_vals = list(np.linspace(0, 1, len(root_children)))
        move_names = []
        for child in root_children:
            for G in G_list:
                if child in G:
                    move_names.append(G.nodes[child]['move'])
                    break
        for owner, G in enumerate(G_list):

            #########################
            x_lab = []  # X-label
            G_non_root_nodes = int(G.nodes[gt.get_root(G)]['N']) - 1

            # get best root child
            root = gt.get_root(G)
            edges = G.out_edges(root)
            best_move = pt.get_best_edge(G, edges)[1]

            for j, child in enumerate(root_children):  # X-label
                if best_move == move_names[j]:
                    val = '<a href="" style="color: ' + BEST_MOVE_COLOR + '"> <b>' + move_names[j] + '</b>' + '<br>'
                else:
                    val = '<b>' + move_names[j] + '</b>' + '<br>'
                if child in G:  # X-label
                    nodes = int(G.nodes[child]['N'])
                    p = str(round(100 * nodes / G_non_root_nodes, 1)) + '%'

                    val += p  # X-label
                    if best_move == move_names[j]:
                        val += '</a>'

                x_lab.append(val)  # X-label
            x_labels.append(x_lab)  # X-label
            #########################

            G_pos = pt.get_own_pos(G, pos)
            pos_list = pt.pos_separation(G, G_pos)
            node_counts.append(gt.get_nodes_in_depth(G))

            pv_nodes = pt.get_pv_nodes(G)

            for i, branch in enumerate(pos_list):
                for node in branch:
                    if node not in data:
                        parent = gt.get_parent(G, node)
                        parent_point = [None, None] if parent is None else pos[parent]
                        miniboard = pt.get_miniboard_unicode(G, node, self.board, moves).replace('\n', '<br>')
                        data[node] = {'point': branch[node],
                                      'parent': parent_point,
                                      'miniboard':  miniboard,
                                      'visible': {}
                                      }
                    node_metrics = pt.get_node_metric_text(G, node)
                    edge_type = ''
                    if node in pv_nodes:
                        edge_type = 'pv'
                    if node == 'root':
                        type = 'root'
                    elif i%2 == 0:
                        type = 'even'
                    elif i%2 == 1:
                        type = 'odd'
                    data[node]['visible'][owner] = {'type': (type, edge_type), 'metric': node_metrics}
                    if type == 'root':
                        eval = pt.get_node_eval(G, node)
                        data[node]['visible'][owner]['eval'] = eval

        self.data[position_index] = data
        y_tick_labels, y_tick_values = pt.get_y_ticks(pos)
        y_range = [-1, len(y_tick_values)]
        x_range = pt.get_x_range(pos)
        self.x_range[position_index] = x_range
        self.y_range[position_index] = y_range
        self.y_tick_labels[position_index] = y_tick_labels
        self.y_tick_values[position_index] = y_tick_values


        max_len = max([len(nc) for nc in node_counts])
        node_counts = [['0'] * (max_len - len(nc)) + nc for nc in node_counts]
        y2_max = max(max([int(x) for x in nc]) for nc in node_counts)
        self.y2_range[position_index] = [0, y2_max]
        self.data_depth[position_index] = {i: (list(range(len(node_count))), list(map(int, node_count))) for i, node_count in enumerate(node_counts)}
        self.x_tick_labels[position_index] = {i: x_label_list for i, x_label_list in enumerate(x_labels)}
        self.x_tick_values[position_index] = x_label_vals

    def create_demo_data(self):
        net = '/home/jusufe/leelas/graph_analysis3/nets60T/weights_run1_62100.pb.gz'
        engine = '/home/jusufe/lc0_test4/build/release/lc0'
        self.args = [engine, '--weights=' + net]

        #param1 = ['--cpuct=2.147', '--minibatch-size=1', '--threads=1',
                  #'--max-collision-events=1', '--max-collision-visits=1']
        #param2 = ['--cpuct=4.147', '--minibatch-size=1', '--threads=1',
                  #'--max-collision-events=1', '--max-collision-visits=1']

        param1 = {'CPuct': '2.147', 'MinibatchSize': '1', 'Threads': '1',
                          'MaxCollisionEvents': '1', 'MaxCollisionVisits': '1', }
        param2 = {'CPuct': '4.147', 'MinibatchSize': '1', 'Threads': '1',
                          'MaxCollisionEvents': '1', 'MaxCollisionVisits': '1', }

        nodes = 20

        position_index = 0
        moves = []
        board = chess.Board()
        self.run_search(position_index, param1, board, nodes)
        self.run_search(position_index, param2, board, nodes)
        self.create_data(position_index, moves)

net = '/home/jusufe/tmp/weights_run2_591226.pb.gz'
engine = '/home/jusufe/lc0_test4/build/release/lc0'
args = [engine, '--weights=' + net]
lc0 = leela_engine(args)#leela(args)

data_creator = DataCreator(lc0)
data_creator.create_demo_data()
game_data = GameData()
config_data = ConfigData()

