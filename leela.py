import chess.engine
import time
import networkx as nx
import os
from os.path import isfile, join
from datetime import datetime
from constants import ROOT_DIR

class leela_engine:
    def __init__(self, engine_path=None):
        self.error = None
        if engine_path is None:
            engine_path = self.find_engine()
            net = self.find_net()
        if net is not None and engine_path is not None:
            engine_path = [engine_path, '--weights=' + net]  # '--logfile=lc0_log.txt']
            try:
                self.lc0 = chess.engine.SimpleEngine.popen_uci(engine_path)
            except:
                self.error = f'{datetime.now()}: Could not launch lc0_tree engine with command "{"".join(engine_path)}"'
        else:
            self.lc0 = None
            self.error = ''
            if net is None:
                self.error += f'{datetime.now()}: Could not find any weight files in "weights"-folder. Add at least one weight file. \n'
            if engine_path is None:
                self.error += f'{datetime.now()}: Coult not find lc0_tree engine. Please refer to the installation guide in "https://github.com/jkormu/leela-tree-dash" \n'
        log_file = join(ROOT_DIR, 'LcT_log.txt')
        print(log_file)
        if self.error is not None:
            log_file = join(ROOT_DIR, 'LcT_log.txt')
            print(log_file)
            with open(log_file, "w") as log:
                log.write(self.error)
        self.analyzed_count = 0 #used as unique id of position for SimpleEngine.play(), forces ucinewgame
        self.configuration = {}
        self.options = self.get_options()
        for opt in self.options:
            if opt in ['MultiPV', 'Ponder', 'UCI_Chess960']:
                continue
            value = self.options[opt].default
            self.configuration[opt] = value

    def find_engine(self):
        root = ROOT_DIR
        for r, d, files in os.walk(root):
            for f in files:
                if f.startswith('lc0') and isfile(join(r, f)):
                    return(join(r, f))
        return(None)

    def find_net(self):
        root = ROOT_DIR
        weights_folder = os.path.join(root, 'weights')
        net_path = [os.path.relpath(join(weights_folder, f)) for f in os.listdir(weights_folder) if isfile(join(weights_folder, f))]
        try:
            net_path = net_path[0]
        except IndexError:
            net_path = None
        return(net_path)

    def play(self, board, nodes):
        self.analyzed_count += 1
        start = time.time()
        try:
            self.lc0.play(board, chess.engine.Limit(nodes=nodes), game=self.analyzed_count)
        except chess.engine.EngineError:#ValueError:
            #we have hit terminal and lc0 responded "a1a1" as null move, python chess expects 0000
            #we can safely carry on reading the tree file with just one node
            pass
        print('search completed in time: ', time.time() - start)
        g = nx.readwrite.gml.read_gml('tree.gml', label='id')
        os.remove('tree.gml')
        return(g)

    def configure(self, options):
        #change configuration only if new options differ from old
        changed = False
        boolean_conversion = {'False': False, 'True': True}
        for opt in options:
            # Need to convert boolean strings to booleans since
            # dash datatable works with strings and python chess with booleans
            if options[opt] in ['True', 'False']:
                options[opt] = boolean_conversion[options[opt]]

            #clip the option value to allowed range
            min_ = self.options[opt].min
            max_ = self.options[opt].max
            if min_ is not None:
                options[opt] = min(options[opt], max_)
            if max_ is not None:
                options[opt] = max(options[opt], min_)

            #round interger options to nearest integer
            if self.options[opt].type == 'spin':
                options[opt] = int(round(options[opt]))

            if self.configuration[opt] != options[opt]:
                self.configuration[opt] = options[opt]
                changed = True
        if changed:
            #print('CONFIGURING:', options)
            #print('setting parameters:', self.configuration)
            self.lc0.configure(self.configuration)

    def quit(self):
        self.lc0.quit()


    def get_options(self):
        return(self.lc0.options)