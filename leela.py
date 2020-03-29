import chess.engine

class leela_engine:
    def __init__(self, engine_path):
        self.lc0 = chess.engine.SimpleEngine.popen_uci(engine_path)

