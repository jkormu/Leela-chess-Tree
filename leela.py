import chess.engine
import time
import networkx as nx
import os

class leela_engine:
    def __init__(self, engine_path):
        self.lc0 = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.analyzed_count = 0 #used as unique id of position for SimpleEngine.play(), forces ucinewgame
        self.configuration = {}
        self.options = self.get_options()
        for opt in self.options:
            if opt in ['MultiPV', 'Ponder', 'UCI_Chess960']:
                continue
            value = self.options[opt].default
            self.configuration[opt] = value

    def play(self, board, nodes):
        if board.is_game_over():
            #TODO: return only root node, manually crete one
            #currently hits error if game over position
            pass

        self.analyzed_count += 1
        start = time.time()
        self.lc0.play(board, chess.engine.Limit(nodes=nodes), game=self.analyzed_count)
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