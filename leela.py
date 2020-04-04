import chess.engine
import time
import networkx as nx
import os
from os.path import isfile, join

class leela_engine:
    def __init__(self, engine_path = None):
        if engine_path is None:
            engine_path = self.find_engine()
            net = '/home/jusufe/tmp/weights_run2_591226.pb.gz'
            engine_path = [engine_path, '--weights=' + net]
        print(engine_path)
        self.lc0 = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.analyzed_count = 0 #used as unique id of position for SimpleEngine.play(), forces ucinewgame
        self.configuration = {}
        self.options = self.get_options()
        for opt in self.options:
            if opt in ['MultiPV', 'Ponder', 'UCI_Chess960']:
                continue
            value = self.options[opt].default
            self.configuration[opt] = value

    def find_engine(self):
        root = os.getcwd()
        for r, d, files in os.walk(root):
            for f in files:
                if f.startswith('lc0_tree') and isfile(join(r, f)):
                    return(join(r, f))
        #path = os.getcwd()
        #engine_path = [join(path, f) for f in os.listdir(path) if isfile(join(path, f)) and f.startswith('lc0_tree')][0]
        return(None)

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
        print('CONFIGURING:', options)
        changed = False
        for opt in options:
            if self.configuration[opt] != options[opt]:
                self.configuration[opt] = options[opt]
                changed = True
        if changed:
            print('setting parameters:', self.configuration)
            self.lc0.configure(self.configuration)


    def get_options(self):
        return(self.lc0.options)