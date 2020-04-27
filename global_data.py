from networkx.algorithms.dag import topological_sort
import graphtools as gt
import plottools as pt
import chess
import chess.engine
from leela import leela_engine
import os
from os.path import isfile, join

from dash_table.Format import Format, Scheme

from constants import MAX_NUMBER_OF_CONFIGS, DEFAULT_NODES, ROOT_DIR, SHOW_UNICODE_BOARD
import time
import json

BEST_MOVE_COLOR = 'rgb(178,34,34)'

# deterministic search settings
deterministic_defaults = {
    'Threads': 1,
    'MinibatchSize': 1,
    'MaxPrefetch': 1,
    'MaxCollisionEvents': 1,
    'MaxCollisionVisits': 1,
    'OutOfOrderEval': 'False',
    'MaxConcurrentSearchers': 1,
}

# Disable smart pruning
other_defaults = {
    'SmartPruningFactor': 0
}

#Options user cannot change, mostly due to not having effect on search
filter_out_options = [
    'Backend',
    'BackendOptions',
    'NNCacheSize',
    'Temperature',
    'TempDecayMoves',
    'TempCutoffMove',
    'TempEndgame',
    'TempValueCutoff',
    'TempVisitOffset',
    'DirichletNoise',
    'VerboseMoveStats',
    'SyzygyFastPlay',
    'MultiPV',
    'PerPVCounters',
    'ScoreType',
    'HistoryFill',
    'SyzygyPath',
    'Ponder',
    'UCI_Chess960',
    'UCI_ShowWDL',
    'ConfigFile',
    'RamLimitMb',
    'MoveOverheadMs',
    'Slowmover',
    'ImmediateTimeUse',
    'LogFile',
    'SmartPruningMinimumBatches',
    'TimeManager']

#dictionary of option categorys and option names user can edit
#this this dict also determines order of the groups and parameters (dicts are ordered in python 3.7)
COLUMNS_PER_GROUP = {
    'Nodes': ['Nodes'],
    'Net': ['WeightsFile'],
    'Cpuct': ['CPuct',
              'CPuctFactor',
              'CPuctBase',
              'CPuctAtRoot',
              'CPuctFactorAtRoot',
              'CPuctBaseAtRoot'],
    'Fpu': ['FpuStrategy',
            'FpuValue',
            'FpuStrategyAtRoot',
            'FpuValueAtRoot'],
    'Policy temp': ['PolicyTemperature'],
    'Moves left': ['MovesLeftThreshold',
                   'MovesLeftMaxEffect',
                   'MovesLeftSlope'],
    'Search enhancements': ['LogitQ',
                            'ShortSightedness'],
    'Draw score': ['DrawScoreSideToMove',
                   'DrawScoreOpponent',
                   'DrawScoreWhite',
                   'DrawScoreBlack'],
    'Misc': ['CacheHistoryLength',
             'StickyEndgames'],
    'Early stop': ['KLDGainAverageInterval',
                   'MinimumKLDGainPerNode',
                   'SmartPruningFactor'],
    'Threading and batching': ['Threads',
                               'MinibatchSize',
                               'MaxPrefetch',
                               'MaxCollisionEvents',
                               'MaxCollisionVisits',
                               'OutOfOrderEval',
                               'MaxOutOfOrderEvalsFactor',
                               'MaxConcurrentSearchers']
}
COLUMN_ORDER = [column for group in COLUMNS_PER_GROUP for column in COLUMNS_PER_GROUP[group]]
GROUP_PER_COLUMN = {column: group for group in COLUMNS_PER_GROUP for column in COLUMNS_PER_GROUP[group]}

class GlobalParameters:
    def __init__(self):
        self.draw_miniboard = True
        self.default_nodes = 200
        self.max_nodes = 200000
        self.max_configs = 10
        self.position_pane_relative_width = 20 #portion of the total screen width in percentages

class GameData:
    def __init__(self, mode):
        self.board = chess.Board()
        self.pgn_start_fen = self.board.fen()
        self.data = None #[row1, row2, ...] where row1 = {'column_name1': value1, 'column_name2': value2, ...}
        self.data_previous = None # ToDo: this is no longer needed as we don't use pandas anymore. fen delete callback should use GameData.data directly
        self.mode = mode #either "pgn" or "fen"
        self.running_fen_id = 0

    def get_value_by_position_id(self, column_name, position_id):
        for row in self.data:
            if row['ply'] == position_id:
                return(row[column_name])
        return(None)

    def get_value_by_row_id(self, column_name, row):
        value = self.data[row][column_name]
        return(value)

    def get_position_id(self, row):
        try:
            return(self.data[row]['ply'])
        except (KeyError, TypeError) as e:
            return(None)

    def set_board_position(self, position_id):
        if self.mode == 'fen':
            if self.data is None or position_id is None:
                self.board.reset_board()
            else:
                fen = self.get_value_by_position_id('fen', position_id)
                self.board.set_fen(fen)
        else:
            self.reset_board()
            for row in self.data[1:position_id + 1]:#move in [self.data[row]['move'] for row in self.data[1:position_id + 1]]:
                move = row['move']
                self.board.push_san(move)

    def reset_board(self):
        self.board.set_fen(self.pgn_start_fen)

    def get_running_fen_id(self):
        fen_id = self.running_fen_id
        self.running_fen_id += 1
        return(fen_id)

    def set_column(self, column_name, values):
        for i, value in enumerate(values):
            self.data[i][column_name] = value


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def try_to_round(value, precision):
    #don't convert boolean values to floats
    if isinstance(value, bool):
        return value
    try:
        out = round(float(value), precision)
    except ValueError:
        out = value
    return out

class ConfigData:
    def __init__(self, lc0):
        self.data = []#pd.DataFrame()
        self.data_analyzed = []#pd.DataFrame()
        self.data_row = {}
        self.dropdowns = {}
        self.columns = []
        self.columns_with_min = [] #options with min allowed uci value
        self.columns_with_max = [] #options with max allowed uci value
        self.lc0 = lc0
        self.weight_files = []
        self.weight_paths = []
        self.find_weights()
        self.construct_config_data(True)

    def find_weights(self):
        root = ROOT_DIR#os.path.dirname(os.path.abspath(__file__))#os.getcwd()
        weights_folder = os.path.join(root, 'weights')
        weight_files = [f.split(".")[0] for f in os.listdir(weights_folder) if isfile(join(weights_folder, f))]
        weight_paths = [os.path.relpath(join(weights_folder, f)) for f in os.listdir(weights_folder) if isfile(join(weights_folder, f))]
        #print('WEIGHT PATHS', weight_paths)
        self.weight_files = weight_files
        self.weight_paths = weight_paths

    def construct_config_data(self, use_deterministic_defaults):
        self.data_row = {}
        self.columns = []
        self.columns_with_min = []
        self.columns_with_max = []
        self.data_row['Nodes'] = DEFAULT_NODES
        self.data_row['Nodes_default'] = DEFAULT_NODES
        node_col = {'id': 'Nodes', 'name': ['', 'Nodes'], 'clearable': False}
        self.columns.append(node_col)
        for opt in self.lc0.options:
            option = lc0.options[opt]
            if opt not in filter_out_options:
                group = GROUP_PER_COLUMN.get(opt, 'Misc')
                self.add_column(option, group, use_deterministic_defaults)

        self.columns.sort(key=lambda x: COLUMN_ORDER.index(x['name'][1]) if x['name'][1] in COLUMN_ORDER else 999999)

        #df = pd.DataFrame(self.df_dict)
        #df = pd.concat([df] * MAX_NUMBER_OF_CONFIGS, ignore_index=True)
        self.data = [self.data_row for _ in range(MAX_NUMBER_OF_CONFIGS)]

    def add_column(self, option, category, use_deterministic_defaults):
        option_type = option.type
        default = option.default
        if option_type == 'check':
            default = str(default)
        elif option_type != "spin":
            default = try_to_round(default, 3)  # TODO: don't round here, rather edit datatable formatting
        name = option.name
        if use_deterministic_defaults and name in deterministic_defaults:
            self.data_row[name] = deterministic_defaults[name]
        elif name in other_defaults:
            self.data_row[name] = other_defaults[name]
        else:
            self.data_row[name] = default

        self.data_row[name + '_default'] = default
        if option.min is not None:
            self.data_row[name + '_min'] = option.min
            self.columns_with_min.append(name)
        if option.max is not None:
            self.data_row[name + '_max'] = option.max
            self.columns_with_max.append(name)
        col = {'id': name, 'name': [category, name], 'clearable': False}#, 'validation': {'allow_null': False}, 'on_change': {'action': 'validate'}}
        if option_type == 'spin' or is_number(default) or option.min is not None or option.max is not None:
            col['type'] = 'numeric'
            if option_type == 'spin':
                col['format'] = Format(precision=0, scheme=Scheme.fixed)
            else:
                col['format'] = Format(precision=2, scheme=Scheme.fixed)
        if option_type == 'combo' or option_type == 'check' or name == 'WeightsFile':
            col['presentation'] = 'dropdown'
            if option_type == 'combo':
                var = option.var
            else:
                var = ('True', 'False')
            if name == 'WeightsFile':
                dropdown = {'options': [{'label': file, 'value': path} for file, path in zip(self.weight_files, self.weight_paths)],
                            'clearable': False}
            else:
                dropdown = {'options': [{'label': val, 'value': val} for val in var],
                            'clearable': False}
            self.dropdowns[name] = dropdown
        self.columns.append(col)
        return(None)

    def update_data(self, data):
        nr_of_rows = len(data)
        self.data[:nr_of_rows] = data
        return(self.is_data_equal_to_analyzed())

    def is_data_equal_to_analyzed(self):
        return(self.data == self.data_analyzed)

    def get_row(self, row_ind):
        row = self.data[row_ind]
        return(row)

    def get_configurations(self, row_ind, global_weight, only_non_default=False):
        row = self.get_row(row_ind)
        config = {}
        for option_name in row:
            if option_name.endswith('_default') or option_name.endswith('_min') or option_name.endswith('_max') or option_name == 'Nodes':
                continue
            if option_name == 'WeightsFile' and global_weight is not None:
                config[option_name] = global_weight
                continue
            option_value = row[option_name]
            if not only_non_default or option_value != row[option_name + '_default'] or option_name == 'WeightsFile':
                config[option_name] = option_value
        return(config)

    def get_nodes(self, row_ind, nodes_mode, global_nodes):
        if nodes_mode == ['global']:
            return(global_nodes)
        row = self.get_row(row_ind)
        nodes = row['Nodes']
        return(nodes)


    def get_data(self, nr_of_rows):
        return(self.data[:nr_of_rows])

    def get_columns(self, with_nodes, with_nets):
        columns_to_exclude = []
        if not with_nodes:
            columns_to_exclude.append('Nodes')
        if not with_nets:
            columns_to_exclude.append('WeightsFile')

        d = [col for col in self.columns if col['id'] not in columns_to_exclude]
        return(d)

#replicate behaviour of numpy's linspace
def linspace(a, b, n):
    if n == 0:
        return([])
    elif n < 2:
        return [a]
    diff = (b - a)/(n - 1)
    return([diff * i + a  for i in range(n)])

class TreeData:
    def __init__(self, lc0, type):
        self.lc0 = lc0
        self.type = type  # 'pgn' or 'fen'
        self.G_dict = {} #{position_id1: [], position_id2: []....}
        self.merged_graphs = {} #{position_id: merger_graph...}
        self.heatmap_data_for_moves = {} #{position_id: [{(color, piece, depth): z}, ... ]}
        self.heatmap_data_for_board_states = {}  # {position_id: [{(color, piece, depth): z}, ... ]}
        self.data = {}
        self.data_depth = {}
        self.board = chess.Board()

        self.x_range = {}
        self.y_range = {}
        self.y_tick_labels = {}
        self.y_tick_values = {}
        self.y2_range = {}
        self.x_tick_labels = {}
        self.x_tick_values = {}

    def reset_data(self):
        self.G_dict = {}
        self.merged_graphs = {}
        self.heatmap_data_for_moves = {}
        self.heatmap_data_for_board_states = {}
        self.data = {}
        self.data_depth = {}
        self.board = chess.Board()
        self.x_range = {}
        self.y_range = {}
        self.y_tick_labels = {}
        self.y_tick_values = {}
        self.y2_range = {}
        self.x_tick_labels = {}
        self.x_tick_values = {}

    def get_best_moves(self, position_id, slider_value, type, max_moves):
        try:
                tree = self.G_dict[position_id][slider_value]
        except (KeyError, IndexError) as e:
            #position not yet analyzed or slider value set to config not yet analyzed
            return ([], [])
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
            elif type in ('ml_low', 'ml_high'):
                metric = float(tree.nodes[node]['M'])
            metrics.append(metric)
            moves.append(tree.nodes[node]['move'])

        if moves == []:
            return([], [])

        higher_is_better = True
        if type == 'ml_low':
            higher_is_better = False

        metrics, moves = zip(*sorted(zip(metrics, moves), reverse=higher_is_better))

        #convert absolute number of visits to ratios
        if type == 'n':
            total = sum(metrics)
            metrics = [visits/total for visits in metrics]

        nr_of_children = len(moves)
        metrics = metrics[: min(max_moves, nr_of_children)]
        moves = moves[: min(max_moves, nr_of_children)]
        return(moves, metrics)

    def run_search(self, position_id, parameters, board, nodes):
        self.lc0.configure(parameters)
        g = self.lc0.play(board, nodes)
        if position_id in self.G_dict:
            self.G_dict[position_id].append(g)
        else:
            self.G_dict[position_id] = [g]

    def get_ML_range(self):
        roots = [self.data[position_id]['root'] for position_id in self.data]
        Ms = [root['visible'][visible]['eval']['M'] for root in roots for visible in root['visible']]
        M_min = min(Ms)
        M_max = max(Ms)
        return(M_min, M_max)

    def create_data(self, position_id, moves):
        start = time.time()
        G_merged, G_list = gt.merge_graphs(self.G_dict[position_id])
        print('graphs merged in', time.time() - start)
        self.G_dict[position_id] = G_list
        start = time.time()
        #for n in topological_sort(G_merged.reverse()):
        #    parent = gt.get_parent(G_merged, n)
        #    if parent is None:
        #        break
        #    if 'N' not in G_merged.nodes[n]:
        #        G_merged.nodes[n]['N'] = 1
        #    if 'N' not in G_merged.nodes[parent]:
        #        G_merged.nodes[parent]['N'] = 1 + G_merged.nodes[n]['N']
        #    else:
        #        G_merged.nodes[parent]['N'] += G_merged.nodes[n]['N']
        print('N calculation in', time.time() - start)
        pos = pt.get_tree_layout(G_merged)
        pos = pt.adjust_y(pos)
        data = {}
        node_counts = []

        root = gt.get_root(G_merged)  # X-label
        root_children = list(gt.get_children(G_merged, root))  # X-label
        root_children.sort(key=lambda n: pos[n][0])  # X-label
        x_labels = []  # X-label
        x_label_vals = linspace(0, 1, len(root_children))
        move_names = []
        for child in root_children:
            for G in G_list:
                if child in G:
                    move_names.append(G.nodes[child]['move'])
                    break

        for owner, G in enumerate(G_list):
            start  = time.time()
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
            print('x-axis stuff in', time.time() - start)
            start = time.time()
            G_pos = pt.get_own_pos(G, pos)
            print('get_own_pos', time.time() - start)
            start = time.time()
            pos_list = pt.branch_separation(G, G_pos)
            print('branch separation', time.time() - start)
            start = time.time()
            node_counts.append(gt.get_nodes_in_depth(G))
            print('node depths', time.time() - start)

            pv_nodes = pt.get_pv_nodes(G)
            miniboard_time = 0
            node_metric_time = 0
            start = time.time()
            for i, branch in enumerate(pos_list):
                for node in branch:
                    if node not in data:
                        parent = gt.get_parent(G, node)
                        parent_point = [None, None] if parent is None else pos[parent]
                        if not SHOW_UNICODE_BOARD:
                            miniboard = ''
                        else:
                            miniboard = pt.get_miniboard_unicode(G, node, self.board, moves)
                        if miniboard != '':
                            miniboard = miniboard.replace('\n', '<br>')
                        move = pt.get_move(G, node)
                        if move == "":
                            move = None
                        data[node] = {'point': branch[node],
                                      'parent': parent_point,
                                      'miniboard':  miniboard,
                                      #'fen': fen,
                                      'move': move,
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
            print('Tree process time:', (time.time() - start))
        self.data[position_id] = data
        self.merged_graphs[position_id] = G_merged
        y_tick_labels, y_tick_values = pt.get_y_ticks(pos)
        y_range = [-1, len(y_tick_values)]
        x_range = pt.get_x_range(pos)
        self.x_range[position_id] = x_range
        self.y_range[position_id] = y_range
        self.y_tick_labels[position_id] = y_tick_labels
        self.y_tick_values[position_id] = y_tick_values


        max_len = max([len(nc) for nc in node_counts])
        node_counts = [['0'] * (max_len - len(nc)) + nc for nc in node_counts]
        y2_max = max(max([int(x) for x in nc]) for nc in node_counts)
        self.y2_range[position_id] = [0, y2_max]
        self.data_depth[position_id] = {i: (list(range(len(node_count))), list(map(int, node_count))) for i, node_count in enumerate(node_counts)}
        self.x_tick_labels[position_id] = {i: x_label_list for i, x_label_list in enumerate(x_labels)}
        self.x_tick_values[position_id] = x_label_vals

    def calculate_heatmap_helpers(self, position_id):
        G = self.merged_graphs[position_id]
        if self.type == 'pgn':
            game_data = game_data_pgn
        else:
            game_data = game_data_fen
        fen = game_data.get_value_by_position_id('fen', position_id)
        initial_board = chess.Board(fen)
        boards = {}

        nodes = {}
        depths = {}

        x_map = {letter: index for index, letter in enumerate('abcdefgh')}
        y_map = {letter: index for index, letter in enumerate('12345678')}

        X = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        Y = ['1', '2', '3', '4', '5', '6', '7', '8']
        pychess_square_table = {8 * Y.index(y) + X.index(x): x + y for y in Y for x in X}

        letters = 'abcdefgh'
        numbers = '12345678'
        coordinate_map = {x+y: (x_ind, y_ind) for x_ind, x in enumerate(letters) for y_ind, y in enumerate(numbers)}

        #map first letter of long algebraic notation to piece
        letter_to_piece = {letter: 'p' for letter in 'abcdefgh'} #pawn moves
        letter_to_piece['O'] = 'k' #castling considered as king move
        letter_to_piece.update({letter: letter.lower() for letter in 'NBRQK'})

        color_map = {True: 'white', False: 'black'}

        for node in topological_sort(G):
            parent = gt.get_parent(G, node)
            if parent is None:
                boards[node] = initial_board
                depths[node] = 0
            else:
                board = boards[parent].copy(stack=False)
                move_uci = G.nodes[node]['move']
                move = chess.Move.from_uci(move_uci)
                piece = board.lan(move)[0]
                piece = letter_to_piece[piece]

                turn = color_map[board.turn]

                #x_origin, y_origin = move_uci[:2]
                #x_origin = x_map[x_origin]
                #y_origin = y_map[y_origin]

                x_origin, y_origin = coordinate_map[move_uci[:2]]

                #x_destination, y_destination = move_uci[2:4]
                #x_destination = x_map[x_destination]
                #y_destination = y_map[y_destination]

                x_destination, y_destination = coordinate_map[move_uci[2:4]]

                board.push(move)
                boards[node] = board
                depth = 1 + depths[parent]
                depths[node] = depth

                key = (turn, piece, depth)
                value = {'origin': (x_origin, y_origin), 'destination': (x_destination, y_destination)}


                occupied = []
                pieces_on_board = board.piece_map()
                for position, piece in pieces_on_board.items():
                    piece = str(piece)
                    piece_color = color_map[not piece.islower()] #lower case pieces are black
                    piece = piece.lower()
                    x, y = coordinate_map[pychess_square_table[position]]
                    occupied.append((piece_color, piece, x, y))

                value['occupied'] = occupied

                nodes[node] = (key, value)

        data_moves = []
        data_board_states = []
        for G in self.G_dict[position_id]:
            move_related_data = {}
            board_state_related_data = {}
            for node in G:
                if node == 'root':
                    continue
                key, value = nodes[node]
                x_origin, y_origin = value['origin']
                x_destination, y_destination = value['destination']
                if key not in move_related_data:
                    move_related_data[key] = {'origin': [[0, 0, 0, 0, 0, 0, 0, 0] for _ in range(8)],
                                'destination': [[0, 0, 0, 0, 0, 0, 0, 0] for _ in range(8)]}
                move_related_data[key]['origin'][y_origin][x_origin] += 1
                move_related_data[key]['destination'][y_destination][x_destination] += 1

                depth = key[2]
                for piece in value['occupied']:
                    color, piece, x, y = piece
                    key = (color, piece, depth)
                    if key not in board_state_related_data:
                        board_state_related_data[key] = {'occupied': [[0, 0, 0, 0, 0, 0, 0, 0] for _ in range(8)]}
                    board_state_related_data[key]['occupied'][y][x] += 1

            data_moves.append(move_related_data)
            data_board_states.append((board_state_related_data))

        self.heatmap_data_for_moves[position_id] = data_moves
        self.heatmap_data_for_board_states[position_id] = data_board_states


lc0 = leela_engine(None)

tree_data_pgn = TreeData(lc0, 'pgn')
tree_data_fen = TreeData(lc0, 'fen')

game_data_pgn = GameData('pgn')
game_data_fen = GameData('fen')

config_data = ConfigData(lc0)

